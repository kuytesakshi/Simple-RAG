import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    """Login users. Passwords are NEVER stored plain — only bcrypt hashes."""

    __tablename__ = "users"

    # UUID PK: stable, non-enumerable (unlike 1,2,3 ints in URLs/tokens)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # Login name: unique + indexed for fast lookup on every login
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # bcrypt hash (~60 chars); 255 leaves headroom
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Kill-switch: disable logins without deleting the row/audit trail
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Admin flag: prompt library + future admin endpoints. Default false;
    # existing rows backfilled by lifespan migration (ADD COLUMN IF NOT EXISTS).
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
