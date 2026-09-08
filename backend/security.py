"""Security helpers: JWT tokens, password hashing, captcha, admin dependency."""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

import bcrypt as _bcrypt
import jwt as pyjwt
from fastapi import HTTPException, Request

from config import (
    ACCESS_TOKEN_DAYS,
    ADMIN_TOKEN_HOURS,
    CAPTCHA_SECRET,
    CAPTCHA_TTL_SECONDS,
    JWT_ALGORITHM,
    JWT_SECRET,
    PUBLIC_BASE_URL,
    db,
    logger,
)


# ---- Passwords -------------------------------------------------------------

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---- Access tokens (customer JWT for Pickaxe agents) -----------------------

def generate_access_token(
    customer_email: str,
    agent_id: str,
    level: str = "full",
    customer_name: str = "",
    days_valid: int | None = None,
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


def decode_jti(token: str) -> str:
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("jti", "")
    except Exception:
        return ""


# ---- Admin JWT + dependency ------------------------------------------------

def create_admin_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email.lower(),
        "role": "admin",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ADMIN_TOKEN_HOURS)).timestamp()),
        "jti": uuid.uuid4().hex,
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


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


# ---- Captcha ---------------------------------------------------------------

def build_captcha_signature(answer: str, issued_at: int) -> str:
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
        expected = build_captcha_signature(user_answer.strip(), issued_at)
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


async def consume_captcha_token(token: str) -> bool:
    """Mark a captcha token as used so it can't be replayed. Returns True on
    first use, False if already consumed."""
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
        return False


# ---- Client IP (behind proxy) ---------------------------------------------

def extract_client_ip(request: Request) -> str:
    """Return the client IP, trusting only the first hop from x-forwarded-for
    when we run behind a single reverse proxy."""
    import os
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        try:
            hops = int(os.environ.get("TRUSTED_PROXY_HOPS", "1"))
        except ValueError:
            hops = 1
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            idx = max(-len(parts), -max(hops, 1))
            return parts[idx]
    return request.client.host if request.client else "unknown"
