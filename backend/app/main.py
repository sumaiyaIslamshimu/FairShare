"""FastAPI entry point. Each member adds ONLY their own router lines (final edit: Member 4)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.db.indexes import ensure_indexes
from app.db.mongo import get_db, ping_db
from app.routers import auth, categories , compare, seller_products



@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_indexes(get_db())
    yield


app = FastAPI(title="FairShare API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)


@app.get("/api/health", tags=["System"])
def health():
    up = ping_db()
    return {"status": "ok" if up else "degraded", "database": "up" if up else "down"}


# --- Member 1 routers ---
app.include_router(auth.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
# --- Member 2 routers ---
app.include_router(compare.router, prefix="/api")
app.include_router(seller_products.router, prefix="/api")
# --- Member 3 routers: (added in Member 3's phase) ---
from app.routers import seller_portal
app.include_router(seller_portal.router, prefix="/api")
# --- Member 3 routers: (added in Member 3's phase) ---
from app.routers import seller_portal, cart
app.include_router(seller_portal.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
# --- Member 4 routers: (added in Member 4's phase) ---