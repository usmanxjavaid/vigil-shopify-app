from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings  # noqa: F401 — runs Settings() on import, so a
                              # missing/invalid .env fails loudly here at
                              # startup, not three files deep later.
from logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Vigil backend starting up")
    yield
    logger.info("Vigil backend shutting down")


app = FastAPI(title="Vigil Backend", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok", "service": "vigil-backend"}


# Phase 3 adds real routers here, e.g.:
# from api import flags, shops
# app.include_router(flags.router)