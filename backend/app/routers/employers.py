from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Employer, PlanTier, User, UserProfile
from app.services.scoring import score_employer
from app.services.validation import clean_company_name, is_valid_company

router = APIRouter(prefix="/api/employers", tags=["employers"])
settings = get_settings()

EU_COUNTRIES = [
    "germany", "netherlands", "france", "sweden", "ireland", "spain", "portugal",
    "denmark", "finland", "austria", "belgium", "poland", "czech", "norway",
    "switzerland", "europe", "estonia", "latvia", "lithuania",
]
INDIA_TERMS = [
    "india", "hyderabad", "bangalore", "bengaluru", "mumbai",
    "pune", "chennai", "delhi", "noida", "gurgaon", "gurugram", "kolkata",
]


def _classify_region(emp: Employer) -> str:
    geo = f"{emp.country} {emp.hiring_geography} {emp.city}".lower()
    if any(c in geo for c in EU_COUNTRIES):
        return "Europe"
    if any(c in geo for c in ["usa", "united states", "u.s."]):
        return "USA"
    if any(c in geo for c in ["australia", "new zealand"]):
        return "Australia/NZ"
    if any(c in geo for c in INDIA_TERMS):
        return "India"
    return "Remote/Global"


def _employer_dict(emp: Employer, score: int | None = None) -> dict:
    return {
        "id": emp.id,
        "company": emp.company,
        "website": emp.website,
        "careers_url": emp.careers_url,
        "country": emp.country,
        "city": emp.city,
        "sector": emp.sector,
        "company_stage": emp.company_stage,
        "employer_category": emp.employer_category,
        "remote": emp.remote,
        "visa_sponsorship": emp.visa_sponsorship,
        "visa_sponsor_register": emp.visa_sponsor_register,
        "tech_stack": emp.tech_stack,
        "language_requirement": emp.language_requirement,
        "reason_match": emp.reason_match,
        "source": emp.source,
        "region": _classify_region(emp),
        "score": score,
    }


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    all_emps = db.query(Employer).all()
    valid = [e for e in all_emps if is_valid_company(clean_company_name(e.company))]
    total = len(valid)
    visa_yes = sum(1 for e in valid if (e.visa_sponsorship or "").lower() == "yes")
    remote_yes = sum(1 for e in valid if (e.remote or "").lower() == "yes")
    return {"total": total, "visa_confirmed": visa_yes, "remote": remote_yes}


@router.get("")
def list_employers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    region: Optional[str] = None,
    visa: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Employer)

    if search:
        term = f"%{search.lower()}%"
        q = q.filter(
            or_(
                func.lower(Employer.company).like(term),
                func.lower(Employer.sector).like(term),
                func.lower(Employer.tech_stack).like(term),
                func.lower(Employer.country).like(term),
            )
        )

    if visa == "confirmed":
        q = q.filter(func.lower(Employer.visa_sponsorship) == "yes")
    elif visa == "possible":
        q = q.filter(func.lower(Employer.visa_sponsorship) == "possible")
    elif visa == "remote":
        q = q.filter(func.lower(Employer.remote) == "yes")

    raw = q.order_by(Employer.company).all()
    employers = []
    for emp in raw:
        cleaned = clean_company_name(emp.company)
        if is_valid_company(cleaned):
            emp.company = cleaned
            employers.append(emp)

    if region:
        employers = [e for e in employers if _classify_region(e).lower() == region.lower()]

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    can_score = user.plan != PlanTier.free

    if user.plan == PlanTier.free:
        employers = employers[: settings.free_employer_limit]

    total = len(employers)
    start = (page - 1) * limit
    page_items = employers[start : start + limit]

    data = []
    for emp in page_items:
        score = score_employer(emp, profile)[0] if can_score and profile else None
        data.append(_employer_dict(emp, score))

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "plan": user.plan.value,
        "scoring_enabled": can_score,
        "data": data,
    }