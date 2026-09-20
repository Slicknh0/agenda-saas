from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus


class BookingConflict(Exception):
    pass


def ensure_no_conflict(
    db: Session, *, service_id: int, starts_at: datetime, duration_minutes: int
) -> None:
    """Reject a booking that overlaps an existing scheduled appointment
    for the same service.

    Scope is per-service, not per-tenant: this schema models one
    resource per service (no separate staff/room entity), which keeps
    the demo focused. A real multi-staff booking system would check
    conflicts per assigned resource instead — noted as a next step in
    the README.
    """
    new_end = starts_at + timedelta(minutes=duration_minutes)

    existing = db.scalars(
        select(Appointment).where(
            Appointment.service_id == service_id,
            Appointment.status == AppointmentStatus.scheduled,
        )
    ).all()

    for appt in existing:
        existing_end = appt.starts_at + timedelta(minutes=appt.duration_minutes)
        overlaps = starts_at < existing_end and new_end > appt.starts_at
        if overlaps:
            raise BookingConflict(
                f"Horario indisponivel: conflita com agendamento existente as {appt.starts_at.isoformat()}."
            )
