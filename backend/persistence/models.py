import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Plain text for now. Real encryption-at-rest is a Phase 8 security-pass
    # task per the TAD — not implemented yet, flagging so it isn't forgotten.
    access_token: Mapped[str] = mapped_column(String(255))
    scope: Mapped[str] = mapped_column(String(255))
    installed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    uninstalled_at: Mapped[datetime | None] = mapped_column(default=None)


class ShopSettings(Base):
    __tablename__ = "settings"

    # shop_id IS the primary key here, not a separate id column — this
    # table is genuinely one-to-one with shops, so a redundant extra id
    # would just be noise. Every other table below gets its own id since
    # they're genuinely one-to-many.
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), primary_key=True)
    threshold_hours: Mapped[int] = mapped_column(default=72)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class FlagStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED_APPROVED = "edited_approved"
    DISMISSED = "dismissed"
    SENT = "sent"


class FlaggedOrder(Base):
    __tablename__ = "flagged_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), index=True)
    shopify_order_id: Mapped[str] = mapped_column(String(64))
    order_number: Mapped[str] = mapped_column(String(64))
    customer_email: Mapped[str] = mapped_column(String(255))
    # Numeric/Decimal, never Float, for money — floats can't represent
    # 19.99 exactly and silently accumulate rounding errors over time.
    order_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    flagged_at: Mapped[datetime] = mapped_column(server_default=func.now())
    threshold_crossed_at: Mapped[datetime]
    priority_score: Mapped[int]
    ai_explanation: Mapped[str] = mapped_column(String)
    ai_draft_message: Mapped[str] = mapped_column(String)
    # Plain string, not a native Postgres ENUM type — Postgres enums are
    # genuinely painful to alter later (adding one new status needs a
    # special migration). A string column plus the Python enum above for
    # validation in code is the lower-friction, more common real-world choice.
    status: Mapped[str] = mapped_column(String(32), default=FlagStatus.PENDING.value)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
    resolved_by: Mapped[str | None] = mapped_column(String(255), default=None)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), index=True)
    flagged_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("flagged_orders.id"), default=None
    )
    event_type: Mapped[str] = mapped_column(String(64))
    event_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shops.id"), index=True)
    # Unique, so a duplicate delivery (Shopify does retry webhooks) can be
    # caught as a constraint violation instead of silently double-processing.
    shopify_webhook_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    topic: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())