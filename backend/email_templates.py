"""Email templates per agent and access level.

Each template is intentionally written in Obdulio's voice (direct, action-driven,
short sentences, "no te quedes mirando, úsalo"). Visual layout follows the
psicolfis.net brand: blue/violet gradient header, white content card, large CTA
button, and a small secondary upsell link only on the demo variants.

Public API: render_email(agent_id, level, *, customer_name, access_url, full_url)
returns (subject, plain_text, html).
"""

from typing import Optional

# ---- Layout primitives shared across all emails ------------------------------

_BASE_STYLES = """
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1f2937; background: #f3f4f6; margin: 0; padding: 0; }
  .wrap { max-width: 620px; margin: 0 auto; padding: 24px 16px; }
  .card { background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 8px 28px rgba(15, 23, 42, 0.08); }
  .header { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: #ffffff; padding: 30px 28px; }
  .header .brand { font-size: 12px; letter-spacing: 0.18em; opacity: 0.85; text-transform: uppercase; }
  .header h1 { margin: 8px 0 0; font-size: 24px; line-height: 1.25; font-weight: 800; }
  .header .agent-tag { display: inline-block; margin-top: 14px; padding: 6px 14px; border-radius: 999px; background: rgba(255,255,255,0.18); font-weight: 700; letter-spacing: 0.06em; font-size: 13px; }
  .body { padding: 30px 28px 12px; color: #1f2937; font-size: 15.5px; }
  .body p { margin: 0 0 14px; }
  .body .lead { font-weight: 500; color: #0f172a; }
  .arrow { color: #3b82f6; font-weight: 700; margin-right: 4px; }
  .cta-wrap { text-align: center; margin: 28px 0 18px; }
  .cta-btn { display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: #ffffff !important; text-decoration: none; padding: 16px 28px; border-radius: 12px; font-weight: 800; font-size: 16px; letter-spacing: 0.02em; box-shadow: 0 8px 22px rgba(59, 130, 246, 0.32); }
  .cta-hint { text-align: center; font-size: 12px; color: #64748b; margin: 0 0 22px; }
  .upsell { margin-top: 18px; padding: 18px 18px; border: 1px dashed rgba(245, 158, 11, 0.55); background: #fffbeb; border-radius: 12px; text-align: center; }
  .upsell-title { font-weight: 800; color: #92400e; font-size: 14px; margin: 0 0 8px; }
  .upsell-link { display: inline-block; color: #b45309 !important; text-decoration: none; border-bottom: 2px solid #f59e0b; font-weight: 700; padding-bottom: 1px; font-size: 14px; }
  .pd { background: #f1f5f9; border-left: 4px solid #8b5cf6; padding: 14px 16px; border-radius: 8px; margin: 22px 0 8px; color: #334155; font-size: 14.5px; }
  .pd strong { color: #1e293b; }
  .signature { margin: 22px 0 4px; font-size: 15px; }
  .signature .name { font-weight: 700; color: #0f172a; }
  .footer { padding: 22px 28px 28px; color: #94a3b8; font-size: 12.5px; text-align: center; }
  .footer .brand { color: #475569; font-weight: 700; letter-spacing: 0.08em; }
  .footer a { color: #64748b; text-decoration: none; }
"""


def _shell(header_title: str, agent_name: str, level_label: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>{_BASE_STYLES}</style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="header">
        <div class="brand">Universo PSICOLFIS.NET</div>
        <h1>{header_title}</h1>
        <span class="agent-tag">{agent_name} · {level_label}</span>
      </div>
      <div class="body">
        {body_html}
      </div>
      <div class="footer">
        <p class="brand">PSICOLFIS.NET</p>
        <p>Tu sabiduría. Nuestra IA. Resultados en acción.</p>
        <p>
          <a href="mailto:obdulio@psicolfis.net">obdulio@psicolfis.net</a> &nbsp;·&nbsp;
          <a href="https://psicolfis.net">psicolfis.net</a>
        </p>
      </div>
    </div>
  </div>
</body>
</html>"""


def _cta(access_url: str, label: str) -> str:
    return f"""
<div class="cta-wrap">
  <a href="{access_url}" class="cta-btn">{label}</a>
</div>
<p class="cta-hint">Enlace personal e intransferible. Te lleva directo a tu agente dentro de psicolfis.net.</p>
"""


def _upsell(full_url: str, agent_name: str) -> str:
    if not full_url:
        return ""
    return f"""
<div class="upsell">
  <p class="upsell-title">¿Sin ganas de límites? Quita el freno.</p>
  <a href="{full_url}" class="upsell-link">Activar Acceso Total a {agent_name} →</a>
</div>
"""


# ---- Per-agent demo content (Obdulio's voice, untouched) --------------------

_DEMO_BODIES = {
    "iris": {
        "subject": "Empieza a usarlo… y verás lo que cambia",
        "header": "Empieza a usarlo… y verás lo que cambia",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Gracias por dar este paso.</p>
<p>Ya tienes acceso a la <strong>demo de IRIS</strong>.</p>
<p>Y te digo algo importante desde ya:<br>no te quedes mirando… <strong>úsalo</strong>.</p>
<p>Escribe. Prueba. Juega con ello.</p>
<p>Porque IRIS no está pensada para que la entiendas…<br><span class="arrow">›</span>está pensada para que la <strong>sientas funcionando</strong>.</p>
<p>En cuanto empieces a usarla, te vas a dar cuenta de algo:</p>
<p><span class="arrow">›</span>Puedes generar contenido sin bloquearte<br><span class="arrow">›</span>Puedes avanzar sin tener que pensarlo todo<br><span class="arrow">›</span>Puedes estar visible sin agotarte</p>
<p>Eso es lo que hay aquí.</p>
<p>La demo tiene un uso limitado, suficiente para que lo compruebes por ti mismo… <strong>pero no para que te quedes ahí</strong>.</p>
<p>Y es normal.</p>
<p>Porque cuando veas lo que hace contigo,<br>vas a querer usarlo <strong>sin freno</strong>.</p>
{cta}
{upsell}
<div class="pd"><strong>PD:</strong> Si en algún momento notas que "se te queda corto"… no es casualidad. Significa que ya has entendido el potencial.</div>
<p class="signature">Pruébalo de verdad.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "alex": {
        "subject": "Aquí es donde empiezas a recuperar tiempo",
        "header": "Aquí empiezas a recuperar tiempo",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes acceso a la <strong>demo de ALEX</strong>.</p>
<p>Y aquí no hay teoría.</p>
<p><span class="arrow">›</span>Aquí vienes a <strong>quitarte trabajo de encima</strong>.</p>
<p>Empieza a usarlo y observa:</p>
<p><span class="arrow">›</span>cómo responde,<br><span class="arrow">›</span>cómo organiza,<br><span class="arrow">›</span>cómo te quita carga mental sin darte cuenta.</p>
<p>Porque eso es lo importante.</p>
<p>No es solo lo que hace…<br>es lo que <strong>te libera</strong>.</p>
<p>La demo te deja probarlo en situaciones reales, pero con un límite. Lo justo para que lo veas claro.</p>
<p>Y cuando lo veas claro… vas a entender que <strong>hacerlo todo tú ya no tiene sentido</strong>.</p>
{cta}
{upsell}
<div class="pd"><strong>PD:</strong> Si notas que empiezas a depender de él… vas por buen camino.</div>
<p class="signature">Sin filtros.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "umbral": {
        "subject": "Aquí empieza el cambio (si lo usas de verdad)",
        "header": "Aquí empieza el cambio (si lo usas de verdad)",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes acceso a la <strong>demo de UMBRAL</strong>.</p>
<p>Y te voy a ser muy claro:</p>
<p><span class="arrow">›</span><strong>esto no sirve si no lo usas de verdad</strong>.</p>
<p>UMBRAL está diseñado para algo muy concreto:</p>
<p><span class="arrow">›</span>ayudarte a ver con claridad lo que antes era ruido<br><span class="arrow">›</span>ordenar lo que tienes dentro<br><span class="arrow">›</span>tomar decisiones con más sentido</p>
<p>Pero eso no se entiende leyendo… <strong>se entiende usándolo</strong>.</p>
<p>Además, hay algo importante:</p>
<p>UMBRAL tiene un enfoque especialmente cuidado y humano, y está afinado para acompañar también a personas del entorno LGTBI+, donde muchas veces esa claridad no es tan fácil de encontrar fuera.</p>
<p><strong>Sin etiquetas. Sin juicio. Solo claridad.</strong></p>
<p>La demo tiene un límite, sí. Pero es más que suficiente para que te des cuenta de algo:</p>
<p><span class="arrow">›</span>o sigues como hasta ahora…<br><span class="arrow">›</span>o empiezas a ver las cosas de otra manera.</p>
{cta}
{upsell}
<div class="pd"><strong>PD:</strong> Si algo encaja dentro mientras lo usas… no lo ignores.</div>
<p class="signature">Y pruébalo en serio.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
}


# ---- Per-agent FULL content (placeholder until Obdulio sends final texts) ----

_FULL_BODIES = {
    "iris": {
        "subject": "Bienvenido. Ya no hay límite con IRIS.",
        "header": "Sin límite. Ahora es cuando.",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes <strong>acceso total a IRIS</strong>.</p>
<p>Sin freno, sin contadores, sin "espera al siguiente mensaje".</p>
<p>Solo tú e IRIS, las veces que quieras, el tiempo que necesites.</p>
<p>Úsala como tu compañera real:</p>
<p><span class="arrow">›</span>cuando quieras pensar mejor algo importante<br><span class="arrow">›</span>cuando necesites generar sin bloquearte<br><span class="arrow">›</span>cuando lo tengas todo en la cabeza y no sepas por dónde tirar</p>
<p>IRIS está aquí para acompañarte. Lo demás, lo construyes tú.</p>
{cta}
<div class="pd"><strong>PD:</strong> Si algo te encanta, mejora tu vida o quieres más, escríbenos. Estamos al otro lado del email.</div>
<p class="signature">Bienvenido al Universo PSICOLFIS.NET.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "alex": {
        "subject": "Bienvenido. ALEX ya es tuyo, sin límite.",
        "header": "Tu tiempo, recuperado.",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes <strong>acceso total a ALEX</strong>.</p>
<p>Esto cambia el juego.</p>
<p>Ya no es probar a ver qué tal. Es <strong>delegar de verdad</strong>.</p>
<p>Empieza a usarlo cada día:</p>
<p><span class="arrow">›</span>para decidir más rápido<br><span class="arrow">›</span>para ordenar lo que tienes pendiente<br><span class="arrow">›</span>para quitarte ruido y avanzar con claridad</p>
<p>El cambio no se ve en una semana. Se ve en cómo terminas la jornada.</p>
{cta}
<div class="pd"><strong>PD:</strong> Si echas algo en falta o quieres ajustar el tono, dímelo. ALEX se afina contigo.</div>
<p class="signature">Recupera tu tiempo.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "umbral": {
        "subject": "Bienvenido a UMBRAL, sin límite.",
        "header": "Sin etiquetas. Sin juicio. Sin límite.",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes <strong>acceso total a UMBRAL</strong>.</p>
<p>Aquí no hay prisa, no hay contador, no hay nadie mirando.</p>
<p>Solo un espacio para ti, para pensar con claridad lo que antes era ruido.</p>
<p>Úsalo:</p>
<p><span class="arrow">›</span>cuando algo se mueve dentro y necesitas ordenarlo<br><span class="arrow">›</span>cuando una decisión te pesa más de lo que quieres reconocer<br><span class="arrow">›</span>cuando quieras hablar de lo que normalmente no se habla</p>
<p>UMBRAL no decide por ti. <strong>Te ayuda a verlo más claro</strong>.</p>
{cta}
<div class="pd"><strong>PD:</strong> Si algo encaja, no lo ignores. Y si algo no encaja, escríbeme. Aquí seguimos puliendo UMBRAL contigo.</div>
<p class="signature">Bienvenido a casa.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
}


def _strip_html(html: str) -> str:
    """Very small HTML→plain converter for the text/plain MIME part."""
    import re
    text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common entities
    text = (text.replace('&nbsp;', ' ')
                .replace('&amp;', '&')
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&quot;', '"'))
    # Collapse blank lines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


def render_email(
    agent_id: str,
    level: str,
    *,
    customer_name: str,
    access_url: str,
    full_url: Optional[str] = None,
):
    """Build (subject, plain_text, html) for a given agent_id and level.

    Falls back to a generic template if agent_id is unknown.
    """
    agent_id = (agent_id or "").lower()
    level = (level or "full").lower()
    agent_name = {"iris": "IRIS", "alex": "ALEX", "umbral": "UMBRAL"}.get(agent_id, agent_id.upper() or "Agente")
    level_label = "Acceso completo" if level == "full" else "Versión demo"

    pool = _FULL_BODIES if level == "full" else _DEMO_BODIES
    tpl = pool.get(agent_id)

    if tpl is None:
        # Generic fallback (should never trigger if Stripe metadata is right)
        subject = f"Tu Agente {agent_name} ya está listo"
        body_html = (
            f'<p class="lead">Hola {customer_name},</p>'
            f'<p>Ya tienes acceso a tu Agente <strong>{agent_name}</strong> ({level_label}).</p>'
            f'{{cta}}'
            f'<p class="signature">Bienvenido al Universo PSICOLFIS.NET.<br><span class="name">Obdulio Bailador</span></p>'
        )
        header_title = f"Tu Agente {agent_name} está listo"
    else:
        subject = tpl["subject"]
        body_html = tpl["body"]
        header_title = tpl["header"]

    cta_label = f"Acceder a mi Agente {agent_name} →"
    cta_block = _cta(access_url, cta_label)
    upsell_block = _upsell(full_url, agent_name) if (level == "demo") else ""

    body_html = body_html.format(
        customer_name=customer_name or "amigo",
        cta=cta_block,
        upsell=upsell_block,
    )

    html = _shell(header_title, agent_name, level_label, body_html)

    # Plain text fallback derived from the rendered HTML body
    plain = _strip_html(body_html)
    plain += (
        "\n\n---\nPSICOLFIS.NET — Tu sabiduría. Nuestra IA. Resultados en acción."
        "\nobdulio@psicolfis.net | psicolfis.net"
    )

    return subject, plain, html
