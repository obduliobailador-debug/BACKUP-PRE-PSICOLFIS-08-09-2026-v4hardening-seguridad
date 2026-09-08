"""Static catalogues: agents (Pickaxe deployments) and initial B2B sectors.

The sector catalogue here is only used as the seed for MongoDB. Once seeded,
the CMS in the admin panel becomes the source of truth. Editing this list has
no effect on already-seeded sectors.
"""
from __future__ import annotations

import os
from typing import Dict, Optional


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


def public_sector(s: dict, *, include_deployment: bool = False) -> dict:
    """Serialize a sector for the public API (optionally with deployment id)."""
    out = {k: v for k, v in s.items() if k not in ("deployment_env", "_id", "deployment_id", "hidden", "deleted_at", "created_at", "updated_at")}
    if include_deployment:
        stored = s.get("deployment_id", "") if isinstance(s, dict) else ""
        env_val = os.environ.get(s.get("deployment_env", ""), "") if s.get("deployment_env") else ""
        out["deployment_id"] = stored or env_val or ""
    return out
