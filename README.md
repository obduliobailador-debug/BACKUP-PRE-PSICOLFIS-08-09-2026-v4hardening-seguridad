# PSICOLFIS.NET — Landing con Agentes de IA

Landing profesional con integración de pagos (Stripe Payment Links),
formularios con envío por email, captcha HMAC stateless, sistema de
reseñas con rich-snippets para Google, WhatsApp privado, SEO
optimizado y animaciones al hacer scroll.

## 🚀 Stack

- **Frontend**: React 19 (CRA + CRACO), Tailwind, Radix UI.
- **Backend**: FastAPI + Motor (MongoDB async) + SMTP SSL.
- **Base de datos**: MongoDB.
- **Despliegue**: Emergent Platform.

## 📂 Estructura

```
/app
├── backend/              # FastAPI + MongoDB
│   ├── server.py         # Endpoints: /captcha, /contact/budget,
│   │                     #            /reviews, /whatsapp redirect, ...
│   ├── requirements.txt
│   └── .env.example      # Plantilla de variables de entorno
├── frontend/             # React SPA
│   ├── src/
│   │   ├── App.js        # Componentes Home, AgentesPage,
│   │   │                 # SuccessPage, CancelPage, LegalPage
│   │   └── App.css       # Todos los estilos
│   └── public/
│       ├── index.html    # SEO + JSON-LD + meta tags
│       ├── robots.txt
│       ├── sitemap.xml
│       └── videos/       # Vídeos verticales de los agentes
└── memory/
    ├── PRD.md            # Estado completo del producto
    └── test_credentials.md  (excluido del git)
```

## 🔧 Configuración

1. Copia los ejemplos de variables de entorno:
   ```
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. Rellena los valores reales en `backend/.env`:
   - `SMTP_PASSWORD` — contraseña del correo obdulio@psicolfis.net
   - `MONGO_URL` y `DB_NAME` si es distinto del local
   - (opcional) `WHATSAPP_NUMBER`, `WHATSAPP_DEFAULT_TEXT`, `CAPTCHA_SECRET`

3. Instala dependencias:
   ```
   cd backend && pip install -r requirements.txt
   cd ../frontend && yarn install
   ```

4. Arranca los servicios (en Emergent ya vienen gestionados por
   supervisor).

## ✨ Funcionalidades principales

### Público
- Landing con popup inicial y 3 agentes (IRIS / ALEX / UMBRAL)
- Pagos directos vía Stripe Payment Links
- Formulario de presupuesto con email a `obdulio@psicolfis.net`
- Reseñas con rating y formulario público
- WhatsApp con número **no expuesto** en el HTML
- FAQ, precios, cookies, legal

### SEO
- `<html lang="es">`, title/description/canonical dinámicos por ruta
- Open Graph + Twitter Cards
- **4 bloques JSON-LD**: Organization, FAQPage, Products, WebSite
- **AggregateRating** dinámico generado desde las reseñas reales
- robots.txt + sitemap.xml
- Noindex en rutas transitorias (/success, /cancel)
- Alt texts descriptivos, `loading="lazy"`, `<noscript>` fallback

### Seguridad
- Captcha HMAC SHA-256 stateless (sin DB) con TTL 10 min
- Honeypot invisible contra bots
- SMTP SSL (puerto 465)
- Pagos delegados a Stripe (PCI-DSS compliance externo)

## 📄 Endpoints API

| Método | Ruta | Descripción |
|:-:|---|---|
| GET | /api/whatsapp | 302 redirect a WhatsApp |
| GET | /api/captcha | Challenge matemático firmado |
| POST | /api/contact/budget | Solicitud de presupuesto |
| GET | /api/reviews | Lista reseñas + rating medio |
| POST | /api/reviews | Crear nueva reseña |
| GET | /api/ | Health check |

## 📝 Licencia

Código privado para PSICOLFIS, S.L.
