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
  .header { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); color: #ffffff; padding: 26px 28px; }
  .header table { width: 100%; border-collapse: collapse; }
  .header td.photo-cell { width: 96px; padding-right: 18px; vertical-align: middle; }
  .header td.text-cell { vertical-align: middle; }
  .header .photo { display: block; width: 88px; height: 88px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255,255,255,0.55); box-shadow: 0 6px 18px rgba(0,0,0,0.18); }
  .header .brand { font-size: 12px; letter-spacing: 0.18em; opacity: 0.85; text-transform: uppercase; }
  .header h1 { margin: 6px 0 0; font-size: 22px; line-height: 1.25; font-weight: 800; }
  .header .agent-tag { display: inline-block; margin-top: 12px; padding: 5px 12px; border-radius: 999px; background: rgba(255,255,255,0.18); font-weight: 700; letter-spacing: 0.06em; font-size: 12.5px; }
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


def _shell(header_title: str, agent_name: str, agent_id: str, level_label: str, body_html: str, photo_base_url: str) -> str:
    photo_url = f"{photo_base_url.rstrip('/')}/api/agents/{agent_id.lower()}/photo"
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
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td class="photo-cell">
              <img class="photo" src="{photo_url}" alt="{agent_name}" width="88" height="88" />
            </td>
            <td class="text-cell">
              <div class="brand">Universo PSICOLFIS.NET</div>
              <h1>{header_title}</h1>
              <span class="agent-tag">{agent_name} · {level_label}</span>
            </td>
          </tr>
        </table>
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


# ---- Per-agent FULL content -------------------------------------------------

_FULL_BODIES = {
    "iris": {
        "subject": "Ahora sí… sin límites",
        "header": "Ahora sí… sin límites",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Perfecto.</p>
<p>Ya tienes <strong>IRIS activa al completo</strong>.</p>
<p>Ahora cambia todo.</p>
<p>Porque ya no hay cortes,<br>no hay límites…<br>y no tienes que medir lo que haces.</p>
<p><strong>Mi recomendación:</strong></p>
<p><span class="arrow">›</span><strong>intégrala en tu día a día desde ya</strong>.</p>
<p>Para crear contenido,<br>para pensar ideas,<br>para avanzar sin bloquearte.</p>
<p>Cuanto más la uses, más natural te va a resultar.</p>
<p>Y en poco tiempo te darás cuenta de algo:</p>
<p><span class="arrow">›</span>lo que antes te costaba horas… <strong>ahora fluye</strong>.</p>
<p>Eso es exactamente lo que buscabas.</p>
{cta}
<p class="signature">Ahora sí, úsala de verdad.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "alex": {
        "subject": "Empieza a trabajar distinto desde hoy",
        "header": "Empieza a trabajar distinto desde hoy",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes <strong>ALEX funcionando sin límites</strong>.</p>
<p>Y aquí es donde empieza el cambio real.</p>
<p>Porque ya no se trata de probar…<br><span class="arrow">›</span><strong>se trata de apoyarte en él de verdad</strong>.</p>
<p>Empieza poco a poco:</p>
<p>delegando tareas,<br>probando respuestas,<br>dejando que te quite carga.</p>
<p>Y observa.</p>
<p>Porque en cuanto lo integres en tu rutina, vas a notar algo muy claro:</p>
<p><span class="arrow">›</span>tienes más tiempo<br><span class="arrow">›</span>más foco<br><span class="arrow">›</span>menos saturación</p>
<p>Eso no es teoría. <strong>Es uso</strong>.</p>
{cta}
<p class="signature">Empieza hoy mismo.<br><span class="name">Obdulio Bailador</span></p>
""",
    },
    "umbral": {
        "subject": "Ahora sí… con claridad de verdad",
        "header": "Ahora sí… con claridad de verdad",
        "body": """
<p class="lead">Hola {customer_name},</p>
<p>Ya tienes <strong>UMBRAL activo sin limitaciones</strong>.</p>
<p>Y eso cambia las reglas.</p>
<p>Porque ahora ya no estás probando…<br><span class="arrow">›</span>ahora puedes usarlo <strong>de verdad</strong>, sin frenos y sin quedarte a medias.</p>
<p>UMBRAL está para algo muy concreto:</p>
<p><span class="arrow">›</span>ayudarte a ver con claridad<br><span class="arrow">›</span>ordenar lo que antes era ruido<br><span class="arrow">›</span>tomar decisiones con más sentido</p>
<p>Y eso, cuando lo empiezas a usar en tu día a día… <strong>se nota</strong>.</p>
<p>Más foco.<br>Más calma.<br>Menos dudas innecesarias.</p>
<p>Además, hay algo que forma parte de su esencia:</p>
<p>UMBRAL está diseñado desde un enfoque profundamente humano, y con una sensibilidad especial hacia personas del entorno LGTBI+, donde muchas veces encontrar claridad real no es tan sencillo fuera.</p>
<p><strong>Sin etiquetas. Sin presión. Solo un espacio donde pensar mejor.</strong></p>
<p>Ahora mi recomendación es simple:</p>
<p><span class="arrow">›</span>úsalo en situaciones reales<br><span class="arrow">›</span>no lo dejes como algo puntual<br><span class="arrow">›</span>intégralo en tu forma de decidir</p>
<p>Porque ahí es donde marca la diferencia.</p>
<p>Y lo vas a notar.</p>
{cta}
<div class="pd"><strong>PD:</strong> Si empiezas a ver cosas que antes no veías… no es casualidad. Es que estás usando bien la herramienta.</div>
<p class="signature"><span class="name">Obdulio Bailador</span></p>
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
    photo_base_url: str = "https://psicolfis.net",
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

    # Fallback when Stripe doesn't send a customer name: use a warm greeting
    # ("Hola, qué bueno que estés aquí,") instead of an awkward placeholder.
    cust = (customer_name or "").strip()
    if cust:
        greeting_value = f" {cust}"
    else:
        greeting_value = ", qué bueno que estés aquí"

    body_html = body_html.replace(
        "<p class=\"lead\">Hola {customer_name},</p>",
        f"<p class=\"lead\">Hola{greeting_value},</p>",
    )

    body_html = body_html.format(
        customer_name=cust,
        cta=cta_block,
        upsell=upsell_block,
    )

    html = _shell(header_title, agent_name, agent_id, level_label, body_html, photo_base_url)

    # Plain text fallback derived from the rendered HTML body
    plain = _strip_html(body_html)
    plain += (
        "\n\n---\nPSICOLFIS.NET — Tu sabiduría. Nuestra IA. Resultados en acción."
        "\nobdulio@psicolfis.net | psicolfis.net"
    )

    return subject, plain, html
