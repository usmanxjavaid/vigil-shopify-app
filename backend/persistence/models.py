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
    access_token: Mapped[str] = mapped_column(String(255))
    scope: Mapped[str] = mapped_column(String(255))
    installed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    uninstalled_at: Mapped[datetime | None] = mapped_column(default=None)


class ShopSettings(Base):
    __tablename__ = "settings"

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
    order_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    flagged_at: Mapped[datetime] = mapped_column(server_default=func.now())
    threshold_crossed_at: Mapped[datetime]
    priority_score: Mapped[int]
    # Nullable now — Phase 4 (detection) writes the row the instant it's
    # flagged, with these still empty and status=pending. Phase 5
    # (reasoning) fills them in afterward. Keeps a slow/failed LLM call
    # from ever blocking or losing a real detection.
    ai_explanation: Mapped[str | None] = mapped_column(String, default=None)
    ai_draft_message: Mapped[str | None] = mapped_column(String, default=None)
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
    shopify_webhook_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    topic: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(server_default=func.now())