import httpx

from config import settings
from logger import get_logger

logger = get_logger(__name__)

GRAPHQL_ENDPOINT_TEMPLATE = "https://{shop_domain}/admin/api/{version}/graphql.json"


async def execute_graphql(
    shop_domain: str, access_token: str, query: str, variables: dict | None = None
) -> dict:
    """
    Sends one GraphQL request to a shop's Admin API and returns the parsed
    `data` payload. Raises RuntimeError on transport failure or a non-empty
    `errors` array — callers get one clear failure mode instead of having
    to separately check HTTP status and inspect the body themselves.
    """
    url = GRAPHQL_ENDPOINT_TEMPLATE.format(
        shop_domain=shop_domain, version=settings.shopify_api_version
    )
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json",
    }
    payload = {"query": query, "variables": variables or {}}

    logger.info(f"Using token ending in: ...{access_token[-6:]} (length: {len(access_token)})")

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        logger.error(f"Shopify GraphQL HTTP {response.status_code}: {response.text}")
        raise RuntimeError(f"Shopify API returned HTTP {response.status_code}")

    body = response.json()

    if "errors" in body:
        logger.error(f"Shopify GraphQL errors: {body['errors']}")
        raise RuntimeError(f"Shopify GraphQL returned errors: {body['errors']}")

    return body["data"]