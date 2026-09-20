from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.service import Service
from app.models.tenant import Plan, Tenant


class PlanLimitExceeded(Exception):
    pass


def ensure_can_create_service(db: Session, tenant: Tenant) -> None:
    """Free plan caps active services; pro plan has no cap.

    Kept as its own function (not inline in the router) so the rule is
    testable in isolation and easy to change if pricing tiers evolve.
    """
    if tenant.plan != Plan.free:
        return

    active_count = db.scalar(
        select(func.count())
        .select_from(Service)
        .where(Service.tenant_id == tenant.id, Service.active.is_(True))
    )
    if active_count is not None and active_count >= settings.free_plan_max_services:
        raise PlanLimitExceeded(
            f"Plano free permite no maximo {settings.free_plan_max_services} servicos ativos. "
            "Faca upgrade para pro ou desative um servico existente."
        )
