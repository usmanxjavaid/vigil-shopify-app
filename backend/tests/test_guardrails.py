from datetime import datetime, timedelta, timezone

from core.guardrails import is_stuck_order

FIXED_NOW = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)
THRESHOLD = 72


def hours_ago(hours: float) -> datetime:
    return FIXED_NOW - timedelta(hours=hours)


def test_flags_paid_unfulfilled_past_threshold():
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="unfulfilled",
        order_created_at=hours_ago(73),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is True


def test_does_not_flag_one_hour_under_threshold():
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="unfulfilled",
        order_created_at=hours_ago(71),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is False


def test_flags_exactly_at_threshold():
    # Boundary case: 72.0 hours exactly should flag, since the rule is
    # >=, not >. Worth a dedicated test — off-by-one at the boundary is
    # exactly the kind of bug that's invisible until it silently isn't.
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="unfulfilled",
        order_created_at=hours_ago(72),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is True


def test_does_not_flag_unpaid_order():
    result = is_stuck_order(
        financial_status="pending",
        fulfillment_status="unfulfilled",
        order_created_at=hours_ago(100),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is False


def test_does_not_flag_fulfilled_order():
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="fulfilled",
        order_created_at=hours_ago(100),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is False


def test_does_not_flag_partially_fulfilled_order():
    # Per the PRD: partial fulfillment counts as "already being handled,"
    # not stuck — same reasoning Velvora used for its refund guardrails.
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="partial",
        order_created_at=hours_ago(100),
        threshold_hours=THRESHOLD,
        now=FIXED_NOW,
    )
    assert result is False


def test_respects_per_shop_threshold():
    # Same order age, different shop-configured threshold — confirms the
    # function actually uses the passed-in threshold rather than a
    # hardcoded number.
    result = is_stuck_order(
        financial_status="paid",
        fulfillment_status="unfulfilled",
        order_created_at=hours_ago(30),
        threshold_hours=24,
        now=FIXED_NOW,
    )
    assert result is True