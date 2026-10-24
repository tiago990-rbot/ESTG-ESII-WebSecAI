from app.db.types import UTCDateTime as DateTime
from datetime import datetime, timezone
from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def now():
    return datetime.now(timezone.utc)

class Investigation(Base):
    __tablename__ = "investigations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    target: Mapped[str] = mapped_column(String(2000))
    domain: Mapped[str] = mapped_column(String(253), default="")
    kind: Mapped[str] = mapped_column(String(20), default="domain")
    organization: Mapped[str] = mapped_column(String(150), default="")
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    is_demo: Mapped[bool] = mapped_column(default=False)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    technical: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    message_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    runs: Mapped[list["ProviderRun"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    evidence: Mapped[list["Evidence"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    reports: Mapped[list["AIReport"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

class ProviderRun(Base):
    __tablename__ = "provider_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text, default="")
    results_count: Mapped[int] = mapped_column(Integer, default=0)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Evidence(Base):
    __tablename__ = "evidence"
    reviews: Mapped[list["EvidenceReview"]] = relationship(cascade="all, delete-orphan", lazy="selectin", order_by="EvidenceReview.id")
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    category: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(2000), default="")
    confirmation: Mapped[str] = mapped_column(String(30), default="unverified")
    published_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    event_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

class EvidenceReview(Base):
    __tablename__ = "evidence_reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    identity_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(Text, default="")
    evidence_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    author = relationship("User", lazy="selectin")


class AIReport(Base):
    __tablename__ = "ai_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(40), default="v1")
    evidence_hash: Mapped[str] = mapped_column(String(64))
    report: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Usage(Base):
    __tablename__ = "provider_usage"
    provider: Mapped[str] = mapped_column(String(40), primary_key=True)
    period: Mapped[str] = mapped_column(String(20), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
