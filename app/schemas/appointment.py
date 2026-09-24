from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    service_id: int
    client_name: str = Field(min_length=2, max_length=160)
    client_contact: str = Field(min_length=3, max_length=160)
    starts_at: datetime

    @field_validator("starts_at")
    @classmethod
    def _reject_past(cls, value: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        # Compara em UTC; datetime naive é assumido como UTC.
        moment = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        if moment < now:
            raise ValueError("starts_at nao pode estar no passado")
        return value


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    client_name: str
    client_contact: str
    starts_at: datetime
    duration_minutes: int
    status: AppointmentStatus
