# Guía — Conectar el CRM a `crm.psicolfis.net`

> Objetivo: que el CRM (hoy en `https://git-import-helper.emergent.host/`)
> sea accesible desde `https://crm.psicolfis.net` sin tocar su código.
> El CRM sigue siendo un proyecto Emergent independiente; solo cambiamos
> cómo se llega a él.

## Resumen (3 pasos)

1. En el **proyecto Emergent del CRM** → añadir `crm.psicolfis.net` como
   dominio custom (Emergent te dará un valor DNS).
2. En **Cloudflare / GVO** (donde tienes el DNS de psicolfis.net) →
   crear un registro CNAME con ese valor.
3. Esperar 5–30 min a que propague, verificar con el navegador, y
   avisarme para actualizar la URL del botón "Probar el CRM en vivo".

---

## Paso 1 · Emergent (proyecto CRM)

1. Entra en https://app.emergent.sh y abre el proyecto del CRM
   inmobiliario.
2. Busca la sección **"Domains"** / **"Link domain"** / **"Custom
   domain"** (está en el mismo sitio donde vinculaste `psicolfis.net`
   al proyecto principal).
3. Escribe el subdominio: `crm.psicolfis.net`.
4. Emergent te mostrará un valor de DNS para configurar. Suele ser
   algo como:
   - **Tipo**: `CNAME`
   - **Host / Nombre**: `crm`
   - **Valor / Destino**: `algo.emergent-deploy.com` (te lo dará
     Emergent; cópialo EXACTAMENTE).
5. Deja la pantalla de Emergent abierta — lo más probable es que
   aparezca "Pending verification" hasta que el DNS propague.

## Paso 2 · Cloudflare (o panel DNS de GVO)

Si tienes el dominio en **Cloudflare**:

1. Entra en el dashboard de Cloudflare → dominio `psicolfis.net` →
   **DNS** → **Records**.
2. Pulsa **Add record**.
3. Rellena:
   - **Type**: `CNAME`
   - **Name**: `crm`  *(NO pongas `crm.psicolfis.net`, solo `crm`)*
   - **Target**: el valor que te dio Emergent en el paso 1.4.
   - **Proxy status**: deja en **"DNS only"** (nube gris). Más
     sencillo. Si prefieres la nube naranja (proxy), también vale
     pero asegúrate de tener SSL a `Full (strict)` en Cloudflare.
   - **TTL**: Auto.
4. Save.

Si tienes el DNS en **GVO** (panel clásico):

1. Panel de DNS → Zona `psicolfis.net` → Añadir registro.
2. Mismo: `CNAME` + host `crm` + destino el valor de Emergent.
3. Guardar.

> ⚠️ **Muy importante**: NO toques los registros `A`, `MX`, `TXT` de
> `psicolfis.net`. Solo añadimos un nuevo registro; no editamos ni
> borramos nada.

## Paso 3 · Verificar

1. Espera 5–30 minutos (a veces basta 2 min, otras tarda más).
2. Abre en una pestaña nueva: https://crm.psicolfis.net
3. Deberías ver el CRM funcionando **con candado verde** (SSL ok) y la
   URL `crm.psicolfis.net` en la barra.
4. Vuelve a Emergent → la pantalla de "Link domain" debería mostrar
   "Verified" / "Active".
5. Avísame ("ya está activo crm.psicolfis.net") y yo actualizo en
   30 segundos la variable `REACT_APP_CRM_DEMO_URL_INMOBILIARIAS` en
   `/app/frontend/.env` — así el botón "Probar el CRM en vivo" pasará
   a abrir `crm.psicolfis.net` y nunca más `git-import-helper.emergent.host`.

## Paso 4 (futuro, opcional) · Migración real

Cuando quieras hacer la Opción 3 (fusionar el CRM dentro del mismo
código de `psicolfis.net`), podemos reservar una sesión dedicada.
Necesitaré acceso al código del CRM (via GitHub o export) y calcular
impacto en el sistema de auth (hay dos: el del admin de psicolfis
y el del CRM — habría que unificarlos o aislarlos por rol).

## Checklist rápido

- [ ] Emergent (CRM) → Link domain `crm.psicolfis.net`
- [ ] DNS (Cloudflare/GVO) → CNAME `crm` → valor de Emergent
- [ ] Propagación OK → abre `https://crm.psicolfis.net` con SSL verde
- [ ] Avisar a Obdulio → agente → cambiar `.env` y redeploy
