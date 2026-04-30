# PRD — PSICOLFIS.NET

## 1. Problema original
Mejorar la landing de PSICOLFIS.NET (clonada del repo
`obduliobailador-debug/Psicofis-actualizada-FINAL-4--9-01-2026`) y
construir un **ecosistema cerrado**: tras un pago en Stripe, el cliente
recibe un email con un enlace único que abre el agente IA (Pickaxe)
embebido dentro del propio dominio `psicolfis.net`, sin redirecciones a
terceros. El admin (Obdulio) gestiona todo desde un back-office en
`/admin`: solicitudes de presupuesto, reseñas y la posibilidad de
**regalar accesos** manualmente (saltándose Stripe).

## 2. Arquitectura
- **Frontend**: React 19 + CRA/CRACO + Tailwind + Radix UI.
  Rutas: `/`, `/agentes`, `/success`, `/cancel`, `/legal`,
  `/mi-agente/:token` y `/admin`.
- **Backend**: FastAPI + Motor (Mongo async) + SMTP SSL + Stripe + JWT
  (PyJWT) + bcrypt.
- **Pagos**:
  - Payment Links de Stripe (IRIS/ALEX/UMBRAL) con `metadata`
    (`agent_id`, `level`) configurada vía API.
  - Webhook `POST /api/webhook/stripe` (firma verificada) que tras
    `checkout.session.completed` envía email con el enlace único.
- **Acceso a agentes**: JWT firmado con `JWT_SECRET`; el cliente entra
  por `/mi-agente/:token` y la SPA llama a `/api/access/validate` para
  obtener el `deployment_id` de Pickaxe y embeber el iframe.
- **Revocación**: colección `revoked_tokens` (denylist por `jti`).
- **Email**: SMTP propio `psicolfis.net:465 (SSL)` con plantillas
  dinámicas por agente (`/app/backend/email_templates.py`) e imágenes
  extraídas de los vídeos.
- **Base de datos**: MongoDB con colecciones `budget_requests`,
  `reviews`, `payment_transactions`, `admin_users`, `login_attempts`,
  `access_links`, `revoked_tokens`.
- **i18n**: Widget de Google Translate (22 idiomas, incluido Rumano)
  en el header (oculto en `/admin`).

## 3. Personas / Audiencia
- Autónomos y pequeños negocios en España que buscan automatizar
  tareas con IA (atención al cliente, redacción, leads).
- Perfiles secundarios: fisioterapeutas, coaches, consultores,
  academias online, clínicas estéticas.

## 4. Core requirements
1. Landing pública con los 3 agentes (IRIS, ALEX, UMBRAL).
2. Botones "Lo quiero" → Payment Links de Stripe.
3. Formulario de presupuesto + captcha HMAC + honeypot.
4. Reseñas + AggregateRating JSON-LD + moderación.
5. Tras pagar: email automático con enlace JWT a `/mi-agente/:token`
   donde el agente Pickaxe está embebido (sin salir del dominio).
6. **Panel admin `/admin`** con:
   - Login (bcrypt + lockout tras 5 intentos en 15 min).
   - Solicitudes de presupuesto (ver / marcar leída / eliminar /
     responder por mailto).
   - Reseñas (aprobar / despublicar / eliminar).
   - **Regalar acceso**: formulario para generar enlace manual,
     enviar email automáticamente, ver historial, copiar enlace,
     reenviar email, revocar (denylist) y eliminar del historial.
7. SEO: title/description/canonical, Open Graph, JSON-LD, sitemap,
   robots, alt texts, AggregateRating.
8. Botón WhatsApp con número oculto (redirect backend).
9. Traductor Google con 22 idiomas.

## 5. Lo implementado (fechas relevantes)
### Sesiones 1-9 (enero 2026)
Importación, formularios, Stripe Payment Links, captcha, WhatsApp,
animaciones, SEO Fase 1, reseñas, JSON-LD AggregateRating, ajustes
visuales, badge Emergent, contenido legal.

### Sesión 10-11 (feb 2026) — Universo Psicolfis.net
- Webhook Stripe firmado con `STRIPE_WEBHOOK_SECRET`, lectura de
  `metadata.agent_id` y `metadata.level` desde Payment Links.
- Generación de JWT firmado con expiración configurable.
- Ruta SPA `/mi-agente/:token` con iframe Pickaxe protegido.
- Plantillas de email dinámicas + Widget Google Translate (22 idiomas).

### Sesión 12 (feb 2026) — Panel Admin Fase 1
- Backend: bcrypt + PyJWT + admin_users + login_attempts (rate-limit).
- Frontend: `/admin` con login y 2 tabs (Presupuestos + Reseñas).

### Sesión 13 (feb 2026) — Regalar acceso
- 5 endpoints `/api/admin/access-links*` con denylist `revoked_tokens`.
- Frontend: 3ª pestaña "Regalar acceso" con formulario, historial,
  acciones (Copiar / Reenviar / Revocar / Eliminar).

### Sesión 14 (feb 2026) — Soluciones por sector (B2B verticales)
- Backend: `SECTOR_CATALOGUE` con 3 verticales (inmobiliarias,
  clinicas-dentales, salones-belleza). Endpoints públicos:
  - `GET /api/sectors` — listado (sin deployment_id).
  - `GET /api/sectors/{slug}` — detalle (con deployment_id si existe).
- Variables `.env`: `PICKAXE_DEPLOYMENT_SECTOR_INMOBILIARIAS`,
  `_DENTAL`, `_BEAUTY` (vacías hasta que se creen los agentes en
  Pickaxe; mientras, la página muestra placeholder "Demo próximamente").
- Frontend:
  - Nuevo enlace **"Soluciones"** en navbar Home.
  - Sección destacada en Home (`#soluciones`) con 3 tarjetas y CTA
    "Ver todas las soluciones por sector".
  - `/soluciones` — index público con grid de los 3 sectores.
  - `/soluciones/:slug` — landing detallada por sector con:
    hero + métricas + problema/solución + casos de uso + demo en
    vivo Pickaxe (o placeholder) + CTAs duales (Solicitar demo +
    WhatsApp directo) + final CTA.
  - El CTA "Solicitar demo" navega a `/?demo=<Sector>` y el Home
    abre automáticamente el modal de presupuesto con el plan
    `Demo personalizada · <Sector>` autorrellenado.
  - El CTA WhatsApp abre `/api/whatsapp?text=` con un mensaje
    contextual al sector.
- Tests: 15/15 pytest pasados + verificación E2E completa.

## 6. Ficheros clave
- `/app/backend/server.py` — FastAPI con todos los endpoints.
- `/app/backend/email_templates.py` — Plantillas HTML por agente.
- `/app/backend/.env` — Mongo, SMTP, Stripe, JWT, ADMIN, PICKAXE.
- `/app/frontend/src/App.js` — SPA monolítica
  (Home + Agentes + Success/Cancel + Legal + MiAgente + Admin).
- `/app/frontend/src/App.css` — Estilos completos.
- `/app/tests/test_admin_access_links.py` — Suite pytest.

## 7. Endpoints backend (resumen)
| Método | Ruta | Descripción |
|:-:|---|---|
| GET | /api/whatsapp | Redirect 302 oculto |
| GET | /api/captcha | Challenge HMAC |
| POST | /api/contact/budget | Formulario + email |
| GET/POST | /api/reviews | Listar/crear |
| POST | /api/checkout/session | (Legacy) |
| POST | /api/webhook/stripe | Webhook firmado |
| GET | /api/access/validate | Valida JWT + denylist |
| POST | /api/access/generate | Legacy (service-key) |
| POST | /api/admin/login | bcrypt + JWT 8h |
| GET | /api/admin/me | Sesion actual |
| GET/PATCH/DELETE | /api/admin/budget-requests | Back-office |
| GET/PATCH/DELETE | /api/admin/reviews | Moderar |
| POST/GET | /api/admin/access-links | Crear/listar |
| POST | /api/admin/access-links/{id}/resend | Reenviar email |
| POST | /api/admin/access-links/{id}/revoke | Revocar |
| DELETE | /api/admin/access-links/{id} | Borrar del historial |

## 8. Variables de entorno (backend/.env)
- MONGO_URL, DB_NAME
- STRIPE_API_KEY (Live), STRIPE_WEBHOOK_SECRET
- SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
- WHATSAPP_NUMBER, WHATSAPP_DEFAULT_TEXT
- CAPTCHA_SECRET (opcional)
- JWT_SECRET, ACCESS_TOKEN_DAYS (por defecto 365)
- PUBLIC_BASE_URL (`https://psicolfis.net`)
- ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_TOKEN_HOURS=8
- SERVICE_API_KEY (legacy)
- PICKAXE_DEPLOYMENT_IRIS / _ALEX / _UMBRAL [_DEMO]
- STRIPE_FULL_URL_IRIS / _ALEX / _UMBRAL (upsell desde demo)

## 9. Pendientes / Backlog

### P0 — Próxima acción del usuario
- [ ] **Crear los 3 agentes de Pickaxe** para los nuevos sectores
      (Inmobiliarias / Clínicas dentales / Salones de belleza) y
      añadir sus deployment IDs a `/app/backend/.env`:
      - `PICKAXE_DEPLOYMENT_SECTOR_INMOBILIARIAS`
      - `PICKAXE_DEPLOYMENT_SECTOR_DENTAL`
      - `PICKAXE_DEPLOYMENT_SECTOR_BEAUTY`
      Mientras estén vacíos, las páginas muestran un placeholder
      "Demo próximamente" (totalmente válido para lanzar).
- [ ] **Redeploy a producción** desde Emergent — todas las novedades
      (Stripe webhook, panel admin completo, "Regalar acceso",
      Soluciones por sector) están solo en preview hasta el deploy.
- [ ] Tras redeploy: probar 1 compra demo real y un primer "regalo"
      desde el panel admin.

### P1 — Mejoras técnicas
- [ ] Refactor: dividir `/app/backend/server.py` (~1700 líneas) en
      routers (`admin/`, `access/`, `payments/`, `sectors/`).
- [ ] Refactor: dividir `/app/frontend/src/App.js` (~3000 líneas) en
      `pages/` y `components/`.
- [ ] Compresión de vídeos `*_sonriendo.mp4` y `preload="metadata"`.
- [ ] Imágenes en `.webp` / `.avif` para LCP (Core Web Vitals).
- [ ] Convertir CTAs WhatsApp en `<a href target=_blank>` (mejora
      accesibilidad y middle-click).

### P2 — Extras
- [ ] Botón flotante WhatsApp en todas las páginas.
- [ ] Google Analytics 4.
- [ ] Blog / contenido SEO por sector.
- [ ] Versión en inglés (i18n).
- [ ] Más sectores: gimnasios, fisios, restaurantes, asesorías.
- [ ] Editor del catálogo de sectores desde el panel admin (Mongo).

## 10. Enhancement sugerido
En el panel admin, añadir un pequeño contador "Conversiones del mes"
sobre los 3 agentes (cuántos pagos confirmados por agente en los
últimos 30 días) usando `payment_transactions`. Permite a Obdulio ver
de un vistazo qué agente vende mejor sin entrar en Stripe.
