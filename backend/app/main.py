from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

# Google's token response uses short scope aliases (e.g. "email", "profile") instead of
# the full URLs we request (userinfo.email, userinfo.profile). oauthlib treats this as a
# scope change and raises Warning, crashing the callback with a 500. This env var suppresses
# that check. Must be set before any google-auth-oauthlib imports are used.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from app.database import engine, Base
import app.models  # noqa: F401 — ensure ORM models are registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start scheduler
    from app.scheduler import scheduler
    scheduler.start()

    yield

    # Shutdown scheduler
    scheduler.shutdown()


app = FastAPI(title="YouTube Analytics API", lifespan=lifespan)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


from app.routers import auth, dashboard

app.include_router(auth.router)
app.include_router(dashboard.router, prefix="/api")

# Dev-only: manually trigger the snapshot job
if os.getenv("ENV", "development") == "development":
    from fastapi import BackgroundTasks

    @app.get("/admin/run-snapshot", tags=["admin"])
    async def run_snapshot(background_tasks: BackgroundTasks):
        from app.scheduler import daily_snapshot_job
        background_tasks.add_task(daily_snapshot_job)
        return {"message": "Snapshot job queued"}
