"""SMTP helpers: bounded async wrapper, purchase email, budget request email.

All blocking SMTP calls should be routed through `send_email_bounded` to
prevent slow mail servers from blocking the event loop or holding an HTTP
request open for minutes.
"""
from __future__ import annotations

import asyncio
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    PUBLIC_BASE_URL,
    SMTP_FROM,
    SMTP_HARD_TIMEOUT,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USER,
    logger,
)
from security import build_agent_access_url, generate_access_token


async def send_email_bounded(fn, /, **kwargs) -> bool:
    """Run a blocking SMTP helper in a worker thread with a hard wall-clock cap.

    Falls back to `False` on TimeoutError or any exception so the caller can
    persist `email_sent=false` and surface a graceful UX message.
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


def send_purchase_email(
    customer_email: str,
    customer_name: str,
    agent_name: str,
    agent_id: str,
    level: str = "full",
) -> bool:
    """Send confirmation email after a successful purchase, with signed JWT link."""
    try:
        from email_templates import render_email

        token = generate_access_token(
            customer_email=customer_email,
            agent_id=agent_id,
            level=level,
            customer_name=customer_name,
        )
        agent_url = build_agent_access_url(token)

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

        message.attach(MIMEText(text, "plain", "utf-8"))
        message.attach(MIMEText(html, "html", "utf-8"))

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
