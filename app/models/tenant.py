import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Plan(str, enum.Enum):
    free = "free"
    pro = "pro"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    plan: Mapped[Plan] = mapped_column(Enum(Plan), default=Plan.free, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    services: Mapped[list["Service"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
