from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.db import get_db
from persistence.models import Shop, ShopSettings
from security.internal_auth import verify_internal_secret
from logger import get_logger

router = APIRouter(prefix="/internal/shops", dependencies=[Depends(verify_internal_secret)])
logger = get_logger(__name__)


class ShopSyncRequest(BaseModel):
    shop_domain: str
    access_token: str
    scope: str


@router.post("/sync")
async def sync_shop(payload: ShopSyncRequest, db: AsyncSession = Depends(get_db)):
    """
    Upserts a shop's current token every time Node authenticates an
    embedded page load — not just once at install. This is the "keep
    the token warm" design from the TAD: as long as a merchant opens
    the app periodically, this table never goes stale, without needing
    a separate refresh mechanism.
    """
    result = await db.execute(select(Shop).where(Shop.shop_domain == payload.shop_domain))
    shop = result.scalar_one_or_none()

    if shop is None:
        shop = Shop(
            shop_domain=payload.shop_domain,
            access_token=payload.access_token,
            scope=payload.scope,
        )
        db.add(shop)
        await db.flush()  # populates shop.id before we reference it below

        # New shop -> give it default settings immediately, same moment
        # it's created, so nothing downstream ever has to handle "shop
        # exists but has no settings row yet" as a special case.
        db.add(ShopSettings(shop_id=shop.id))
        logger.info(f"New shop installed: {payload.shop_domain}")
    else:
        shop.access_token = payload.access_token
        shop.scope = payload.scope
        shop.uninstalled_at = None  # reinstall after a prior uninstall
        logger.info(f"Refreshed token for existing shop: {payload.shop_domain}")

    await db.commit()
    return {"status": "synced", "shop_domain": payload.shop_domain}