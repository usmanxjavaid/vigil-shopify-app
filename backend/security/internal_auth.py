from fastapi import Header, HTTPException

from config import settings


async def verify_internal_secret(x_internal_secret: str = Header(...)) -> None:
    """
    FastAPI dependency guarding every route only admin-ui should ever call.
    Compares the caller's X-Internal-Secret header against our own secret.
    Raises 401 on anything missing or mismatched — this header is the
    entire trust boundary between the public-facing Node service and
    this one, so there's no partial-credit here.
    """
    if x_internal_secret != settings.internal_api_secret:
        raise HTTPException(status_code=401, detail="Invalid internal secret")