from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.schemas.appointment import AppointmentOut

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Appointment]:
    return db.query(Appointment).filter(Appointment.tenant_id == user.tenant_id).all()


@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Appointment:
    appt = (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id, Appointment.tenant_id == user.tenant_id)
        .first()
    )
    if appt is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agendamento nao encontrado")

    appt.status = AppointmentStatus.cancelled
    db.commit()
    db.refresh(appt)
    return appt
