from fastapi import FastAPI, APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import smtplib
import ssl
import hmac
import hashlib
import secrets
import random
import time
import json
import jwt as pyjwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# SMTP Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'psicolfis.net')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_USER = os.environ.get('SMTP_USER', 'obdulio@psicolfis.net')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', 'obdulio@psicolfis.net')

# Create the main app without a prefix
app = FastAPI()

# Static files directory
static_dir = ROOT_DIR / "static"

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '34670716305')
WHATSAPP_DEFAULT_TEXT = os.environ.get(
    'WHATSAPP_DEFAULT_TEXT',
    'Hola Obdulio, te escribo desde psicolfis.net'
)

# Public-facing base URL where the SPA is served (used to build email links)
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://psicolfis.net').rstrip('/')

# JWT config for signed access tokens delivered after purchase
JWT_SECRET = os.environ.get('JWT_SECRET') or secrets.token_hex(64)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_DAYS = int(os.environ.get('ACCESS_TOKEN_DAYS', '365'))

# Internal service key for protected admin endpoints
SERVICE_API_KEY = os.environ.get('SERVICE_API_KEY', '')

# Agent catalogue: ID, public name, and Pickaxe deployment IDs per access level.
# The "demo" deployment is the same as "full" by default - Pickaxe handles
# rate limits at the deployment level when configured. If you eventually want
# distinct demo deployments, set PICKAXE_DEPLOYMENT_*_DEMO env vars.
def _agent_deployment(agent_key: str, level: str) -> str:
    base = os.environ.get(f'PICKAXE_DEPLOYMENT_{agent_key.upper()}', '')
    if level == 'demo':
        return os.environ.get(f'PICKAXE_DEPLOYMENT_{agent_key.upper()}_DEMO', base)
    return base


AGENT_CATALOGUE = {
    "iris": {"id": "iris", "name": "IRIS"},
    "alex": {"id": "alex", "name": "ALEX"},
    "umbral": {"id": "umbral", "name": "UMBRAL"},
}


def get_agent_info(agent_id: str, level: str = "full") -> Optional[Dict]:
    """Return agent metadata + Pickaxe deployment id for the given access level."""
    info = AGENT_CATALOGUE.get((agent_id or "").lower())
    if not info:
        return None
    deployment_id = _agent_deployment(info["id"], level)
    return {
        "id": info["id"],
        "name": info["name"],
        "level": level,
        "deployment_id": deployment_id,
    }


def generate_access_token(
    customer_email: str,
    agent_id: str,
    level: str = "full",
    customer_name: str = "",
    days_valid: Optional[int] = None,
) -> str:
    """Generate a signed JWT granting access to a specific agent for a customer."""
    if days_valid is None:
        days_valid = ACCESS_TOKEN_DAYS
    now = datetime.now(timezone.utc)
    payload = {
        "sub": customer_email.lower().strip(),
        "name": (customer_name or "").strip(),
        "agent": agent_id.lower(),
        "level": level.lower(),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=days_valid)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict:
    """Validate and decode a JWT access token. Raises HTTPException on failure."""
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El enlace de acceso ha caducado. Contacta con nosotros para renovarlo.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Enlace de acceso no válido.")
    if not payload.get("agent") or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token de acceso incompleto.")
    return payload


def build_agent_access_url(token: str) -> str:
    return f"{PUBLIC_BASE_URL}/mi-agente/{token}"

# Email sending function
def send_purchase_email(
    customer_email: str,
    customer_name: str,
    agent_name: str,
    agent_id: str,
    level: str = "full",
):
    """Send confirmation email after a successful purchase.

    Generates a signed JWT access token tied to the customer's email + agent +
    level, then builds a personal access URL on psicolfis.net that gates the
    embedded Pickaxe agent. Email content is rendered from per-agent templates
    so each agent (IRIS / ALEX / UMBRAL) speaks in its own voice.
    """
    try:
        from email_templates import render_email

        token = generate_access_token(
            customer_email=customer_email,
            agent_id=agent_id,
            level=level,
            customer_name=customer_name,
        )
        agent_url = build_agent_access_url(token)

        # Upsell URL only matters for demo emails. We pull it from env so it
        # can be rotated without code changes.
        full_url = os.environ.get(f'STRIPE_FULL_URL_{(agent_id or "").upper()}', '') or None

        subject, text, html = render_email(
            agent_id=agent_id,
            level=level,
            customer_name=customer_name or "",
            access_url=agent_url,
            full_url=full_url,
            photo_base_url=PUBLIC_BASE_URL,
        )

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"PSICOLFIS.NET <{SMTP_FROM}>"
        message["To"] = customer_email

        part1 = MIMEText(text, "plain", "utf-8")
        part2 = MIMEText(html, "html", "utf-8")
        message.attach(part1)
        message.attach(part2)
        
        # Send email using SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, customer_email, message.as_string())
        
        logger.info(f"Email sent successfully to {customer_email} for agent {agent_name} ({level})")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email to {customer_email}: {str(e)}")
        return False


def send_budget_request_email(nombre: str, email: str, telefono: str, plan: str,
                              agente: str = "", mensaje: str = "") -> bool:
    """Send budget request email to the business owner."""
    try:
        if not SMTP_PASSWORD:
            logger.error("SMTP_PASSWORD not configured - cannot send budget email")
            return False

        message = MIMEMultipart("alternative")
        message["Subject"] = f"📩 Nueva solicitud de presupuesto - {plan}"
        message["From"] = f"PSICOLFIS.NET <{SMTP_FROM}>"
        message["To"] = SMTP_FROM
        message["Reply-To"] = email

        telefono_safe = telefono.strip() if telefono else "(no proporcionado)"
        agente_safe = agente.strip() if agente else "(sin preferencia)"
        mensaje_safe = mensaje.strip() if mensaje else "(sin comentarios adicionales)"

        text = f"""Nueva solicitud de presupuesto desde psicolfis.net

Plan seleccionado: {plan}
Agente de interés: {agente_safe}

Datos del solicitante:
  - Nombre: {nombre}
  - Email: {email}
  - Teléfono: {telefono_safe}

Proyecto / comentarios:
{mensaje_safe}

Responde a este correo para contactar directamente con el cliente.
"""

        # Escape minimal HTML in message to avoid breaking the layout
        html_mensaje = (
            mensaje_safe
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Arial, sans-serif; color:#1f2937; background:#f8fafc; padding:24px;">
  <div style="max-width:620px; margin:0 auto; background:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 4px 18px rgba(0,0,0,0.06);">
    <div style="background:linear-gradient(135deg,#3b82f6,#8b5cf6); color:#fff; padding:24px 28px;">
      <h1 style="margin:0; font-size:22px;">📩 Nueva solicitud de presupuesto</h1>
      <p style="margin:6px 0 0; opacity:0.9;">Desde la landing de PSICOLFIS.NET</p>
    </div>
    <div style="padding:28px;">
      <p style="margin:0 0 10px;"><strong>Plan seleccionado:</strong><br/>
        <span style="display:inline-block; margin-top:4px; padding:6px 12px; background:#eef2ff; color:#4338ca; border-radius:999px; font-weight:600;">{plan}</span>
      </p>
      <p style="margin:0 0 18px;"><strong>Agente de interés:</strong>
        <span style="display:inline-block; margin-left:6px; padding:4px 10px; background:#fef3c7; color:#92400e; border-radius:999px; font-weight:600;">{agente_safe}</span>
      </p>
      <table style="width:100%; border-collapse:collapse;">
        <tr><td style="padding:10px 0; border-bottom:1px solid #e5e7eb; color:#6b7280; width:120px;">Nombre</td><td style="padding:10px 0; border-bottom:1px solid #e5e7eb;"><strong>{nombre}</strong></td></tr>
        <tr><td style="padding:10px 0; border-bottom:1px solid #e5e7eb; color:#6b7280;">Email</td><td style="padding:10px 0; border-bottom:1px solid #e5e7eb;"><a href="mailto:{email}" style="color:#3b82f6;">{email}</a></td></tr>
        <tr><td style="padding:10px 0; color:#6b7280;">Teléfono</td><td style="padding:10px 0;">{telefono_safe}</td></tr>
      </table>
      <div style="margin-top:22px; padding:16px 18px; background:#f9fafb; border-left:4px solid #8b5cf6; border-radius:6px;">
        <p style="margin:0 0 6px; color:#6b7280; font-size:13px; text-transform:uppercase; letter-spacing:0.4px;">Proyecto / comentarios</p>
        <p style="margin:0; color:#1f2937; line-height:1.6;">{html_mensaje}</p>
      </div>
      <p style="margin-top:22px; color:#6b7280; font-size:13px;">Puedes responder directamente a este correo para contactar con el cliente.</p>
    </div>
  </div>
</body>
</html>
"""

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, SMTP_FROM, message.as_string())

        logger.info(f"Budget request email sent from {email} for plan {plan}")
        return True

    except Exception as e:
        logger.error(f"Error sending budget request email: {str(e)}")
        return False

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class CheckoutRequest(BaseModel):
    agent_id: str
    origin_url: str

class BudgetRequest(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = ""
    plan: str
    agente: Optional[str] = ""
    mensaje: Optional[str] = ""
    captcha_token: str
    captcha_answer: str
    # Honeypot: real users must leave this empty; bots tend to fill every field
    website: Optional[str] = ""


class ReviewCreate(BaseModel):
    author: str
    rating: int = Field(ge=1, le=5)
    text: str
    role: Optional[str] = ""  # "Fisioterapeuta", "Dueño de cafetería"...
    captcha_token: str
    captcha_answer: str
    website: Optional[str] = ""  # honeypot


# ----- Simple stateless CAPTCHA (signed math challenge) -----
CAPTCHA_SECRET = os.environ.get('CAPTCHA_SECRET') or secrets.token_hex(32)
CAPTCHA_TTL_SECONDS = 600  # 10 minutes


def _build_captcha_signature(answer: str, issued_at: int) -> str:
    payload = f"{answer}:{issued_at}".encode("utf-8")
    return hmac.new(CAPTCHA_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_captcha(token: str, user_answer: str) -> bool:
    try:
        if not token or "." not in token:
            return False
        issued_str, signature = token.split(".", 1)
        issued_at = int(issued_str)
        if time.time() - issued_at > CAPTCHA_TTL_SECONDS:
            return False
        expected = _build_captcha_signature(user_answer.strip(), issued_at)
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_id: str
    amount: float
    currency: str
    payment_status: str
    metadata: Dict[str, str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Fixed packages for each agent with Stripe Product IDs
AGENT_PACKAGES = {
    "iris": {
        "name": "IRIS", 
        "price": 50.00, 
        "description": "Agente IRIS IA",
        "stripe_product_id": "prod_TepDjoE0cAFPPL"
    },
    "alex": {
        "name": "ALEX", 
        "price": 50.00, 
        "description": "Agente ALEX IA",
        "stripe_product_id": "prod_TepFe4bwAuXp9g"
    },
    "umbral": {
        "name": "UMBRAL", 
        "price": 50.00, 
        "description": "Agente UMBRAL IA",
        "stripe_product_id": "prod_TepGUnus1GtsMQ"
    }
}

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.get("/video/{filename}")
async def stream_video(filename: str, request: Request):
    """Stream video with range request support for better browser compatibility"""
    video_path = static_dir / filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_size = video_path.stat().st_size
    
    # Check for range header
    range_header = request.headers.get("range")
    
    if range_header:
        # Parse range header
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        if start >= file_size:
            raise HTTPException(status_code=416, detail="Range not satisfiable")
        
        end = min(end, file_size - 1)
        content_length = end - start + 1
        
        def iterfile():
            with open(video_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk_size = min(8192, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        return StreamingResponse(
            iterfile(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Cache-Control": "public, max-age=86400",
            }
        )
    else:
        # No range header - return full file
        return FileResponse(
            video_path,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Cache-Control": "public, max-age=86400",
            }
        )

@api_router.get("/download/production-package")
async def download_production_package():
    from fastapi.responses import FileResponse
    import os
    
    file_path = "/app/psicolfis-production.tar.gz"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type="application/gzip",
        filename="psicolfis-production.tar.gz",
        headers={
            "Content-Disposition": "attachment; filename=psicolfis-production.tar.gz"
        }
    )

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Stripe Checkout Endpoints
@api_router.get("/whatsapp")
async def whatsapp_redirect():
    """Server-side redirect that hides the real WhatsApp number from the public HTML.

    Users click a link to /api/whatsapp on the frontend; the backend issues a
    302 redirect to wa.me, so the phone number never appears in the page source.
    """
    from urllib.parse import quote
    text = quote(WHATSAPP_DEFAULT_TEXT)
    target = f"https://wa.me/{WHATSAPP_NUMBER}?text={text}"
    return RedirectResponse(url=target, status_code=302, headers={"Cache-Control": "no-store"})


@api_router.get("/captcha")
async def get_captcha():
    """Issue a simple signed math CAPTCHA challenge.

    The token encodes the issue timestamp and an HMAC that depends on the
    correct answer, so verification is stateless - no DB storage needed.
    """
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    answer = str(a + b)
    issued_at = int(time.time())
    signature = _build_captcha_signature(answer, issued_at)
    return {
        "question": f"¿Cuánto es {a} + {b}?",
        "token": f"{issued_at}.{signature}",
        "ttl_seconds": CAPTCHA_TTL_SECONDS,
    }


@api_router.post("/contact/budget")
async def submit_budget_request(request: BudgetRequest):
    """Receive budget request from the landing page form and email it to the owner."""
    nombre = request.nombre.strip()
    email = request.email.strip()
    plan = request.plan.strip()

    if not nombre or not email or not plan:
        raise HTTPException(status_code=400, detail="Nombre, email y plan son obligatorios")

    # Honeypot: real users never fill this hidden field
    if request.website and request.website.strip():
        logger.warning(f"Honeypot triggered for email {email} - rejecting")
        raise HTTPException(status_code=400, detail="Solicitud no válida")

    # Verify CAPTCHA
    if not verify_captcha(request.captcha_token, request.captcha_answer):
        raise HTTPException(
            status_code=400,
            detail="Verificación de seguridad incorrecta. Por favor, vuelve a resolverla."
        )

    agente = (request.agente or "").strip()
    mensaje = (request.mensaje or "").strip()

    # Persist the request for record-keeping
    record = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "email": email,
        "telefono": (request.telefono or "").strip(),
        "plan": plan,
        "agente": agente,
        "mensaje": mensaje,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "email_sent": False,
        "read": False,
    }

    email_sent = send_budget_request_email(
        nombre=nombre,
        email=email,
        telefono=record["telefono"],
        plan=plan,
        agente=agente,
        mensaje=mensaje,
    )
    record["email_sent"] = email_sent

    try:
        await db.budget_requests.insert_one(record)
    except Exception as e:
        logger.error(f"Error storing budget request: {str(e)}")

    if not email_sent:
        raise HTTPException(
            status_code=502,
            detail="No pudimos entregar tu solicitud por email en este momento. Por favor, inténtalo más tarde o escríbenos a obdulio@psicolfis.net."
        )

    return {"success": True, "message": "Solicitud enviada correctamente"}


# ----- Reviews / Testimonials -----
@api_router.get("/reviews")
async def list_reviews():
    """Return the published (approved) reviews, newest first."""
    cursor = db.reviews.find(
        {"approved": True},
        {"_id": 0, "email": 0}  # never expose email publicly
    ).sort("created_at", -1).to_list(100)
    reviews = await cursor

    # Convert ISO string timestamps back to readable form for client
    for r in reviews:
        if isinstance(r.get("created_at"), str):
            r["created_at"] = r["created_at"]

    if reviews:
        total = sum(r["rating"] for r in reviews)
        average = round(total / len(reviews), 2)
    else:
        average = 0

    return {
        "reviews": reviews,
        "count": len(reviews),
        "average": average,
    }


@api_router.post("/reviews")
async def create_review(payload: ReviewCreate):
    """Submit a new review. Auto-approved, but can be hidden by admin in DB."""
    author = payload.author.strip()
    text = payload.text.strip()
    role = (payload.role or "").strip()

    if not author or not text:
        raise HTTPException(status_code=400, detail="Nombre y reseña son obligatorios")

    if len(text) < 20:
        raise HTTPException(status_code=400, detail="La reseña debe tener al menos 20 caracteres")

    if payload.website and payload.website.strip():
        logger.warning(f"Honeypot triggered for review from {author}")
        raise HTTPException(status_code=400, detail="Solicitud no válida")

    if not verify_captcha(payload.captcha_token, payload.captcha_answer):
        raise HTTPException(
            status_code=400,
            detail="Verificación de seguridad incorrecta. Por favor, vuelve a resolverla."
        )

    review = {
        "id": str(uuid.uuid4()),
        "author": author[:80],
        "role": role[:80],
        "rating": payload.rating,
        "text": text[:1000],
        "approved": True,  # auto-approve; admin can flip to False to hide
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.reviews.insert_one(review.copy())
    review.pop("_id", None)
    logger.info(f"New review from {author} with rating {payload.rating}")
    return {"success": True, "review": review}


# ----- Access Tokens (for embedded Pickaxe agents) -----

class AccessGenerateRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = ""
    agent_id: str
    level: str = "full"  # "demo" or "full"
    days_valid: Optional[int] = None


@api_router.get("/access/validate")
async def validate_access_token(token: str):
    """Validate a JWT access token and return the agent metadata to embed.

    Called from the SPA at /mi-agente/:token. Returns the Pickaxe deployment
    ID needed to render the embedded agent. The Pickaxe URL itself never
    leaves the server-side configuration.
    """
    payload = decode_access_token(token)
    agent_id = payload.get("agent")
    level = payload.get("level", "full")
    info = get_agent_info(agent_id, level=level)
    if not info or not info.get("deployment_id"):
        raise HTTPException(status_code=404, detail="Agente no encontrado o no configurado.")

    return {
        "agent_id": info["id"],
        "agent_name": info["name"],
        "level": info["level"],
        "deployment_id": info["deployment_id"],
        "customer_email": payload.get("sub"),
        "customer_name": payload.get("name", ""),
        "expires_at": payload.get("exp"),
    }


@api_router.post("/access/generate")
async def admin_generate_access(
    payload: AccessGenerateRequest,
    x_service_key: Optional[str] = Header(default=None, alias="X-Service-Key"),
):
    """Admin-only endpoint to generate a personal access link manually.

    Useful for sending access to an existing customer outside Stripe (gifts,
    partners, replays, etc.). Protected by SERVICE_API_KEY header.
    """
    if not SERVICE_API_KEY or x_service_key != SERVICE_API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")

    info = get_agent_info(payload.agent_id, level=payload.level)
    if not info or not info.get("deployment_id"):
        raise HTTPException(status_code=400, detail="Agente o nivel no válido.")

    token = generate_access_token(
        customer_email=payload.customer_email,
        agent_id=info["id"],
        level=info["level"],
        customer_name=payload.customer_name or "",
        days_valid=payload.days_valid,
    )
    url = build_agent_access_url(token)
    return {
        "token": token,
        "url": url,
        "agent_id": info["id"],
        "agent_name": info["name"],
        "level": info["level"],
    }


@api_router.get("/agents/{agent_id}/photo")
async def get_agent_photo(agent_id: str):
    """Serve a static portrait image for an agent (used in emails)."""
    agent_id = (agent_id or "").lower()
    if agent_id not in {"iris", "alex", "umbral"}:
        raise HTTPException(status_code=404, detail="Not found")
    img_path = static_dir / "agents" / f"{agent_id}.jpg"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(
        img_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@api_router.get("/access/preview-email")
async def admin_preview_email(
    request: Request,
    agent_id: str,
    level: str = "demo",
    customer_name: str = "Obdulio",
    key: Optional[str] = None,
    x_service_key: Optional[str] = Header(default=None, alias="X-Service-Key"),
):
    """Render the welcome email HTML for QA without sending it.

    Generates a real signed token tied to the requested agent + level so the
    embedded CTA points to a working /mi-agente/:token URL on production.
    Auth: SERVICE_API_KEY either as the `X-Service-Key` header or `?key=` query
    param (so a plain browser link works during preview).
    """
    from fastapi.responses import HTMLResponse
    from email_templates import render_email

    provided = x_service_key or key
    if not SERVICE_API_KEY or provided != SERVICE_API_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")

    info = get_agent_info(agent_id, level=level)
    if not info or not info.get("deployment_id"):
        raise HTTPException(status_code=400, detail="Agente o nivel no válido.")

    token = generate_access_token(
        customer_email="preview@psicolfis.net",
        agent_id=info["id"],
        level=info["level"],
        customer_name=customer_name,
    )
    access_url = build_agent_access_url(token)
    full_url = os.environ.get(f'STRIPE_FULL_URL_{info["id"].upper()}', '') or None

    # Build a public-facing photo base URL. Prefer x-forwarded headers (set by
    # the ingress proxy when reaching us through a custom domain or preview),
    # fall back to PUBLIC_BASE_URL only as a last resort.
    fwd_proto = request.headers.get("x-forwarded-proto", "https")
    fwd_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if fwd_host and not fwd_host.startswith("localhost"):
        photo_base = f"{fwd_proto}://{fwd_host}"
    else:
        photo_base = PUBLIC_BASE_URL

    subject, plain, html = render_email(
        agent_id=info["id"],
        level=info["level"],
        customer_name=customer_name,
        access_url=access_url,
        full_url=full_url,
        photo_base_url=photo_base,
    )
    # Wrap with the subject as a small banner above the email so previewers see
    # the From / Subject metadata too.
    preview = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Preview · {info['name']} · {info['level']}</title>
<style>body{{margin:0;font-family:system-ui;background:#0b1020;color:#e2e8f0}}
.meta{{background:#0f172a;color:#cbd5e1;padding:16px 22px;border-bottom:1px solid #1f2937;font-size:13px}}
.meta b{{color:#fff}}.meta span{{color:#94a3b8;margin-right:6px}}</style></head>
<body><div class="meta"><span>From:</span><b>PSICOLFIS.NET &lt;obdulio@psicolfis.net&gt;</b><br>
<span>To:</span><b>{customer_name} &lt;tu-email@ejemplo.com&gt;</b><br>
<span>Subject:</span><b>{subject}</b></div>{html}</body></html>"""
    return HTMLResponse(content=preview)


# ---- Admin auth + back-office endpoints --------------------------------------

import bcrypt as _bcrypt

ADMIN_EMAIL = (os.environ.get("ADMIN_EMAIL") or "").lower().strip()
_ADMIN_PASSWORD_PLAIN = os.environ.get("ADMIN_PASSWORD") or ""
ADMIN_TOKEN_HOURS = int(os.environ.get("ADMIN_TOKEN_HOURS", "8"))
LOGIN_LOCK_MAX_ATTEMPTS = 5
LOGIN_LOCK_WINDOW_MIN = 15


def _hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _create_admin_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email.lower(),
        "role": "admin",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ADMIN_TOKEN_HOURS)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def seed_admin_if_needed():
    if not ADMIN_EMAIL or not _ADMIN_PASSWORD_PLAIN:
        logger.warning("Admin not seeded - ADMIN_EMAIL or ADMIN_PASSWORD missing in .env")
        return
    existing = await db.admin_users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        await db.admin_users.insert_one({
            "id": str(uuid.uuid4()),
            "email": ADMIN_EMAIL,
            "password_hash": _hash_password(_ADMIN_PASSWORD_PLAIN),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin seeded: {ADMIN_EMAIL}")
    elif not _verify_password(_ADMIN_PASSWORD_PLAIN, existing.get("password_hash", "")):
        await db.admin_users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"password_hash": _hash_password(_ADMIN_PASSWORD_PLAIN)}},
        )
        logger.info(f"Admin password rotated: {ADMIN_EMAIL}")


async def get_current_admin(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = auth[7:].strip()
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesion expirada")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token no valido")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    return payload


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


@api_router.post("/admin/login")
async def admin_login(payload: AdminLoginRequest, request: Request):
    email = payload.email.lower().strip()
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=LOGIN_LOCK_WINDOW_MIN)

    recent_failed = await db.login_attempts.count_documents({
        "identifier": identifier,
        "ts": {"$gte": window_start.isoformat()},
        "success": False,
    })
    if recent_failed >= LOGIN_LOCK_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espera unos minutos.")

    user = await db.admin_users.find_one({"email": email})
    ok = bool(user) and _verify_password(payload.password, user.get("password_hash", ""))

    await db.login_attempts.insert_one({
        "identifier": identifier,
        "email": email,
        "ip": ip,
        "ts": now.isoformat(),
        "success": ok,
    })

    if not ok:
        raise HTTPException(status_code=401, detail="Email o contrasena incorrectos")

    token = _create_admin_token(email)
    return {"token": token, "email": email, "expires_in_hours": ADMIN_TOKEN_HOURS}


@api_router.get("/admin/me")
async def admin_me(admin: dict = Depends(get_current_admin)):
    return {"email": admin["sub"], "role": admin["role"], "exp": admin["exp"]}


@api_router.get("/admin/budget-requests")
async def admin_list_budget_requests(admin: dict = Depends(get_current_admin)):
    cursor = db.budget_requests.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    items = await cursor.to_list(500)
    unread = await db.budget_requests.count_documents({"read": {"$ne": True}})
    total = await db.budget_requests.count_documents({})
    return {"items": items, "unread": unread, "total": total}


class MarkReadRequest(BaseModel):
    read: bool = True


@api_router.patch("/admin/budget-requests/{request_id}")
async def admin_mark_budget_request(
    request_id: str,
    payload: MarkReadRequest,
    admin: dict = Depends(get_current_admin),
):
    update = {"read": payload.read}
    if payload.read:
        update["read_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update["read_at"] = None
    res = await db.budget_requests.update_one({"id": request_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"success": True, "read": payload.read}


@api_router.get("/admin/reviews")
async def admin_list_reviews(admin: dict = Depends(get_current_admin)):
    cursor = db.reviews.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    items = await cursor.to_list(500)
    pending = await db.reviews.count_documents({"approved": False})
    return {"items": items, "pending": pending, "total": len(items)}


class ReviewModerationRequest(BaseModel):
    approved: bool


@api_router.patch("/admin/reviews/{review_id}")
async def admin_moderate_review(
    review_id: str,
    payload: ReviewModerationRequest,
    admin: dict = Depends(get_current_admin),
):
    res = await db.reviews.update_one({"id": review_id}, {"$set": {"approved": payload.approved}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return {"success": True, "approved": payload.approved}


@api_router.delete("/admin/reviews/{review_id}")
async def admin_delete_review(
    review_id: str,
    admin: dict = Depends(get_current_admin),
):
    res = await db.reviews.delete_one({"id": review_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return {"success": True}



async def seed_reviews_if_empty():
    """Insert a few realistic starter reviews if the collection is empty."""
    existing = await db.reviews.count_documents({})
    if existing > 0:
        return
    seed = [
        {
            "id": str(uuid.uuid4()),
            "author": "María Ruiz",
            "role": "Fisioterapeuta autónoma",
            "rating": 5,
            "text": "Obdulio entendió a la primera cómo quería que mi agente respondiera. Ahora gestiona las preguntas básicas de mis pacientes y yo recupero casi 6 horas a la semana.",
            "approved": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "author": "Javier Pérez",
            "role": "Fundador de academia online",
            "rating": 5,
            "text": "El acompañamiento es lo que marca la diferencia. No te dan una herramienta y se van: te ayudan a que funcione. Mi agente ya redacta secuencias de email que convierten.",
            "approved": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "author": "Laura Fernández",
            "role": "Consultora de marketing",
            "rating": 4,
            "text": "Tuve dudas al principio, pero en pocas sesiones personalizamos el tono y la calidad de las respuestas mejoró muchísimo. Lo recomiendo para profesionales que quieran escalar sin perder su voz.",
            "approved": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "author": "Carlos Méndez",
            "role": "Dueño de clínica estética",
            "rating": 5,
            "text": "Me sorprendió lo rápido que se adapta a mi forma de hablar. Respuesta en minutos a preguntas que antes me ocupaban media mañana. 10 de 10.",
            "approved": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    await db.reviews.insert_many(seed)
    logger.info(f"Seeded {len(seed)} starter reviews")


@app.on_event("startup")
async def on_startup():
    try:
        await seed_admin_if_needed()
    except Exception as e:
        logger.error(f"Admin seed error: {e}")
    try:
        await seed_reviews_if_empty()
    except Exception as e:
        logger.error(f"Seed error: {e}")
    try:
        await db.admin_users.create_index("email", unique=True)
        await db.login_attempts.create_index("identifier")
        await db.login_attempts.create_index([("ts", 1)])
    except Exception as e:
        logger.error(f"Index creation error: {e}")


@api_router.post("/checkout/session")
async def create_checkout_session(request: CheckoutRequest, http_request: Request):
    try:
        # Validate agent_id
        agent_id_lower = request.agent_id.lower()
        if agent_id_lower not in AGENT_PACKAGES:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        # Get fixed price from server-side definition
        agent_info = AGENT_PACKAGES[agent_id_lower]
        amount = agent_info["price"]
        
        # Build dynamic URLs from provided origin
        success_url = f"{request.origin_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{request.origin_url}/cancel"
        
        # Initialize Stripe
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        
        host_url = str(http_request.base_url)
        webhook_url = f"{host_url}api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create checkout session using existing Stripe product
        # Note: Using the product_id approach requires using Stripe SDK directly
        import stripe
        stripe.api_key = stripe_api_key
        
        # Create checkout session with existing product
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product': agent_info["stripe_product_id"],
                    'unit_amount': int(amount * 100),  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "agent_id": request.agent_id,
                "agent_name": agent_info["name"],
                "source": "web_checkout"
            }
        )
        
        # Convert to CheckoutSessionResponse format
        from types import SimpleNamespace
        session_response = SimpleNamespace(
            session_id=session.id,
            url=session.url
        )
        
        # Store transaction in database
        transaction = PaymentTransaction(
            session_id=session_response.session_id,
            agent_id=request.agent_id,
            amount=amount,
            currency="eur",
            payment_status="pending",
            metadata={
                "agent_name": agent_info["name"],
                "source": "web_checkout",
                "stripe_product_id": agent_info["stripe_product_id"]
            }
        )
        
        transaction_doc = transaction.model_dump()
        transaction_doc['created_at'] = transaction_doc['created_at'].isoformat()
        transaction_doc['updated_at'] = transaction_doc['updated_at'].isoformat()
        
        await db.payment_transactions.insert_one(transaction_doc)
        
        logger.info(f"Created checkout session for agent {request.agent_id}: {session_response.session_id}")
        
        return {"url": session_response.url, "session_id": session_response.session_id}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str):
    try:
        # Initialize Stripe
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        
        # Get status from Stripe
        status_response: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database if payment is complete
        if status_response.payment_status == "paid":
            existing_transaction = await db.payment_transactions.find_one({"session_id": session_id})
            
            if existing_transaction and existing_transaction.get("payment_status") != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {
                        "$set": {
                            "payment_status": "paid",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                logger.info(f"Payment completed for session {session_id}")
        
        return {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount_total": status_response.amount_total,
            "currency": status_response.currency,
            "metadata": status_response.metadata
        }
        
    except Exception as e:
        logger.error(f"Error checking checkout status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe webhook events. Validates signature with STRIPE_WEBHOOK_SECRET
    and, on checkout.session.completed, sends the customer their personal access
    email with the JWT-protected link to /mi-agente/{token}.

    Works for BOTH:
      (a) sessions created via our /api/checkout/session endpoint, and
      (b) Stripe Payment Links (no pre-existing DB row), reading agent_id and
          level from the session.metadata configured in the Payment Link.
    """
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")

        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        if not webhook_secret:
            raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

        import stripe
        stripe.api_key = stripe_api_key

        # Verify signature first; then parse the raw JSON body directly so we
        # work with plain dicts (StripeObject does not expose .get()).
        try:
            stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature,
                secret=webhook_secret,
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            logger.error(f"Stripe webhook parse error: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")

        event = json.loads(body.decode("utf-8"))

        event_type = event.get("type")
        if event_type != "checkout.session.completed":
            # Acknowledge other events but ignore them
            return JSONResponse(content={"status": "ignored", "type": event_type}, status_code=200)

        session_obj = event["data"]["object"]
        session_id = session_obj.get("id")
        payment_status = session_obj.get("payment_status")

        # Pull metadata: prefer the session.metadata (set on Payment Links and Checkout)
        session_metadata = dict(session_obj.get("metadata") or {})
        agent_id = (session_metadata.get("agent_id") or "").strip().lower()
        level = (session_metadata.get("level") or "full").strip().lower()
        if level not in ("demo", "full"):
            level = "full"

        # Fallback: lookup in our DB if metadata isn't on the session (legacy flow)
        if not agent_id:
            existing = await db.payment_transactions.find_one({"session_id": session_id})
            if existing:
                agent_id = (existing.get("agent_id") or "").strip().lower()
                meta = existing.get("metadata") or {}
                if not level or level == "full":
                    level = (meta.get("level") or level or "full").lower()

        # Customer info from the session
        customer_details = session_obj.get("customer_details") or {}
        customer_email = customer_details.get("email") if customer_details else None
        customer_name = (customer_details.get("name") if customer_details else None) or "Cliente"

        # Update or insert payment transaction record
        update_doc = {
            "session_id": session_id,
            "agent_id": agent_id,
            "amount": (session_obj.get("amount_total") or 0) / 100,
            "currency": session_obj.get("currency") or "eur",
            "payment_status": payment_status or "unknown",
            "customer_email": customer_email,
            "customer_name": customer_name,
            "metadata": {**session_metadata, "level": level},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": update_doc,
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            },
            upsert=True,
        )

        # Send the access email only on a real successful payment
        if payment_status == "paid" and customer_email and agent_id:
            agent_info = AGENT_CATALOGUE.get(agent_id, {})
            agent_name = agent_info.get("name", agent_id.upper())

            email_sent = send_purchase_email(
                customer_email=customer_email,
                customer_name=customer_name,
                agent_name=agent_name,
                agent_id=agent_id,
                level=level,
            )
            if email_sent:
                logger.info(f"Access email sent to {customer_email} for {agent_id} ({level})")
            else:
                logger.warning(f"Failed to send access email to {customer_email} for session {session_id}")
        else:
            logger.info(
                f"Webhook processed but no email sent. session={session_id} "
                f"paid={payment_status} agent={agent_id} email={customer_email}"
            )

        return JSONResponse(content={"status": "success"}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
