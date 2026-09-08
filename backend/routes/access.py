"""Access-token generation endpoints (public and internal admin)."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from catalogues import get_agent_info
from config import PUBLIC_BASE_URL, SERVICE_API_KEY
from models import AccessGenerateRequest
from security import build_agent_access_url, generate_access_token


router = APIRouter()


@router.post("/access/generate")
async def admin_generate_access(
    payload: AccessGenerateRequest,
    x_service_key: Optional[str] = Header(default=None, alias="X-Service-Key"),
):
    """Admin-only endpoint to generate a personal access link manually.

    Protected by SERVICE_API_KEY header.
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


@router.get("/access/preview-email")
async def admin_preview_email(
    request: Request,
    agent_id: str,
    level: str = "demo",
    customer_name: str = "Obdulio",
    x_service_key: Optional[str] = Header(default=None, alias="X-Service-Key"),
):
    """Render the welcome email HTML for QA without sending it."""
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
    preview = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Preview · {info['name']} · {info['level']}</title>
<style>body{{margin:0;font-family:system-ui;background:#0b1020;color:#e2e8f0}}
.meta{{background:#0f172a;color:#cbd5e1;padding:16px 22px;border-bottom:1px solid #1f2937;font-size:13px}}
.meta b{{color:#fff}}.meta span{{color:#94a3b8;margin-right:6px}}</style></head>
<body><div class="meta"><span>From:</span><b>PSICOLFIS.NET &lt;obdulio@psicolfis.net&gt;</b><br>
<span>To:</span><b>{customer_name} &lt;tu-email@ejemplo.com&gt;</b><br>
<span>Subject:</span><b>{subject}</b></div>{html}</body></html>"""
    return HTMLResponse(content=preview)
