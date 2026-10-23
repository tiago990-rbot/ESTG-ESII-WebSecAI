from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.types import UTCDateTime


class AccountAction(Base):
    __tablename__ = "account_actions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(12))
    auth_version: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(timezone=True))
