"""Central configuration: env vars, Mongo client, logger, JWT settings.

Everything here is imported once at process start. Modules should read
`db`, `logger`, and constants from here to avoid duplicating dotenv/logging
setup.
"""
from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ---- MongoDB ---------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ---- Logging ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("psicolfis")

# ---- SMTP ------------------------------------------------------------------
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'psicolfis.net')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_USER = os.environ.get('SMTP_USER', 'obdulio@psicolfis.net')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', 'obdulio@psicolfis.net')

# ---- Public URLs -----------------------------------------------------------
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'https://psicolfis.net').rstrip('/')

WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '34670716305')
WHATSAPP_DEFAULT_TEXT = os.environ.get(
    'WHATSAPP_DEFAULT_TEXT',
    'Hola Obdulio, te escribo desde psicolfis.net'
)

# ---- JWT / Access tokens ---------------------------------------------------
JWT_SECRET = os.environ.get('JWT_SECRET') or secrets.token_hex(64)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_DAYS = int(os.environ.get('ACCESS_TOKEN_DAYS', '365'))

# ---- Service key (for internal admin endpoints) ----------------------------
SERVICE_API_KEY = os.environ.get('SERVICE_API_KEY', '')

# ---- Admin auth ------------------------------------------------------------
ADMIN_EMAIL = (os.environ.get("ADMIN_EMAIL") or "").lower().strip()
ADMIN_PASSWORD_PLAIN = os.environ.get("ADMIN_PASSWORD") or ""
ADMIN_TOKEN_HOURS = int(os.environ.get("ADMIN_TOKEN_HOURS", "8"))
LOGIN_LOCK_MAX_ATTEMPTS = 5
LOGIN_LOCK_WINDOW_MIN = 15

# ---- Captcha ---------------------------------------------------------------
CAPTCHA_SECRET = os.environ.get('CAPTCHA_SECRET') or secrets.token_hex(32)
CAPTCHA_TTL_SECONDS = 600  # 10 minutes

# ---- SMTP async timeout ----------------------------------------------------
SMTP_HARD_TIMEOUT = 12  # asyncio wall-clock cap for SMTP sends

# ---- Static files ----------------------------------------------------------
STATIC_DIR = ROOT_DIR / "static"

# ---- CORS ------------------------------------------------------------------
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    'CORS_ORIGINS',
    'https://psicolfis.net,https://www.psicolfis.net'
).split(',') if o.strip()]
