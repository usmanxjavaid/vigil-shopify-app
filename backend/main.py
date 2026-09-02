from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from config import settings
from logger import setup_logging, get_logger
from integrations.shopify_client import execute_graphql
from security.internal_auth import verify_internal_secret

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


TEST_ORDERS_QUERY = """
query TestOrders {
  orders(first: 5) {
    edges {
      node {
        id
        name
        displayFulfillmentStatus
        displayFinancialStatus
      }
    }
  }
}
"""


@app.get("/internal/test/orders", dependencies=[Depends(verify_internal_secret)])
async def test_orders():
    try:
        data = await execute_graphql(
            shop_domain=settings.test_shop_domain,
            access_token=settings.test_shopify_access_token,
            query=TEST_ORDERS_QUERY,
        )
    except RuntimeError as e:
        logger.error(f"Test orders call failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    return data