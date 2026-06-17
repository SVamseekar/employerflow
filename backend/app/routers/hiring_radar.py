from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import JobSignal, PlanTier, User

router = APIRouter(prefix="/api/hiring-radar", tags=["hiring-radar"])
settings = get_settings()


def _limit_for_plan(plan: PlanTier) -> int:
    if plan == PlanTier.premium:
        return settings.premium_hiring_radar_limit
    if plan == PlanTier.pro:
        return settings.pro_hiring_radar_limit
    return settings.free_hiring_radar_limit


@router.get("/stats")
def radar_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total = db.query(func.count(JobSignal.id)).scalar() or 0
    sources = (
        db.query(JobSignal.source, func.count(JobSignal.id))
        .group_by(JobSignal.source)
        .order_by(func.count(JobSignal.id).desc())
        .limit(8)
        .all()
    )
    return {
        "total_signals": total,
        "your_limit": _limit_for_plan(user.plan),
        "plan": user.plan.value,
        "top_sources": [{"source": s, "count": c} for s, c in sources],
    }


@router.get("/")
def list_signals(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    region: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan_limit = _limit_for_plan(user.plan)
    if user.plan == PlanTier.free and plan_limit == 0:
        raise HTTPException(
            status_code=402,
            detail="Hiring Radar is a Pro feature. Upgrade to see live job signals from Indeed, LinkedIn, Seek, and more.",
        )

    q = db.query(JobSignal)
    if search:
        term = f"%{search.lower()}%"
        q = q.filter(
            or_(
                func.lower(JobSignal.company).like(term),
                func.lower(JobSignal.job_title).like(term),
                func.lower(JobSignal.tech_stack).like(term),
                func.lower(JobSignal.city).like(term),
            )
        )
    if region:
        q = q.filter(func.lower(JobSignal.country).like(f"%{region.lower()}%"))

    total = q.count()
    cap = min(total, plan_limit)
    start = (page - 1) * limit
    if start >= cap:
        items = []
    else:
        items = (
            q.order_by(JobSignal.id.desc())
            .offset(start)
            .limit(min(limit, cap - start))
            .all()
        )

    return {
        "total": cap,
        "total_in_db": total,
        "page": page,
        "limit": limit,
        "plan": user.plan.value,
        "upgrade_for_more": user.plan != PlanTier.premium,
        "data": [
            {
                "id": j.id,
                "company": j.company,
                "job_title": j.job_title,
                "job_url": j.job_url,
                "country": j.country,
                "city": j.city,
                "sector": j.sector,
                "tech_stack": j.tech_stack,
                "source": j.source,
                "reason_match": j.reason_match,
                "hiring_confidence": j.hiring_confidence,
            }
            for j in items
        ],
    }