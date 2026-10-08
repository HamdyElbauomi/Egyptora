"""FastAPI app: registers every router. Owner: Person 1 (shared — add your router here, nothing else)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (loads every table so foreign keys resolve)
from app.ai import chat_agent, nl2sql, place_qa, planner, recognizer, sentiment
from app.core.config import settings
from app.core.storage import URL_PREFIX, upload_root
from app.modules.accounts import router as accounts
from app.modules.admin_stats import router as admin_stats
from app.modules.ai_quality import router_admin as ai_quality_admin
from app.modules.catalog import router_admin as catalog_admin
from app.modules.chat import router as chat
from app.modules.companies import router_admin as companies_admin
from app.modules.companies import router_portal as companies_portal
from app.modules.companies import router_public as companies_public
from app.modules.hotels import router as hotels
from app.modules.hotels import router_admin as hotels_admin
from app.modules.offers import router_admin as offers_admin
from app.modules.offers import router_portal as offers_portal
from app.modules.offers import router_public as offers_public
from app.modules.places import router as places
from app.modules.places import router_admin as places_admin
from app.modules.sharing import router as sharing
from app.modules.trips import router as trips
from app.modules.trips import router_lookups as trips_lookups

API_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Egyptora backend. Each endpoint's description says why it exists and what it unlocks next.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTERS = [
    # Person 1
    accounts.router,
    companies_portal.router,
    companies_public.router,
    companies_admin.router,
    # Person 2
    trips_lookups.router,
    trips.router,
    # Person 3
    chat.router,
    sharing.router,
    admin_stats.router,
    catalog_admin.router,
    # Person 4
    places.router,
    places_admin.router,
    # Person 5 (hotels_admin and ai_quality before hotels, so /admin/... paths never clash)
    hotels_admin.router,
    ai_quality_admin.router,
    hotels.router,
    # Person 6
    offers_portal.router,
    offers_admin.router,
    offers_public.router,
]
for r in ROUTERS:
    app.include_router(r, prefix=API_PREFIX)

# Uploaded files (place photos, scans, documents) are served from here.
app.mount(URL_PREFIX, StaticFiles(directory=upload_root()), name="uploads")

if settings.expose_ai_routes:
    for ai in (sentiment, planner, chat_agent, recognizer, place_qa, nl2sql):
        app.include_router(ai.router, prefix=API_PREFIX)


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "ai_mock": settings.ai_mock}


def _mark_files_as_binary(node) -> None:
    """FastAPI describes uploads as `contentMediaType: application/octet-stream` (OpenAPI 3.1), which Swagger UI
    shows as a text box. `format: binary` makes Swagger show a real "Choose file" button, including for lists."""
    if isinstance(node, dict):
        if node.get("type") == "string" and node.get("contentMediaType") == "application/octet-stream":
            node.pop("contentMediaType")
            node["format"] = "binary"
        for value in node.values():
            _mark_files_as_binary(value)
    elif isinstance(node, list):
        for value in node:
            _mark_files_as_binary(value)


def custom_openapi() -> dict:
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        _mark_files_as_binary(schema)
        app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
