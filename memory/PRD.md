# PRD — PSICOLFIS.NET Landing

## Problema original
Mejorar la landing existente de PSICOLFIS.NET (clonada desde GitHub:
`obduliobailador-debug/Psicofis-actualizada-FINAL-4--9-01-2026`). Se mantiene
el diseño actual, y se aplican correcciones, integraciones y nuevas
funcionalidades sobre él.

## Arquitectura
- **Frontend**: React 19 + CRA/CRACO + Tailwind (componentes UI de Radix),
  rutas: `/`, `/agentes`, `/success`, `/cancel`, `/legal`.
- **Backend**: FastAPI + Motor (MongoDB) + SMTP SSL para envío de correos.
- **Pagos**: Enlaces directos de Stripe Payment Links (sin API de checkout
  server-side). Stripe gestiona toda la experiencia de pago y confirmaciones
  al cliente.
- **Email**: SMTP propio (`psicolfis.net:465` SSL, usuario
  `obdulio@psicolfis.net`) para entregar las solicitudes de presupuesto a la
  bandeja del propietario.

## Core requirements (estáticos)
1. Landing pública con los 3 agentes (IRIS, ALEX, UMBRAL) + popup promocional
   inicial.
2. Cada botón "Lo quiero" debe redirigir al enlace Stripe correspondiente:
   - IRIS: https://buy.stripe.com/cNicMY9Jf5NffL30aH7ok00
   - ALEX: https://buy.stripe.com/aFabIU2gN8ZraqJg9F7ok01
   - UMBRAL: https://buy.stripe.com/14A5kwbRnejL56paPl7ok02
3. Sección de precios con 3 planes (Starter, Professional, Enterprise) y
   botones "Solicitar Presupuesto" que abren un modal con formulario.
4. El formulario de presupuesto envía los datos por email a
   `obdulio@psicolfis.net` y persiste un registro en Mongo (`budget_requests`).
5. Secciones legales (Aviso Legal, Privacidad, Cookies) + banner de cookies.

## Lo implementado en esta sesión (2026-01-21)
- Importación del repo GitHub a `/app`, con preservación de `.env` del preview.
- Reducción del tamaño del nombre del agente sobre los vídeos del banner
  (32px → 22px) para que no desborde la tarjeta.
- `handlePurchase`/`handleBuyAgent` redirigen directamente a los enlaces
  Payment Link de Stripe (eliminada dependencia del endpoint de checkout
  propio, que queda dormante).
- Nuevo endpoint `POST /api/contact/budget` que:
  - Valida nombre/email/plan obligatorios.
  - Envía un correo HTML formateado a `obdulio@psicolfis.net` con `Reply-To`
    apuntando al email del cliente.
  - Guarda el registro en la colección `budget_requests`.
- Frontend del formulario con estados `Enviando...`, éxito y error visibles.
- Configuración SMTP completa (servidor, puerto 465 SSL, usuario,
  contraseña, FROM) cargada desde `.env`.

## Pendientes / Backlog
- **P1** Añadir reCAPTCHA o honeypot al formulario para frenar spam.
- **P1** Integrar una página de administración protegida para ver las
  solicitudes almacenadas en `budget_requests`.
- **P2** Optimización de rendimiento:
  - Vídeos `agent*.mp4` (compresión y `preload="metadata"`).
  - Lazy-load de secciones por debajo del fold.
  - Imágenes servidas con `loading="lazy"` y `srcset`.
- **P2** Accesibilidad: mejorar contraste en botones secundarios y estados
  de foco del formulario.
- **P2** Internacionalización (ES/EN) si se quiere expansión.
- **P3** Sustituir emojis decorativos por iconografía SVG consistente.

## Enhancement sugerido
Añadir un pequeño incentivo de conversión en la sección de precios:
un campo opcional "¿Cuándo te gustaría empezar?" con opciones (Esta semana /
Este mes / Explorando opciones) en el formulario de presupuesto. Esto te
permite priorizar los leads más calientes en tu bandeja de entrada.
