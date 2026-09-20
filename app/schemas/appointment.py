from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    service_id: int
    client_name: str = Field(min_length=2, max_length=160)
    client_contact: str = Field(min_length=3, max_length=160)
    starts_at: datetime


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    client_name: str
    client_contact: str
    starts_at: datetime
    duration_minutes: int
    status: AppointmentStatus
