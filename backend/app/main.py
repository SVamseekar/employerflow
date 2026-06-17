import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.routers import applications, auth, billing, employers, shortlist

settings = get_settings()
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "static"))
ASSET_VERSION = os.environ.get("ASSET_VERSION", "ui5")
NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    import threading
    from sqlalchemy import text

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_granted BOOLEAN DEFAULT FALSE"
        ))

    def _seed():
        from app.startup import maybe_seed
        maybe_seed()

    threading.Thread(target=_seed, daemon=True).start()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(employers.router)
app.include_router(shortlist.router)
app.include_router(applications.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/")
def landing():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"), headers=NO_CACHE)


@app.get("/app.html")
def app_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.html"), headers=NO_CACHE)


if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")