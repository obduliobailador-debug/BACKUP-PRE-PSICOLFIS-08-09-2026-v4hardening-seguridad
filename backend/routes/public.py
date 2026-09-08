"""Public API endpoints: root, sectors, sitemap, video, status, whatsapp,
captcha, budget requests, reviews, and access-token validation."""
from __future__ import annotations

import random
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse

from catalogues import get_agent_info, public_sector
from config import (
    CAPTCHA_TTL_SECONDS,
    PUBLIC_BASE_URL,
    STATIC_DIR,
    WHATSAPP_DEFAULT_TEXT,
    WHATSAPP_NUMBER,
    db,
    logger,
)
from email_service import send_budget_request_email, send_email_bounded
from models import (
    BudgetRequest,
    ReviewCreate,
    StatusCheck,
    StatusCheckCreate,
)
from security import (
    build_captcha_signature,
    consume_captcha_token,
    decode_access_token,
    is_token_revoked,
    verify_captcha,
)


router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Hello World"}


# ---- Sectors ---------------------------------------------------------------

@router.get("/sectors")
async def list_sectors():
    """Public list of B2B verticals shown on /soluciones."""
    cursor = db.sectors.find(
        {"hidden": {"$ne": True}, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", 1)
    items = await cursor.to_list(100)
    return {
        "items": [public_sector(s, include_deployment=False) for s in items],
        "total": len(items),
    }


@router.get("/sectors/{slug}")
async def get_sector(slug: str):
    """Public detail for a single sector (includes Pickaxe deployment id)."""
    slug = (slug or "").lower().strip()
    sector = await db.sectors.find_one(
        {"slug": slug, "hidden": {"$ne": True}, "deleted_at": None},
        {"_id": 0}
    )
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    return public_sector(sector, include_deployment=True)


# ---- Sitemap ---------------------------------------------------------------

async def _dynamic_sitemap_response():
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


@router.get("/sitemap.xml")
async def dynamic_sitemap():
    """Dynamic sitemap under /api/sitemap.xml."""
    return await _dynamic_sitemap_response()


# ---- Video streaming -------------------------------------------------------

@router.get("/video/{filename}")
async def stream_video(filename: str, request: Request):
    """Stream video with range request support for better browser compatibility."""
    video_path = STATIC_DIR / filename

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    file_size = video_path.stat().st_size
    range_header = request.headers.get("range")

    if range_header:
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
        return FileResponse(
            video_path,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Cache-Control": "public, max-age=86400",
            }
        )


# ---- Status checks ---------------------------------------------------------

@router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@router.get("/status", response_model=list[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ---- WhatsApp redirect -----------------------------------------------------

@router.get("/whatsapp")
async def whatsapp_redirect():
    """Server-side redirect that hides the real WhatsApp number from HTML."""
    text = quote(WHATSAPP_DEFAULT_TEXT)
    target = f"https://wa.me/{WHATSAPP_NUMBER}?text={text}"
    return RedirectResponse(url=target, status_code=302, headers={"Cache-Control": "no-store"})


# ---- Captcha ---------------------------------------------------------------

@router.get("/captcha")
async def get_captcha():
    """Issue a simple signed math CAPTCHA challenge."""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    answer = str(a + b)
    issued_at = int(time.time())
    signature = build_captcha_signature(answer, issued_at)
    return {
        "question": f"¿Cuánto es {a} + {b}?",
        "token": f"{issued_at}.{signature}",
        "ttl_seconds": CAPTCHA_TTL_SECONDS,
    }


# ---- Budget request --------------------------------------------------------

@router.post("/contact/budget")
async def submit_budget_request(request: BudgetRequest):
    """Receive budget request from the landing page form and email it to the owner."""
    nombre = request.nombre.strip()
    email = request.email.strip()
    plan = request.plan.strip()

    if not nombre or not email or not plan:
        raise HTTPException(status_code=400, detail="Nombre, email y plan son obligatorios")

    if request.website and request.website.strip():
        logger.warning(f"Honeypot triggered for email {email} - rejecting")
        raise HTTPException(status_code=400, detail="Solicitud no válida")

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

    email_sent = await send_email_bounded(
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


# ---- Reviews ---------------------------------------------------------------

@router.get("/reviews")
async def list_reviews():
    """Return the published (approved) reviews, newest first."""
    cursor = db.reviews.find(
        {"approved": True},
        {"_id": 0, "email": 0}  # never expose email publicly
    ).sort("created_at", -1).to_list(100)
    reviews = await cursor

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


@router.post("/reviews")
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
        "approved": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.reviews.insert_one(review.copy())
    review.pop("_id", None)
    logger.info(f"New review from {author} with rating {payload.rating}")
    return {"success": True, "review": review}


# ---- Access token validation ----------------------------------------------

@router.get("/access/validate")
async def validate_access_token(token: str):
    """Validate a JWT access token and return the agent metadata to embed."""
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


# ---- Agent photo -----------------------------------------------------------

@router.get("/agents/{agent_id}/photo")
async def get_agent_photo(agent_id: str):
    """Serve a static portrait image for an agent (used in emails)."""
    agent_id = (agent_id or "").lower()
    if agent_id not in {"iris", "alex", "umbral"}:
        raise HTTPException(status_code=404, detail="Not found")
    img_path = STATIC_DIR / "agents" / f"{agent_id}.jpg"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(
        img_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
