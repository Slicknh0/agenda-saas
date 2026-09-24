from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.ratelimit import limiter
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.tenant import Tenant
from app.schemas.appointment import AppointmentCreate, AppointmentOut
from app.schemas.service import ServiceOut
from app.services.booking import BookingConflict, ensure_no_conflict

router = APIRouter(prefix="/public", tags=["public"])


def _get_tenant_or_404(slug: str, db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "negocio nao encontrado")
    return tenant


@router.get("/{slug}/services", response_model=list[ServiceOut])
def list_public_services(
    slug: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Service]:
    tenant = _get_tenant_or_404(slug, db)
    return (
        db.query(Service)
        .filter(Service.tenant_id == tenant.id, Service.active.is_(True))
        .order_by(Service.id)
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.post("/{slug}/book", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def book_appointment(
    request: Request, slug: str, payload: AppointmentCreate, db: Session = Depends(get_db)
) -> Appointment:
    tenant = _get_tenant_or_404(slug, db)

    service = (
        db.query(Service)
        .filter(
            Service.id == payload.service_id,
            Service.tenant_id == tenant.id,
            Service.active.is_(True),
        )
        .first()
    )
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "servico nao encontrado")

    try:
        ensure_no_conflict(
            db,
            service_id=service.id,
            starts_at=payload.starts_at,
            duration_minutes=service.duration_minutes,
        )
    except BookingConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    appointment = Appointment(
        tenant_id=tenant.id,
        service_id=service.id,
        client_name=payload.client_name,
        client_contact=payload.client_contact,
        starts_at=payload.starts_at,
        duration_minutes=service.duration_minutes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
