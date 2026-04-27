from fastapi import FastAPI, APIRouter, Request, HTTPException, Header
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
    embedded Pickaxe agent. The customer never sees the underlying Pickaxe URL.
    """
    try:
        # Generate a signed access token and build the personal access URL.
        # NB: this URL stays inside psicolfis.net by design.
        token = generate_access_token(
            customer_email=customer_email,
            agent_id=agent_id,
            level=level,
            customer_name=customer_name,
        )
        agent_url = build_agent_access_url(token)

        access_label = "Acceso completo" if level == "full" else "Versión demo"

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"🎉 ¡Tu Agente {agent_name} está listo! - PSICOLFIS.NET"
        message["From"] = f"PSICOLFIS.NET <{SMTP_FROM}>"
        message["To"] = customer_email
        
        # Plain text version
        text = f"""
¡Hola {customer_name}!

¡Gracias por tu compra...! Tu Agente de IA {agent_name} ({access_label}) ya está disponible y listo para ayudarte.

Lo que acabas de activar no es solo un agente… es una forma nueva de avanzar con más claridad, foco y libertad. Gracias por confiar. Aquí empieza algo grande. Bienvenido al Universo PSICOLFIS.NET.

Para acceder a tu agente, haz clic en el siguiente enlace personal e intransferible:
{agent_url}

¿Qué puedes hacer ahora?
- Accede a tu agente usando el enlace de arriba
- Comienza a interactuar y multiplicar tu productividad
- Contacta con nosotros si tienes alguna duda

Si tienes alguna pregunta, no dudes en responder a este email. Estamos para acompañarte y mantenernos en contacto.

Recibe un afectuoso saludo,
Obdulio Bailador

---
PSICOLFIS.NET
Tu sabiduría. Nuestra IA. Resultados en acción.
📧 obdulio@psicolfis.net | 🌐 psicolfis.net
        """
        
        # HTML version
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: linear-gradient(90deg, #3b82f6, #8b5cf6); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #64748b; font-size: 14px; }}
        .agent-name {{ color: #3b82f6; font-weight: bold; font-size: 24px; }}
        .inspirational {{ font-style: italic; color: #475569; margin: 15px 0; padding: 15px; background: #e0e7ff; border-radius: 8px; border-left: 4px solid #3b82f6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 ¡Compra Exitosa!</h1>
            <p>Tu Agente de IA está listo</p>
        </div>
        <div class="content">
            <p>¡Hola <strong>{customer_name}</strong>!</p>
            
            <p>¡Gracias por tu compra...! Tu Agente de IA <span class="agent-name">{agent_name}</span> <em>({access_label})</em> ya está disponible y listo para ayudarte.</p>
            
            <p class="inspirational">Lo que acabas de activar no es solo un agente… es una forma nueva de avanzar con más claridad, foco y libertad. Gracias por confiar. Aquí empieza algo grande. <strong>Bienvenido al Universo PSICOLFIS.NET.</strong></p>
            
            <p style="text-align: center;">
                <a href="{agent_url}" class="button">
                    🚀 Acceder a mi Agente {agent_name}
                </a>
            </p>

            <p style="font-size: 13px; color: #64748b; text-align: center; margin: 0 0 18px;">
              Este enlace es personal e intransferible. Te lleva directamente a tu agente dentro de psicolfis.net.
            </p>
            
            <p><strong>¿Qué puedes hacer ahora?</strong></p>
            <ul>
                <li>Accede a tu agente usando el botón de arriba</li>
                <li>Comienza a interactuar y multiplicar tu productividad</li>
                <li>Contacta con nosotros si tienes alguna duda</li>
            </ul>
            
            <p>Si tienes alguna pregunta, no dudes en responder a este email. Estamos para acompañarte y mantenernos en contacto.</p>
            
            <p>Recibe un afectuoso saludo,<br><strong>Obdulio Bailador</strong></p>
        </div>
        <div class="footer">
            <p><strong>PSICOLFIS.NET</strong></p>
            <p>Tu sabiduría. Nuestra IA. Resultados en acción.</p>
            <p>📧 obdulio@psicolfis.net | 🌐 psicolfis.net</p>
        </div>
    </div>
</body>
</html>
        """
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email using SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, customer_email, message.as_string())
        
        logger.info(f"Email sent successfully to {customer_email} for agent {agent_name}")
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
        await seed_reviews_if_empty()
    except Exception as e:
        logger.error(f"Seed error: {e}")


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
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Initialize Stripe
        stripe_api_key = os.environ.get('STRIPE_API_KEY')
        if not stripe_api_key:
            raise HTTPException(status_code=500, detail="Stripe API key not configured")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update database based on webhook event
        if webhook_response.event_type == "checkout.session.completed":
            # Get transaction info from database
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id}
            )
            
            # Update transaction status
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Send confirmation email if payment is complete
            if webhook_response.payment_status == "paid" and transaction:
                agent_id = transaction.get("agent_id", "")
                agent_info = AGENT_PACKAGES.get(agent_id.lower(), {})
                agent_name = agent_info.get("name", agent_id.upper())
                
                # Get customer email from Stripe session
                import stripe
                stripe.api_key = stripe_api_key
                session = stripe.checkout.Session.retrieve(webhook_response.session_id)
                customer_email = session.customer_details.email if session.customer_details else None
                customer_name = session.customer_details.name if session.customer_details else "Cliente"
                
                if customer_email:
                    # Determine access level: from metadata if provided, else "full"
                    purchase_metadata = transaction.get("metadata", {}) or {}
                    level = (purchase_metadata.get("level")
                             or webhook_response.metadata.get("level")
                             if hasattr(webhook_response, "metadata") and webhook_response.metadata
                             else purchase_metadata.get("level"))
                    level = (level or "full").lower()
                    if level not in ("demo", "full"):
                        level = "full"

                    email_sent = send_purchase_email(
                        customer_email=customer_email,
                        customer_name=customer_name or "Cliente",
                        agent_name=agent_name,
                        agent_id=agent_id,
                        level=level,
                    )
                    if email_sent:
                        logger.info(f"Confirmation email sent to {customer_email}")
                    else:
                        logger.warning(f"Failed to send email to {customer_email}")
            
            logger.info(f"Webhook processed for session {webhook_response.session_id}")
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
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
