import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    cancelled = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"), nullable=False, index=True)

    client_name: Mapped[str] = mapped_column(String(160), nullable=False)
    client_contact: Mapped[str] = mapped_column(String(160), nullable=False)

    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.scheduled, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    service: Mapped["Service"] = relationship(back_populates="appointments")
