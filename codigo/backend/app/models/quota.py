from datetime import datetime, timezone
from sqlalchemy import String, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.types import UTCDateTime


class QuotaGrant(Base):
    __tablename__ = "quota_grants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    provider: Mapped[str] = mapped_column(String(40), index=True)
    period: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(300))
    amount: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ProviderObservation(Base):
    __tablename__ = "provider_observations"
    provider: Mapped[str] = mapped_column(String(40), primary_key=True)
    scope: Mapped[str] = mapped_column(String(100), primary_key=True, default="account")
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(UTCDateTime(timezone=True), nullable=True)
    status: Mapped[int] = mapped_column(Integer)
    blocked_until: Mapped[datetime | None] = mapped_column(UTCDateTime(timezone=True), nullable=True)
    dimensions: Mapped[list] = mapped_column(JSON, default=list)
