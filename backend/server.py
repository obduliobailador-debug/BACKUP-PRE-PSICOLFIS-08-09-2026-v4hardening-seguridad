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
import asyncio
import jwt as pyjwt


# --- Bounded email helpers ---------------------------------------------------

SMTP_HARD_TIMEOUT = 12  # asyncio wall-clock cap for SMTP sends


async def _send_email_bounded(fn, /, **kwargs) -> bool:
    """Run a blocking SMTP helper in a worker thread with a hard wall-clock cap.

    Falls back to `False` on TimeoutError or any exception so the caller can
    persist `email_sent=false` and surface a graceful UX message instead of
    hanging or 500-ing.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, **kwargs),
            timeout=SMTP_HARD_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error(f"SMTP send exceeded {SMTP_HARD_TIMEOUT}s cap for {fn.__name__}")
        return False
    except Exception as e:
        logger.error(f"SMTP send crashed in {fn.__name__}: {e}")
        return False
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
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


# ----- Sector catalogue (vertical solutions) -----
# Each sector represents a B2B vertical with a dedicated landing page,
# a Pickaxe deployment ID for the embedded live demo, and CTAs that
# pre-fill the budget form with the sector slug.
SECTOR_CATALOGUE = [
    {
        "slug": "inmobiliarias",
        "name": "Inmobiliarias",
        "icon": "home",
        "tagline": "Cualifica leads y cierra visitas mientras atiendes a tus clientes.",
        "headline": "Tu agente IA para inmobiliarias: leads cualificados 24/7",
        "description": "Recibe consultas en cualquier momento, cualifica al instante (presupuesto, zona, urgencia) y agenda visitas reales en tu calendario. Lo que antes te quitaba 2 horas al día, ahora se gestiona solo.",
        "problem": "Cada lead que tarda más de 5 minutos en recibir respuesta se pierde. Y tú no puedes estar pegado al móvil 14 horas. Resultado: oportunidades cerradas con la competencia.",
        "solution": "Un agente entrenado con tu cartera y tu forma de hablar, que responde en WhatsApp/web en segundos, califica al cliente, descarta curiosos y solo te pasa los leads listos para visita.",
        "use_cases": [
            "Cualificación automática: presupuesto, zona preferida, plazos, financiación.",
            "Envío automático de fichas de inmuebles que encajan con la búsqueda.",
            "Agendado de visitas con confirmación y recordatorio 24h antes.",
            "Reactivación de leads en frío con el propio histórico de la inmobiliaria.",
            "Follow-up post-visita y captación de feedback automático.",
        ],
        "metrics": [
            {"label": "Leads cualificados", "value": "+180%"},
            {"label": "Tiempo de respuesta", "value": "<30 s"},
            {"label": "Coste por visita", "value": "-45%"},
        ],
        "ideal_for": "Inmobiliarias con 1-15 agentes, agencias franquiciadas, profesionales independientes.",
        "demo_intro": "Prueba el agente como si fueras un cliente: pregunta por un piso, di tu presupuesto, prueba a regatear.",
        "deployment_env": "PICKAXE_DEPLOYMENT_SECTOR_INMOBILIARIAS",
    },
    {
        "slug": "clinicas-dentales",
        "name": "Clínicas dentales",
        "icon": "tooth",
        "tagline": "Reduce cancelaciones, recupera pacientes inactivos y libera tu recepción.",
        "headline": "Tu agente IA para clínicas dentales: menos huecos, más pacientes",
        "description": "Recordatorios inteligentes que reducen cancelaciones, reactivación automática de pacientes que llevan meses sin volver y triaje 24/7 para urgencias y dudas habituales.",
        "problem": "La recepción está saturada, las cancelaciones de última hora dejan huecos imposibles de rellenar y los pacientes inactivos rara vez vuelven sin un empujón.",
        "solution": "Un agente que conversa con tus pacientes en WhatsApp, gestiona recordatorios, ofrece reagendar al instante cuando alguien cancela, y reactiva con mensajes personalizados a quienes no han venido en 6+ meses.",
        "use_cases": [
            "Recordatorio inteligente 48h y 4h antes de cada cita (con confirmación de un clic).",
            "Reagendado automático cuando hay una cancelación: ofrece el hueco a una lista de espera.",
            "Reactivación de pacientes inactivos con campañas personalizadas (limpieza, revisión).",
            "Primer triaje de urgencias: distingue dolor real de consulta general y prioriza.",
            "Información sobre tratamientos, financiación y presupuestos orientativos 24/7.",
        ],
        "metrics": [
            {"label": "Cancelaciones de último minuto", "value": "-40%"},
            {"label": "Pacientes inactivos recuperados", "value": "+22%"},
            {"label": "Llamadas a recepción", "value": "-55%"},
        ],
        "ideal_for": "Clínicas dentales independientes, pequeñas cadenas, ortodoncistas y odontopediatras.",
        "demo_intro": "Pídele información sobre una endodoncia, intenta cancelar una cita, prueba a preguntar por financiación.",
        "deployment_env": "PICKAXE_DEPLOYMENT_SECTOR_DENTAL",
    },
    {
        "slug": "salones-belleza",
        "name": "Salones de belleza y estética",
        "icon": "sparkles",
        "tagline": "Reservas 24/7 por WhatsApp, upsell automático y clientas que vuelven solas.",
        "headline": "Tu agente IA para salones de belleza: reservas que no cuelgan",
        "description": "Tus clientas reservan, mueven o cancelan citas a cualquier hora directamente por WhatsApp, reciben sugerencias de tratamientos complementarios y vuelven solas con recordatorios personalizados.",
        "problem": "Pierdes citas porque al final del día no contestas mensajes, las clientas no saben qué tratamiento les conviene, y mantener la fidelización es una carga manual diaria.",
        "solution": "Un agente que conversa con tus clientas como lo harías tú: las asesora, agenda en tu calendario en segundos, sugiere tratamientos complementarios y reactiva fechas clave (cumpleaños, retoque de color, evento especial).",
        "use_cases": [
            "Reservas, cambios y cancelaciones por WhatsApp 24/7 con calendario sincronizado.",
            "Asesoramiento personalizado: 'Tengo una boda en 3 semanas' → propuesta automática.",
            "Upsell inteligente: cuando alguien reserva un corte, sugiere mascarilla o tratamiento.",
            "Recordatorios de fidelización: retoque de color, manicura semanal, eventos.",
            "Recuperación de huecos cancelados ofreciéndolos a clientas habituales.",
        ],
        "metrics": [
            {"label": "Reservas fuera de horario", "value": "+35%"},
            {"label": "Ticket medio", "value": "+18%"},
            {"label": "Clientas recurrentes", "value": "+27%"},
        ],
        "ideal_for": "Peluquerías, centros de estética, barberías, clínicas de manicura/pedicura, spas urbanos.",
        "demo_intro": "Reserva un corte de pelo, pídele consejo para un evento, intenta cambiar la fecha.",
        "deployment_env": "PICKAXE_DEPLOYMENT_SECTOR_BEAUTY",
    },
]


def _public_sector(s: dict, *, include_deployment: bool = False) -> dict:
    """Serialize a sector for the public API (optionally with deployment id)."""
    out = {k: v for k, v in s.items() if k not in ("deployment_env", "_id", "deployment_id", "hidden", "deleted_at", "created_at", "updated_at")}
    if include_deployment:
        # Prefer stored deployment_id (edited from admin); fall back to env var for legacy seed
        stored = s.get("deployment_id", "") if isinstance(s, dict) else ""
        env_val = os.environ.get(s.get("deployment_env", ""), "") if s.get("deployment_env") else ""
        out["deployment_id"] = stored or env_val or ""
    return out


async def seed_sectors_if_empty():
    """Seed the `sectors` Mongo collection from the in-code catalogue.

    Runs on startup. Only inserts sectors that don't yet exist by slug so it's
    idempotent and preserves any admin edits. `deployment_id` is resolved from
    the corresponding env var at seed time so operators can pre-configure
    Pickaxe deployments through .env if they prefer.
    """
    for s in SECTOR_CATALOGUE:
        existing = await db.sectors.find_one({"slug": s["slug"]})
        if existing:
            continue
        doc = {**s}
        # Materialize deployment id from env for first seed
        env_key = doc.pop("deployment_env", "")
        doc["deployment_env"] = env_key  # keep for future reads
        doc["deployment_id"] = os.environ.get(env_key, "") if env_key else ""
        doc["hidden"] = False
        doc["deleted_at"] = None
        now = datetime.now(timezone.utc).isoformat()
        doc["created_at"] = now
        doc["updated_at"] = now
        doc["id"] = str(uuid.uuid4())
        await db.sectors.insert_one(doc)
        logger.info(f"Seeded sector: {s['slug']}")


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
    """Validate and decode a JWT access token. Raises HTTPException on failure.

    Also checks an optional MongoDB denylist (collection `revoked_tokens`)
    keyed by the JWT `jti`, so admin-revoked links stop working immediately.
    """
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El enlace de acceso ha caducado. Contacta con nosotros para renovarlo.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Enlace de acceso no válido.")
    if not payload.get("agent") or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Token de acceso incompleto.")
    return payload


async def is_token_revoked(jti: str) -> bool:
    if not jti:
        return False
    try:
        doc = await db.revoked_tokens.find_one({"jti": jti}, {"_id": 0, "jti": 1})
        return bool(doc)
    except Exception as e:
        logger.error(f"revoked_tokens lookup failed: {e}")
        return False


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
        
        # Send email using SSL with a 5s timeout so an unreachable host
        # doesn't block the request for 60-90s (DoS surface). See also the
        # asyncio.wait_for wrapper at the call sites for a hard <13s cap.
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=5) as server:
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
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=5) as server:
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
    """Verify HMAC signature and freshness. Does NOT enforce single-use;
    call `consume_captcha_token` afterwards to burn it in Mongo."""
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


async def consume_captcha_token(token: str) -> bool:
    """Mark a captcha token as used so it can't be replayed. Returns True on
    first use, False if already consumed. Uses `captcha_used` collection with
    a Mongo TTL index (30 min) so old entries auto-purge."""
    try:
        now = datetime.now(timezone.utc)
        res = await db.captcha_used.update_one(
            {"token": token},
            {"$setOnInsert": {"token": token, "used_at": now}},
            upsert=True,
        )
        return res.upserted_id is not None
    except Exception as e:
        logger.error(f"consume_captcha_token failed: {e}")
        # Fail closed: if the DB write fails, refuse. Better than allowing replay.
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


@api_router.get("/sectors")
async def list_sectors():
    """Public list of B2B verticals shown on /soluciones.

    Reads from MongoDB, excludes hidden and soft-deleted sectors.
    """
    cursor = db.sectors.find(
        {"hidden": {"$ne": True}, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", 1)
    items = await cursor.to_list(100)
    return {
        "items": [_public_sector(s, include_deployment=False) for s in items],
        "total": len(items),
    }


@api_router.get("/sectors/{slug}")
async def get_sector(slug: str):
    """Public detail for a single sector (includes Pickaxe deployment id).

    Hidden and soft-deleted sectors return 404 publicly.
    """
    slug = (slug or "").lower().strip()
    sector = await db.sectors.find_one(
        {"slug": slug, "hidden": {"$ne": True}, "deleted_at": None},
        {"_id": 0}
    )
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    return _public_sector(sector, include_deployment=True)


@app.get("/sitemap.xml")
@api_router.get("/sitemap.xml")
async def dynamic_sitemap():
    """Dynamic sitemap that always includes all active sector landings.

    Exposed both at /sitemap.xml (declared in robots.txt) AND /api/sitemap.xml
    because the K8s ingress only routes /api/* to the backend; the /api/
    version is the reachable one from the public internet.
    """
    from fastapi.responses import Response
    base = PUBLIC_BASE_URL
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    static_paths = [
        ("/", "1.0", "weekly"),
        ("/agentes", "0.9", "weekly"),
        ("/soluciones", "0.9", "weekly"),
        ("/legal", "0.3", "yearly"),
    ]
    cursor = db.sectors.find(
        {"hidden": {"$ne": True}, "deleted_at": None},
        {"_id": 0, "slug": 1}
    )
    active_slugs = await cursor.to_list(100)
    sector_paths = [(f"/soluciones/{s['slug']}", "0.85", "monthly") for s in active_slugs]

    urls_xml = "\n".join(
        f"  <url><loc>{base}{path}</loc><lastmod>{now}</lastmod><changefreq>{cf}</changefreq><priority>{pri}</priority></url>"
        for path, pri, cf in static_paths + sector_paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls_xml}\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")

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
    if not await consume_captcha_token(request.captcha_token):
        raise HTTPException(
            status_code=400,
            detail="Este captcha ya fue usado. Refresca la página y resuelve el nuevo."
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

    email_sent = await _send_email_bounded(
        send_budget_request_email,
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
    if not await consume_captcha_token(payload.captcha_token):
        raise HTTPException(
            status_code=400,
            detail="Este captcha ya fue usado. Refresca la página y resuelve el nuevo."
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
    if await is_token_revoked(payload.get("jti", "")):
        raise HTTPException(status_code=401, detail="Este enlace ha sido revocado. Contacta con nosotros si necesitas un nuevo acceso.")
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
    x_service_key: Optional[str] = Header(default=None, alias="X-Service-Key"),
):
    """Render the welcome email HTML for QA without sending it.

    Generates a real signed token tied to the requested agent + level so the
    embedded CTA points to a working /mi-agente/:token URL on production.
    Auth: SERVICE_API_KEY via the `X-Service-Key` header only (query-string
    variant removed to avoid leaks in logs/referrer).
    """
    from fastapi.responses import HTMLResponse
    from email_templates import render_email

    if not SERVICE_API_KEY or not x_service_key or x_service_key != SERVICE_API_KEY:
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


def _extract_client_ip(request: Request) -> str:
    """Return the client IP, trusting only the first hop from x-forwarded-for
    when we run behind a single reverse proxy. Prevents lockout bypass by
    attackers that rotate the XFF header themselves.

    The `TRUSTED_PROXY_HOPS` env var (default 1) tells us how many trusted
    hops precede us. We take the value at index -N from the XFF list.
    """
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        try:
            hops = int(os.environ.get("TRUSTED_PROXY_HOPS", "1"))
        except ValueError:
            hops = 1
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            # -hops indexes from the right; clamp to first element as safe fallback
            idx = max(-len(parts), -max(hops, 1))
            return parts[idx]
    return request.client.host if request.client else "unknown"


@api_router.post("/admin/login")
async def admin_login(payload: AdminLoginRequest, request: Request):
    email = payload.email.lower().strip()
    ip = _extract_client_ip(request)
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=LOGIN_LOCK_WINDOW_MIN)

    # Per-account throttle (independent of IP): stops distributed guessing
    # from rotating XFF or coming through multiple exit nodes.
    account_failed = await db.login_attempts.count_documents({
        "email": email,
        "ts": {"$gte": window_start.isoformat()},
        "success": False,
    })
    if account_failed >= LOGIN_LOCK_MAX_ATTEMPTS * 3:
        raise HTTPException(status_code=429, detail="Demasiados intentos para esta cuenta. Espera unos minutos.")

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


@api_router.delete("/admin/budget-requests/{request_id}")
async def admin_delete_budget_request(
    request_id: str,
    admin: dict = Depends(get_current_admin),
):
    res = await db.budget_requests.delete_one({"id": request_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"success": True}


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


# ---- Admin: regalar accesos manualmente ----------------------------------

class AdminAccessLinkRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = ""
    agent_id: str
    level: str = "full"  # "demo" or "full"
    days_valid: Optional[int] = None
    send_email: bool = True

    @field_validator("level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        v = (v or "full").lower().strip()
        if v not in ("demo", "full"):
            raise ValueError("level debe ser 'demo' o 'full'")
        return v


def _decode_jti(token: str) -> str:
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("jti", "")
    except Exception:
        return ""


async def _create_and_persist_access_link(
    *,
    admin_email: str,
    customer_email: str,
    customer_name: str,
    agent_id: str,
    level: str,
    days_valid: Optional[int],
    send_email: bool,
) -> dict:
    """Generate token, optionally send email, persist a record, return metadata."""
    info = get_agent_info(agent_id, level=level)
    if not info or not info.get("deployment_id"):
        raise HTTPException(status_code=400, detail="Agente o nivel no válido.")

    token = generate_access_token(
        customer_email=customer_email,
        agent_id=info["id"],
        level=info["level"],
        customer_name=customer_name or "",
        days_valid=days_valid,
    )
    url = build_agent_access_url(token)
    jti = _decode_jti(token)

    email_status = "skipped"
    last_sent_at = None
    if send_email:
        ok = await _send_email_bounded(
            send_purchase_email,
            customer_email=customer_email,
            customer_name=customer_name or "",
            agent_name=info["name"],
            agent_id=info["id"],
            level=info["level"],
        )
        email_status = "sent" if ok else "failed"
        if ok:
            last_sent_at = datetime.now(timezone.utc).isoformat()

    record = {
        "id": str(uuid.uuid4()),
        "jti": jti,
        "agent_id": info["id"],
        "agent_name": info["name"],
        "level": info["level"],
        "customer_email": customer_email.lower().strip(),
        "customer_name": customer_name or "",
        "url": url,
        "days_valid": days_valid or ACCESS_TOKEN_DAYS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin_email,
        "email_status": email_status,
        "last_sent_at": last_sent_at,
        "revoked": False,
        "revoked_at": None,
    }
    await db.access_links.insert_one(record)
    record.pop("_id", None)
    return record


@api_router.post("/admin/access-links")
async def admin_create_access_link(
    payload: AdminAccessLinkRequest,
    admin: dict = Depends(get_current_admin),
):
    """Generate a personal access link manually (gift / partner / replay).

    If `send_email` is True, the customer receives the same welcome email
    Stripe purchases trigger. The link plus metadata is persisted in
    `access_links` so the admin can re-send or revoke later.
    """
    record = await _create_and_persist_access_link(
        admin_email=admin["sub"],
        customer_email=payload.customer_email,
        customer_name=payload.customer_name or "",
        agent_id=payload.agent_id,
        level=payload.level,
        days_valid=payload.days_valid,
        send_email=payload.send_email,
    )
    return {"success": True, "link": record}


@api_router.get("/admin/access-links")
async def admin_list_access_links(admin: dict = Depends(get_current_admin)):
    cursor = db.access_links.find({}, {"_id": 0}).sort("created_at", -1).limit(50)
    items = await cursor.to_list(50)
    return {"items": items, "total": len(items)}


@api_router.post("/admin/access-links/{link_id}/resend")
async def admin_resend_access_link(
    link_id: str,
    admin: dict = Depends(get_current_admin),
):
    rec = await db.access_links.find_one({"id": link_id}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    if rec.get("revoked"):
        raise HTTPException(status_code=400, detail="No se puede reenviar un enlace revocado")

    ok = await _send_email_bounded(
        send_purchase_email,
        customer_email=rec["customer_email"],
        customer_name=rec.get("customer_name", ""),
        agent_name=rec.get("agent_name") or rec.get("agent_id", "").upper(),
        agent_id=rec["agent_id"],
        level=rec.get("level", "full"),
    )
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.access_links.update_one(
        {"id": link_id},
        {"$set": {
            "email_status": "sent" if ok else "failed",
            "last_sent_at": now_iso if ok else rec.get("last_sent_at"),
        }},
    )
    return {
        "success": ok,
        "email_status": "sent" if ok else "failed",
        "last_sent_at": now_iso if ok else rec.get("last_sent_at"),
        "message": "Email reenviado correctamente." if ok else "No se pudo enviar el email. Revisa la configuración SMTP.",
    }


@api_router.post("/admin/access-links/{link_id}/revoke")
async def admin_revoke_access_link(
    link_id: str,
    admin: dict = Depends(get_current_admin),
):
    rec = await db.access_links.find_one({"id": link_id}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    if rec.get("revoked"):
        return {"success": True, "already": True}

    jti = rec.get("jti", "")
    if jti:
        await db.revoked_tokens.update_one(
            {"jti": jti},
            {"$set": {
                "jti": jti,
                "link_id": link_id,
                "customer_email": rec.get("customer_email"),
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoked_by": admin["sub"],
            }},
            upsert=True,
        )

    await db.access_links.update_one(
        {"id": link_id},
        {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"success": True}


@api_router.delete("/admin/access-links/{link_id}")
async def admin_delete_access_link(
    link_id: str,
    admin: dict = Depends(get_current_admin),
):
    """Remove the link from history. Does NOT auto-revoke; call /revoke first
    if you want the link to stop working."""
    res = await db.access_links.delete_one({"id": link_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return {"success": True}


# ---- Admin: sector CMS -----------------------------------------------------

import re as _re

_SLUG_RE = _re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class SectorMetric(BaseModel):
    label: str
    value: str


class SectorUpsertRequest(BaseModel):
    slug: str
    name: str
    icon: Optional[str] = ""
    tagline: Optional[str] = ""
    headline: Optional[str] = ""
    description: Optional[str] = ""
    problem: Optional[str] = ""
    solution: Optional[str] = ""
    ideal_for: Optional[str] = ""
    demo_intro: Optional[str] = ""
    use_cases: List[str] = []
    metrics: List[SectorMetric] = []
    deployment_id: Optional[str] = ""
    hidden: bool = False


class SectorVisibilityRequest(BaseModel):
    hidden: bool


def _validate_slug(slug: str) -> str:
    slug = (slug or "").lower().strip()
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Slug inválido. Usa solo minúsculas, números y guiones (ej. mi-sector).")
    return slug


@api_router.get("/admin/sectors")
async def admin_list_sectors(admin: dict = Depends(get_current_admin)):
    """Full list including hidden and soft-deleted sectors (for the CMS UI)."""
    cursor = db.sectors.find({}, {"_id": 0}).sort("created_at", 1)
    items = await cursor.to_list(200)
    active = [s for s in items if not s.get("hidden") and not s.get("deleted_at")]
    hidden = [s for s in items if s.get("hidden") and not s.get("deleted_at")]
    trash  = [s for s in items if s.get("deleted_at")]
    return {"items": items, "active": len(active), "hidden": len(hidden), "trash": len(trash)}


@api_router.post("/admin/sectors")
async def admin_create_sector(
    payload: SectorUpsertRequest,
    admin: dict = Depends(get_current_admin),
):
    slug = _validate_slug(payload.slug)
    existing = await db.sectors.find_one({"slug": slug})
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un sector con este slug.")
    now = datetime.now(timezone.utc).isoformat()
    doc = payload.model_dump()
    doc["slug"] = slug
    doc["metrics"] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in (doc.get("metrics") or [])]
    doc["id"] = str(uuid.uuid4())
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["created_by"] = admin["sub"]
    doc["deleted_at"] = None
    doc["deployment_env"] = ""
    await db.sectors.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "sector": doc}


@api_router.patch("/admin/sectors/{slug}")
async def admin_update_sector(
    slug: str,
    payload: SectorUpsertRequest,
    admin: dict = Depends(get_current_admin),
):
    slug = _validate_slug(slug)
    existing = await db.sectors.find_one({"slug": slug})
    if not existing:
        raise HTTPException(status_code=404, detail="Sector no encontrado")

    new_slug = _validate_slug(payload.slug)
    if new_slug != slug:
        collision = await db.sectors.find_one({"slug": new_slug})
        if collision:
            raise HTTPException(status_code=409, detail="Ya existe otro sector con ese slug.")

    update = payload.model_dump()
    update["slug"] = new_slug
    update["metrics"] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in (update.get("metrics") or [])]
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.sectors.update_one({"slug": slug}, {"$set": update})
    doc = await db.sectors.find_one({"slug": new_slug}, {"_id": 0})
    return {"success": True, "sector": doc}


@api_router.post("/admin/sectors/{slug}/visibility")
async def admin_toggle_sector_visibility(
    slug: str,
    payload: SectorVisibilityRequest,
    admin: dict = Depends(get_current_admin),
):
    slug = _validate_slug(slug)
    res = await db.sectors.update_one(
        {"slug": slug},
        {"$set": {"hidden": bool(payload.hidden), "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    return {"success": True, "hidden": bool(payload.hidden)}


@api_router.delete("/admin/sectors/{slug}")
async def admin_soft_delete_sector(
    slug: str,
    admin: dict = Depends(get_current_admin),
):
    """Soft delete: sets deleted_at. Restore possible within 30 days via /restore."""
    slug = _validate_slug(slug)
    res = await db.sectors.update_one(
        {"slug": slug},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    return {"success": True}


@api_router.post("/admin/sectors/{slug}/restore")
async def admin_restore_sector(
    slug: str,
    admin: dict = Depends(get_current_admin),
):
    slug = _validate_slug(slug)
    res = await db.sectors.update_one(
        {"slug": slug},
        {"$set": {"deleted_at": None, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    return {"success": True}


@api_router.delete("/admin/sectors/{slug}/permanent")
async def admin_hard_delete_sector(
    slug: str,
    admin: dict = Depends(get_current_admin),
):
    """Hard delete. Only allowed on already soft-deleted sectors."""
    slug = _validate_slug(slug)
    existing = await db.sectors.find_one({"slug": slug})
    if not existing:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    if not existing.get("deleted_at"):
        raise HTTPException(status_code=400, detail="Primero mueve el sector a la papelera antes de eliminarlo definitivamente.")
    await db.sectors.delete_one({"slug": slug})
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
        await seed_sectors_if_empty()
    except Exception as e:
        logger.error(f"Sector seed error: {e}")
    try:
        await db.admin_users.create_index("email", unique=True)
        await db.login_attempts.create_index("identifier")
        await db.login_attempts.create_index([("ts", 1)])
        await db.access_links.create_index([("created_at", -1)])
        await db.access_links.create_index("id", unique=True)
        await db.revoked_tokens.create_index("jti", unique=True)
        await db.sectors.create_index("slug", unique=True)
        await db.sectors.create_index([("created_at", 1)])
        # Anti-replay: captcha_used entries expire after 30 min (max token TTL)
        await db.captcha_used.create_index("token", unique=True)
        await db.captcha_used.create_index("used_at", expireAfterSeconds=1800)
        # Stripe idempotency
        await db.stripe_events.create_index("event_id", unique=True)
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

        # Idempotency: swallow replayed webhook events by remembering the id.
        event_id = event.get("id")
        if event_id:
            dedup = await db.stripe_events.update_one(
                {"event_id": event_id},
                {"$setOnInsert": {
                    "event_id": event_id,
                    "type": event.get("type"),
                    "received_at": datetime.now(timezone.utc).isoformat(),
                }},
                upsert=True,
            )
            if dedup.upserted_id is None:
                logger.info(f"Stripe webhook event {event_id} already processed, skipping.")
                return JSONResponse(content={"status": "duplicate", "event_id": event_id}, status_code=200)

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

            email_sent = await _send_email_bounded(
                send_purchase_email,
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
    allow_origins=[o.strip() for o in os.environ.get(
        'CORS_ORIGINS',
        'https://psicolfis.net,https://www.psicolfis.net'
    ).split(',') if o.strip()],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Service-Key", "Stripe-Signature"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
