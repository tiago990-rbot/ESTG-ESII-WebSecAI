from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.types import UTCDateTime

def now(): return datetime.now(timezone.utc)

class LabProject(Base):
    __tablename__ = "lab_projects"
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"),index=True)
    name: Mapped[str] = mapped_column(String(100))
    revision: Mapped[str] = mapped_column(String(100))
    digest: Mapped[str] = mapped_column(String(64))
    files: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True),default=now)
    runs: Mapped[list["LabRun"]] = relationship(cascade="all, delete-orphan",lazy="selectin",order_by="LabRun.created_at, LabRun.id")

class LabRun(Base):
    __tablename__ = "lab_runs"
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("lab_projects.id",ondelete="CASCADE"),index=True)
    tool: Mapped[str] = mapped_column(String(30))
    version: Mapped[str] = mapped_column(String(50),default="unknown")
    status: Mapped[str] = mapped_column(String(30))
    report: Mapped[dict] = mapped_column(JSON,default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True),default=now)

class LabReview(Base):
    __tablename__ = "lab_reviews"
    __table_args__ = (UniqueConstraint("project_id","finding_id","sequence"),)
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("lab_projects.id",ondelete="CASCADE"),index=True)
    finding_id: Mapped[str] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text,default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True),default=now)
