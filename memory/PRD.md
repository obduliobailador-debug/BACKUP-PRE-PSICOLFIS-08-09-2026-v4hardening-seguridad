# PRD — PSICOLFIS.NET Landing (versión final pre-deploy)

## 1. Problema original
Mejorar la landing de PSICOLFIS.NET (clonada desde GitHub:
`obduliobailador-debug/Psicofis-actualizada-FINAL-4--9-01-2026`).
Se mantiene el diseño y estructura original, añadiendo correcciones de
bugs, nuevas funcionalidades, integraciones, ajustes visuales y SEO
optimizado para Google.

## 2. Arquitectura
- **Frontend**: React 19 + CRA/CRACO + Tailwind + Radix UI.
  Rutas: `/`, `/agentes`, `/success`, `/cancel`, `/legal`.
- **Backend**: FastAPI + Motor (MongoDB async) + SMTP SSL.
- **Pagos**: Payment Links directos de Stripe (sin API de checkout
  server-side). IRIS / ALEX / UMBRAL van cada uno a su URL de Stripe.
- **Email**: SMTP propio `psicolfis.net:465 (SSL)`, usuario
  `obdulio@psicolfis.net` — envía formularios de presupuesto y notifica
  reseñas nuevas.
- **Base de datos**: MongoDB (collections `budget_requests`, `reviews`).

## 3. Personas / Audiencia
- Autónomos y pequeños negocios en España que buscan automatizar
  tareas repetitivas con IA (atención al cliente, redacción, leads).
- Perfiles secundarios: fisioterapeutas, coaches, consultores,
  academias online, clínicas.

## 4. Core requirements (estáticos)
1. Landing pública con los 3 agentes (IRIS, ALEX, UMBRAL) y popup
   promocional inicial con temporizador.
2. Botones "Lo quiero" redirigen a Payment Links de Stripe:
   - IRIS: https://buy.stripe.com/cNicMY9Jf5NffL30aH7ok00
   - ALEX: https://buy.stripe.com/aFabIU2gN8ZraqJg9F7ok01
   - UMBRAL: https://buy.stripe.com/14A5kwbRnejL56paPl7ok02
3. Aviso "Oferta limitada · solo demostración real" en cada 50€.
4. Sección de precios con 3 planes (Starter, Professional, Enterprise)
   y botones "Solicitar Presupuesto" que abren modal con formulario.
5. Formulario de presupuesto con:
   - Campos obligatorios: nombre, email, plan, captcha.
   - Campos opcionales: teléfono, agente de interés, mensaje libre.
   - Validación server-side + captcha HMAC + honeypot anti-spam.
   - Envío por email a `obdulio@psicolfis.net` + persistencia en Mongo.
6. Módulo de reseñas con:
   - Sección pública "Lo que dicen nuestros clientes" con grid de
     testimonios + rating global (estrellas doradas).
   - Formulario "Dejar mi reseña" con captcha + honeypot.
   - JSON-LD `AggregateRating` dinámico (SEO → rich snippets con
     estrellas en Google).
   - Seed inicial con 4 reseñas realistas.
7. Botón WhatsApp (verde) junto a "Contactar ahora" en FAQ; número
   oculto del source HTML vía redirect backend `/api/whatsapp`.
8. Navegación: enlaces anchor a secciones + "Empezar Ahora" + "Ponte
   en contacto" (abre formulario).
9. Secciones legales (Aviso Legal, Privacidad, Cookies) + banner
   cookies + rutas `/success`, `/cancel`, `/legal`.

## 5. Lo implementado (por sesiones, con fechas 2026-01-21)
### Sesión 1 — Importación y setup
- Clonado del repo GitHub e importado a `/app`, preservando `.env`.
- Dependencias instaladas (yarn + pip).
- Configuración SMTP (servidor, puerto 465 SSL, usuario, contraseña).

### Sesión 2 — Formularios y Stripe
- Botones de compra redirigen a Payment Links de Stripe.
- Endpoint `POST /api/contact/budget` con validación, email HTML
  formateado (Reply-To al cliente) y persistencia en Mongo.
- Estados "Enviando..." / éxito / error visibles en formulario.

### Sesión 3 — Ajustes visuales iteración 1
- Nombre del agente sobre los vídeos reducido de 32px → 18px.
- Botón "Ponte en contacto" en navbar (azul/violeta).
- FAQ "Contactar ahora" (antes `mailto:`) ahora abre el formulario.

### Sesión 4 — Formulario enriquecido + Captcha
- Desplegable de agente (Sin preferencia / IRIS / ALEX / UMBRAL / Varios).
- Textarea amplia "¿En qué proyecto podemos ayudarte?".
- Captcha matemático (suma 1-9) firmado con HMAC SHA-256, TTL 10 min,
  stateless (sin DB).
- Honeypot silencioso (`website`).

### Sesión 5 — WhatsApp + Animaciones
- Botón WhatsApp (verde oficial, icono SVG) junto a FAQ contact.
- Número de teléfono **oculto del HTML source** vía `GET /api/whatsapp`
  que emite 302 redirect a `wa.me/34670716305?text=...`.
- Hook `useScrollReveal` con IntersectionObserver aplicado a 19
  elementos (títulos, tarjetas, comparativas).
- Respeto `prefers-reduced-motion` para accesibilidad.

### Sesión 6 — SEO Fase 1 (completa)
- `<html lang="es">`, title/description optimizados, Open Graph,
  Twitter Cards, canonical `https://psicolfis.net/`.
- `robots.txt` + `sitemap.xml` en `/frontend/public/`.
- 4 bloques JSON-LD estáticos: Organization, FAQPage (12 preguntas),
  3 Products, WebSite.
- Hook `usePageSeo` para title/description/canonical/robots dinámicos
  por ruta. `/success` y `/cancel` llevan `noindex`.
- Alt texts descriptivos + `width`/`height` + `loading="lazy"` en
  imágenes bajo el fold.
- `<noscript>` con contenido mínimo para crawlers sin JS.

### Sesión 7 — Reseñas + AggregateRating
- Modelos `Review` en backend con validación (min 20 chars, captcha).
- Endpoints `GET /api/reviews` (sin exponer emails) y `POST /api/reviews`.
- Seed automático con 4 reseñas starter al primer arranque.
- Sección frontend "Lo que dicen nuestros clientes" con:
  - Resumen global con estrellas + rating promedio + total.
  - Grid responsive de tarjetas (⭐ + cita + autor + rol).
  - Modal "Dejar mi reseña" con rating 1-5 interactivo.
- JSON-LD `AggregateRating` inyectado dinámicamente en `<head>`.
- Enlace "Reseñas" añadido a la navbar.

### Sesión 8 — Detalles finales
- Copyright del footer dinámico: `{new Date().getFullYear()}`.
- Badge Emergent → enlace de afiliado
  `https://app.emergent.sh/register?ref=obdu291682`.

### Sesión 9 — Banner modal: ajustes de tipografía/vídeo
- Textos del banner reducidos: título 48→32px, subtitle 24→16px,
  tagline 22→15px. Padding del overlay reducido.
- Vídeos de agentes: cambio `object-fit: cover` → `contain` y altura
  300→420px para que se vea completo (sin recortes) el vídeo
  vertical 1304×1588 incluyendo el texto azul embedido.

## 6. Ficheros clave
- `/app/backend/server.py` — FastAPI con todos los endpoints.
- `/app/backend/.env` — MONGO_URL, DB_NAME, STRIPE, SMTP.
- `/app/backend/requirements.txt` — dependencias Python.
- `/app/frontend/src/App.js` — React SPA completo.
- `/app/frontend/src/App.css` — todos los estilos.
- `/app/frontend/public/index.html` — SEO + JSON-LD + badge.
- `/app/frontend/public/robots.txt`, `sitemap.xml`.
- `/app/frontend/public/videos/*.mp4` — 4 vídeos agentes (no tocar).

## 7. Endpoints backend
| Método | Ruta | Descripción |
|:-:|---|---|
| GET | /api/ | Health check |
| GET | /api/whatsapp | 302 redirect a WhatsApp (oculta número) |
| GET | /api/captcha | Devuelve challenge HMAC firmado |
| POST | /api/contact/budget | Recibe formulario, valida captcha, envía email |
| GET | /api/reviews | Lista reseñas aprobadas con rating global |
| POST | /api/reviews | Crea reseña con validación + captcha |
| POST | /api/checkout/session | (Legacy, no usado en frontend actual) |
| GET | /api/checkout/status/{id} | (Legacy) |
| POST | /api/webhook/stripe | (Legacy) |
| GET | /api/agent/{id}/data | Datos públicos por agente |

## 8. Variables de entorno (backend/.env)
- MONGO_URL, DB_NAME
- STRIPE_API_KEY (no usada con Payment Links, puede quedar vacía)
- SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
- WHATSAPP_NUMBER (opcional; default 34670716305)
- WHATSAPP_DEFAULT_TEXT (opcional)
- CAPTCHA_SECRET (opcional; se regenera si falta)

## 9. Pendientes / Backlog
### P0 — Deploy y dominio (SIGUIENTE ACCIÓN DEL USUARIO)
- [ ] Save to GitHub (backup del código actualizado)
- [ ] Pulsar Deploy en Emergent (~50 créditos/mes)
- [ ] Usar "Link domain → Entri" para conectar `psicolfis.net`
- [ ] Configurar registros A/CNAME en panel DNS de GVO
  (dejando intactos MX/SPF/DKIM del correo)
- [ ] Enviar sitemap a Search Console tras indexarse el dominio

### P1 — Mejoras de producto
- [ ] Panel admin protegido (`/admin`) para ver solicitudes y
  moderar reseñas sin tocar DB.
- [ ] Compresión de vídeos `*_sonriendo.mp4` y `preload="metadata"`.
- [ ] Imágenes en `.webp` / `.avif` para LCP.
- [ ] Versión en inglés (i18n) si se internacionaliza.

### P2 — Extras
- [ ] Botón flotante WhatsApp en todas las páginas.
- [ ] Integración con Google Analytics 4.
- [ ] Blog / contenido SEO (marketing de atracción).

## 10. Enhancement sugerido
Añadir un campo opcional "¿Cuándo te gustaría empezar?" (Esta semana /
Este mes / Explorando) al formulario de presupuesto. Permite priorizar
los leads más calientes en la bandeja de entrada.
