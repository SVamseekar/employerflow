from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_plan
from app.config import get_settings
from app.database import get_db
from app.models import Employer, PlanTier, ShortlistItem, User, UserProfile
from app.schemas import ShortlistUpdate
from app.services.email_generator import generate_email, guess_to_email
from app.services.scoring import score_all

router = APIRouter(prefix="/api/shortlist", tags=["shortlist"])
settings = get_settings()


def _limit_for_plan(plan: PlanTier) -> int:
    if plan == PlanTier.premium:
        return settings.premium_shortlist_limit
    return settings.pro_shortlist_limit


@router.post("/generate")
def generate_shortlist(
    user: User = Depends(require_plan(PlanTier.pro)),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile or profile.skills_json in ("", "[]"):
        raise HTTPException(status_code=400, detail="Complete your profile with skills before generating a shortlist.")

    employers = db.query(Employer).all()
    limit = _limit_for_plan(user.plan)
    scored = score_all(employers, profile, min_score=20, limit=limit)

    db.query(ShortlistItem).filter(ShortlistItem.user_id == user.id).delete()

    for item in scored:
        emp = item["employer"]
        draft = generate_email(user, profile, emp)
        db.add(ShortlistItem(
            user_id=user.id,
            employer_id=emp.id,
            score=item["score"],
            match_notes=item["match_notes"],
            email_draft=draft,
            to_email=guess_to_email(emp.company, emp.website),
            job_url=emp.careers_url,
        ))
    db.commit()

    return {"generated": len(scored), "limit": limit}


@router.get("")
def get_shortlist(user: User = Depends(require_plan(PlanTier.pro)), db: Session = Depends(get_db)):
    items = (
        db.query(ShortlistItem)
        .filter(ShortlistItem.user_id == user.id)
        .order_by(ShortlistItem.score.desc())
        .all()
    )
    result = []
    for item in items:
        emp = item.employer
        result.append({
            "id": item.id,
            "score": item.score,
            "match_notes": item.match_notes,
            "email_draft": item.email_draft,
            "to_email": item.to_email,
            "job_url": item.job_url,
            "outreach_status": item.outreach_status,
            "sent_at": item.sent_at.isoformat() if item.sent_at else None,
            "employer": {
                "id": emp.id,
                "company": emp.company,
                "sector": emp.sector,
                "country": emp.country,
                "tech_stack": emp.tech_stack,
                "visa_sponsorship": emp.visa_sponsorship,
                "careers_url": emp.careers_url,
                "website": emp.website,
            },
        })
    return result


@router.put("/{item_id}")
def update_shortlist_item(
    item_id: int,
    payload: ShortlistUpdate,
    user: User = Depends(require_plan(PlanTier.pro)),
    db: Session = Depends(get_db),
):
    item = db.query(ShortlistItem).filter(
        ShortlistItem.id == item_id, ShortlistItem.user_id == user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Shortlist item not found")

    if payload.email_draft:
        item.email_draft = payload.email_draft
    if payload.to_email:
        item.to_email = payload.to_email
    if payload.job_url:
        item.job_url = payload.job_url
    if payload.outreach_status:
        item.outreach_status = payload.outreach_status
    db.commit()
    return {"message": "Updated"}