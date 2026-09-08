"""Admin routes: login/me, budget requests, reviews moderation, access links, sectors CMS."""
from __future__ import annotations

import re as _re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from catalogues import get_agent_info
from config import (
    ACCESS_TOKEN_DAYS,
    ADMIN_TOKEN_HOURS,
    LOGIN_LOCK_MAX_ATTEMPTS,
    LOGIN_LOCK_WINDOW_MIN,
    db,
)
from email_service import send_email_bounded, send_purchase_email
from models import (
    AdminAccessLinkRequest,
    AdminLoginRequest,
    MarkReadRequest,
    ReviewModerationRequest,
    SectorUpsertRequest,
    SectorVisibilityRequest,
)
from security import (
    build_agent_access_url,
    create_admin_token,
    decode_jti,
    extract_client_ip,
    generate_access_token,
    get_current_admin,
    verify_password,
)


router = APIRouter(prefix="/admin")

_SLUG_RE = _re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validate_slug(slug: str) -> str:
    slug = (slug or "").lower().strip()
    if not _SLUG_RE.match(slug):
        raise HTTPException(status_code=400, detail="Slug inválido. Usa solo minúsculas, números y guiones (ej. mi-sector).")
    return slug


# ---- Auth ------------------------------------------------------------------

@router.post("/login")
async def admin_login(payload: AdminLoginRequest, request: Request):
    email = payload.email.lower().strip()
    ip = extract_client_ip(request)
    identifier = f"{ip}:{email}"
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=LOGIN_LOCK_WINDOW_MIN)

    # Per-account throttle (independent of IP)
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
    ok = bool(user) and verify_password(payload.password, user.get("password_hash", ""))

    await db.login_attempts.insert_one({
        "identifier": identifier,
        "email": email,
        "ip": ip,
        "ts": now.isoformat(),
        "success": ok,
    })

    if not ok:
        raise HTTPException(status_code=401, detail="Email o contrasena incorrectos")

    token = create_admin_token(email)
    return {"token": token, "email": email, "expires_in_hours": ADMIN_TOKEN_HOURS}


@router.get("/me")
async def admin_me(admin: dict = Depends(get_current_admin)):
    return {"email": admin["sub"], "role": admin["role"], "exp": admin["exp"]}


# ---- Budget requests -------------------------------------------------------

@router.get("/budget-requests")
async def admin_list_budget_requests(admin: dict = Depends(get_current_admin)):
    cursor = db.budget_requests.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    items = await cursor.to_list(500)
    unread = await db.budget_requests.count_documents({"read": {"$ne": True}})
    total = await db.budget_requests.count_documents({})
    return {"items": items, "unread": unread, "total": total}


@router.patch("/budget-requests/{request_id}")
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


@router.delete("/budget-requests/{request_id}")
async def admin_delete_budget_request(
    request_id: str,
    admin: dict = Depends(get_current_admin),
):
    res = await db.budget_requests.delete_one({"id": request_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return {"success": True}


# ---- Reviews moderation ----------------------------------------------------

@router.get("/reviews")
async def admin_list_reviews(admin: dict = Depends(get_current_admin)):
    cursor = db.reviews.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    items = await cursor.to_list(500)
    pending = await db.reviews.count_documents({"approved": False})
    return {"items": items, "pending": pending, "total": len(items)}


@router.patch("/reviews/{review_id}")
async def admin_moderate_review(
    review_id: str,
    payload: ReviewModerationRequest,
    admin: dict = Depends(get_current_admin),
):
    res = await db.reviews.update_one({"id": review_id}, {"$set": {"approved": payload.approved}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return {"success": True, "approved": payload.approved}


@router.delete("/reviews/{review_id}")
async def admin_delete_review(
    review_id: str,
    admin: dict = Depends(get_current_admin),
):
    res = await db.reviews.delete_one({"id": review_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada")
    return {"success": True}


# ---- Access links (gift/partner replay) -----------------------------------

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
    jti = decode_jti(token)

    email_status = "skipped"
    last_sent_at = None
    if send_email:
        ok = await send_email_bounded(
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


@router.post("/access-links")
async def admin_create_access_link(
    payload: AdminAccessLinkRequest,
    admin: dict = Depends(get_current_admin),
):
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


@router.get("/access-links")
async def admin_list_access_links(admin: dict = Depends(get_current_admin)):
    cursor = db.access_links.find({}, {"_id": 0}).sort("created_at", -1).limit(50)
    items = await cursor.to_list(50)
    return {"items": items, "total": len(items)}


@router.post("/access-links/{link_id}/resend")
async def admin_resend_access_link(
    link_id: str,
    admin: dict = Depends(get_current_admin),
):
    rec = await db.access_links.find_one({"id": link_id}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    if rec.get("revoked"):
        raise HTTPException(status_code=400, detail="No se puede reenviar un enlace revocado")

    ok = await send_email_bounded(
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


@router.post("/access-links/{link_id}/revoke")
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


@router.delete("/access-links/{link_id}")
async def admin_delete_access_link(
    link_id: str,
    admin: dict = Depends(get_current_admin),
):
    """Remove the link from history. Does NOT auto-revoke."""
    res = await db.access_links.delete_one({"id": link_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return {"success": True}


# ---- Sector CMS ------------------------------------------------------------

@router.get("/sectors")
async def admin_list_sectors(admin: dict = Depends(get_current_admin)):
    """Full list including hidden and soft-deleted sectors (for the CMS UI)."""
    cursor = db.sectors.find({}, {"_id": 0}).sort("created_at", 1)
    items = await cursor.to_list(200)
    active = [s for s in items if not s.get("hidden") and not s.get("deleted_at")]
    hidden = [s for s in items if s.get("hidden") and not s.get("deleted_at")]
    trash = [s for s in items if s.get("deleted_at")]
    return {"items": items, "active": len(active), "hidden": len(hidden), "trash": len(trash)}


@router.post("/sectors")
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


@router.patch("/sectors/{slug}")
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


@router.post("/sectors/{slug}/visibility")
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


@router.delete("/sectors/{slug}")
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


@router.post("/sectors/{slug}/restore")
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


@router.delete("/sectors/{slug}/permanent")
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
