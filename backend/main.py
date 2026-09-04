from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings  # noqa: F401
from logger import setup_logging, get_logger
from api import shops

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Vigil backend starting up")
    yield
    logger.info("Vigil backend shutting down")


app = FastAPI(title="Vigil Backend", version="0.1.0", lifespan=lifespan)

app.include_router(shops.router)


@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "ok", "service": "vigil-backend"}