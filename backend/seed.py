"""Startup seed helpers: admin user, starter reviews, sector catalogue."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from config import ADMIN_EMAIL, ADMIN_PASSWORD_PLAIN, db, logger
from catalogues import SECTOR_CATALOGUE
from security import hash_password, verify_password


async def seed_admin_if_needed():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD_PLAIN:
        logger.warning("Admin not seeded - ADMIN_EMAIL or ADMIN_PASSWORD missing in .env")
        return
    existing = await db.admin_users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        await db.admin_users.insert_one({
            "id": str(uuid.uuid4()),
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD_PLAIN),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin seeded: {ADMIN_EMAIL}")
    elif not verify_password(ADMIN_PASSWORD_PLAIN, existing.get("password_hash", "")):
        await db.admin_users.update_one(
            {"email": ADMIN_EMAIL},
            {"$set": {"password_hash": hash_password(ADMIN_PASSWORD_PLAIN)}},
        )
        logger.info(f"Admin password rotated: {ADMIN_EMAIL}")


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


async def seed_sectors_if_empty():
    """Seed the `sectors` Mongo collection from the in-code catalogue.

    Only inserts sectors that don't yet exist by slug so it's idempotent and
    preserves any admin edits.
    """
    for s in SECTOR_CATALOGUE:
        existing = await db.sectors.find_one({"slug": s["slug"]})
        if existing:
            continue
        doc = {**s}
        env_key = doc.pop("deployment_env", "")
        doc["deployment_env"] = env_key
        doc["deployment_id"] = os.environ.get(env_key, "") if env_key else ""
        doc["hidden"] = False
        doc["deleted_at"] = None
        now = datetime.now(timezone.utc).isoformat()
        doc["created_at"] = now
        doc["updated_at"] = now
        doc["id"] = str(uuid.uuid4())
        await db.sectors.insert_one(doc)
        logger.info(f"Seeded sector: {s['slug']}")


async def ensure_indexes():
    """Create required Mongo indexes on startup."""
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
