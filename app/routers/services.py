from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.services.plan_limits import PlanLimitExceeded, ensure_can_create_service

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Service]:
    return (
        db.query(Service)
        .filter(Service.tenant_id == user.tenant_id)
        .order_by(Service.id)
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Service:
    try:
        ensure_can_create_service(db, user.tenant)
    except PlanLimitExceeded as exc:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc)) from exc

    service = Service(tenant_id=user.tenant_id, **payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Service:
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.tenant_id == user.tenant_id)
        .first()
    )
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "servico nao encontrado")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service
