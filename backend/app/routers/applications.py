from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_plan
from app.database import get_db
from app.models import Application, PlanTier, User
from app.schemas import ApplicationCreate

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
def list_applications(
    user: User = Depends(require_plan(PlanTier.premium)),
    db: Session = Depends(get_db),
):
    apps = db.query(Application).filter(Application.user_id == user.id).order_by(Application.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "company": a.company,
            "role": a.role,
            "job_url": a.job_url,
            "source": a.source,
            "status": a.status,
            "applied_date": a.applied_date,
            "follow_up_date": a.follow_up_date,
            "notes": a.notes,
        }
        for a in apps
    ]


@router.post("")
def upsert_application(
    payload: ApplicationCreate,
    user: User = Depends(require_plan(PlanTier.premium)),
    db: Session = Depends(get_db),
):
    existing = db.query(Application).filter(
        Application.user_id == user.id,
        Application.company == payload.company,
    ).first()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if existing:
        existing.role = payload.role
        existing.job_url = payload.job_url
        existing.status = payload.status
        existing.follow_up_date = payload.follow_up_date
        existing.notes = payload.notes
        db.commit()
        return {"id": existing.id, "updated": True}

    app = Application(
        user_id=user.id,
        company=payload.company,
        role=payload.role,
        job_url=payload.job_url,
        source=payload.source,
        status=payload.status,
        applied_date=payload.applied_date or today,
        follow_up_date=payload.follow_up_date,
        notes=payload.notes,
    )
    db.add(app)
    db.commit()
    return {"id": app.id, "updated": False}