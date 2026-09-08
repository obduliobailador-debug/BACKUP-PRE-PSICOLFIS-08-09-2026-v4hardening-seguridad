"""Psicolfis API entrypoint.

Thin bootstrap: wires the config, mounts the modular routers under `/api`,
adds CORS, and runs seed/index tasks on startup. All business logic lives in
`routes/` and the helper modules (`security.py`, `email_service.py`, etc.).
"""
from __future__ import annotations

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, client, logger
from routes.access import router as access_router
from routes.admin import router as admin_router
from routes.payments import router as payments_router
from routes.public import _dynamic_sitemap_response, router as public_router
from seed import (
    ensure_indexes,
    seed_admin_if_needed,
    seed_reviews_if_empty,
    seed_sectors_if_empty,
)

app = FastAPI()

# All modular routers share the /api prefix
api_router = APIRouter(prefix="/api")
api_router.include_router(public_router)
api_router.include_router(access_router)
api_router.include_router(admin_router)
api_router.include_router(payments_router)

app.include_router(api_router)


# The sitemap must also be reachable at the SPA root path so it's declared in
# robots.txt. Note: on Kubernetes the ingress only forwards /api/*, so in
# production it's the /api/sitemap.xml one that browsers actually reach.
@app.get("/sitemap.xml")
async def sitemap_root():
    return await _dynamic_sitemap_response()


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Service-Key", "Stripe-Signature"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await seed_admin_if_needed()
    except Exception as e:
        logger.error(f"Admin seed error: {e}")
    try:
        await seed_reviews_if_empty()
    except Exception as e:
        logger.error(f"Seed error: {e}")
    try:
        await seed_sectors_if_empty()
    except Exception as e:
        logger.error(f"Sector seed error: {e}")
    await ensure_indexes()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
