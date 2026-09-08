# RECONSTRUCTION.md — Guía maestra de reconstrucción de PSICOLFIS.NET

> Documento de emergencia. Si perdieras acceso a Emergent, tuvieras que
> migrar a otro proveedor o simplemente clonar el entorno para
> desarrollo local, este archivo describe TODO lo necesario para tener
> `psicolfis.net` funcionando de nuevo.
>
> ⚠️ **Ningún secreto real está aquí**. Solo el nombre de cada variable
> y dónde obtenerla. Los valores reales viven en Emergent (Manage
> Secrets del deployment) o en tu bóveda personal (1Password, Bitwarden…).

## 1 · Stack

| Capa | Tecnología | Versión (aprox.) |
|---|---|---|
| Frontend | React 19 + CRA + Tailwind | ver `frontend/package.json` |
| Backend | FastAPI + Motor (async Mongo) + Uvicorn | ver `backend/requirements.txt` |
| Base de datos | MongoDB | 6.x |
| Pagos | Stripe (Payment Links + Webhook API) | live keys |
| Email transaccional | SMTP SSL propio | `psicolfis.net:465` |
| Agentes IA | Pickaxe (iframes embebidos) | – |
| CRM inmobiliario | proyecto Emergent independiente | preview URL |
| Deploy | Emergent Cloud | – |

## 2 · Estructura del repo

```
/
├── backend/            FastAPI monolítico (server.py principal)
│   ├── server.py       Endpoints, auth, Stripe webhook, sitemap, CMS sectores
│   ├── email_templates.py
│   ├── requirements.txt
│   ├── tests/          pytest — sitemap, admin sectors, regresión
│   └── .env.example    (usa este archivo como plantilla)
├── frontend/           React 19 SPA
│   ├── src/App.js      Monolito con Home + Agentes + Soluciones + Admin
│   ├── src/App.css
│   ├── public/         imágenes, videos comprimidos, robots.txt
│   ├── package.json
│   ├── yarn.lock       (crítico para reconstrucción exacta)
│   └── .env.example
├── memory/             Documentación del proyecto (PRD, CHANGELOG…)
├── tests/              pytest end-to-end (auth, security, SMTP, sectors)
├── .gitignore
└── RECONSTRUCTION.md   (este archivo)
```

## 3 · Requisitos previos para reconstruir

- **Cuentas de servicios**:
  - Stripe (live) — obtener `sk_live_...` y `whsec_...` del webhook
  - Pickaxe Studio — deployment IDs de los agentes IRIS/ALEX/UMBRAL
  - Dominio `psicolfis.net` con DNS accesible
  - Servidor SMTP (el actual: `psicolfis.net:465`, credenciales del panel de correo)
- **Software local si vas a desarrollar**:
  - Python 3.11+
  - Node.js 20+ y Yarn 1.x (`npm install -g yarn`)
  - MongoDB 6.x (local o remoto)
  - `ffmpeg` (para regenerar vídeos comprimidos si hace falta)

## 4 · Variables de entorno

Lista completa documentada en:
- `backend/.env.example`  → 30+ variables (Mongo, Stripe, JWT, admin, SMTP, Pickaxe…)
- `frontend/.env.example` → 12+ variables (backend URL, Stripe payment links, GA4, CRM URL…)

Copia ambos a `.env` en su directorio y rellena los valores.

## 5 · Pasos para clonar y arrancar

```bash
# 1. Clonar el repo
git clone https://github.com/obduliobailador-debug/psicolfisnet-08-09-2026.git
cd psicolfisnet-08-09-2026

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # editar con valores reales

# 3. Frontend
cd ../frontend
yarn install --frozen-lockfile  # usa yarn.lock para reproducir versiones exactas
cp .env.example .env  # editar

# 4. MongoDB local (o apunta al Atlas / remoto en .env)
mongod --dbpath /data/db &

# 5. Arrancar servicios
# Terminal 1
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload
# Terminal 2
cd frontend && yarn start
```

## 6 · Servicios externos a re-configurar

Después de tener la app corriendo, hay que enlazar:

1. **Stripe webhook** → Dashboard → Developers → Webhooks → Add
   endpoint apuntando a `https://<tu-dominio>/api/webhook/stripe`
   (evento `checkout.session.completed`). Guardar el signing secret
   en `STRIPE_WEBHOOK_SECRET`.
2. **Stripe Payment Links** → asegurarte de que cada link tiene metadata
   `agent_id` y `level` (script en `/backend/scripts/` si existe, o
   editar manualmente).
3. **Pickaxe** → en cada agente, permitir el dominio
   `psicolfis.net` en la lista de dominios embebibles.
4. **DNS** → apuntar A/AAAA de `psicolfis.net` al servidor de deploy.
5. **Google Search Console** → declarar sitemap
   `https://psicolfis.net/api/sitemap.xml`.
6. **Seed inicial**:
   - Los sectores (`sectors` collection) se auto-seedan en el startup
     desde `SECTOR_CATALOGUE` en `backend/server.py`.
   - El usuario admin (`admin_users` collection) se auto-seedea con
     `ADMIN_EMAIL` y `ADMIN_PASSWORD` del `.env`.
   - Las reviews demo también se auto-seedan si la colección está
     vacía.

## 7 · Tests de humo tras reconstrucción

```bash
# Backend health
curl https://<dominio>/api/

# Sitemap
curl https://<dominio>/api/sitemap.xml

# Sectores
curl https://<dominio>/api/sectors

# Admin login (debe devolver token)
curl -X POST https://<dominio>/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dominio","password":"..."}'
```

Y en el navegador:
- `/` — Home carga
- `/soluciones` — 4 tarjetas (3 sectores + "tu sector aquí")
- `/soluciones/inmobiliarias` — landing + CRM incluido
- `/admin` — login funciona
- `/mi-agente/<token-real>` — iframe Pickaxe embebido

## 8 · Contactos y accesos

- **Dominio**: gestionado en <proveedor DNS> (ej. Cloudflare/GVO)
- **Emergent**: cuenta obdulio@psicolfis.net
- **Stripe**: cuenta obdulio@psicolfis.net
- **Pickaxe**: cuenta obdulio@psicolfis.net
- **GitHub repo**: https://github.com/obduliobailador-debug/psicolfisnet-08-09-2026

## 9 · Backups recomendados (rutina)

- `mongodump` semanal de la BD → `psicolfis-YYYYMMDD.gz`
- Commit + tag en GitHub tras cada release grande
- Descargar tarball de configuración del panel Emergent (si existe)

## 10 · Rotación de secretos

Los siguientes secretos deberían rotarse cada 3-6 meses o ante cualquier
sospecha de fuga:

- `STRIPE_API_KEY` y `STRIPE_WEBHOOK_SECRET`
- `JWT_SECRET` (invalida enlaces `/mi-agente/*` existentes — asumible)
- `SERVICE_API_KEY`
- `ADMIN_PASSWORD` (más el bcrypt hash en `admin_users`)
- `CAPTCHA_SECRET` (invalida captchas activos, se regenera solo)
- `SMTP_PASSWORD`

## 11 · Notas históricas

- Este documento se crea como parte del commit **BACKUP
  PRE-RECONSTRUCCION PSICOLFIS 08-09-2026**.
- Ver `memory/PRD.md` para la historia detallada de cada sesión de
  desarrollo (10-18 hasta la fecha).
