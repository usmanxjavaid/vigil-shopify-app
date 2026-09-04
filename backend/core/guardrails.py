from datetime import datetime, timezone


def is_stuck_order(
    financial_status: str,
    fulfillment_status: str,
    order_created_at: datetime,
    threshold_hours: int,
    now: datetime | None = None,
) -> bool:
    """
    The v1 base rule from the PRD: paid, not yet fulfilled, and past the
    shop's configured threshold. Nothing about priority or explanation
    lives here — this function answers exactly one yes/no question,
    on purpose, so it stays trivially testable.

    `now` is an injectable parameter rather than always using
    datetime.now() internally — this is what makes the function testable
    without needing to fake the system clock; tests can just pass a fixed
    `now` and get a deterministic result every time.
    """
    if financial_status != "paid":
        return False

    if fulfillment_status in ("fulfilled", "partial"):
        return False

    current_time = now or datetime.now(timezone.utc)
    hours_since_order = (current_time - order_created_at).total_seconds() / 3600

    return hours_since_order >= threshold_hours