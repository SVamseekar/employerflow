from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Employer, PlanTier, User, UserProfile
from app.services.data_quality import classify_employer, enrich_from_job_url
from app.services.scoring import score_employer
from app.services.validation import clean_company_name

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


def _geo_text():
    return func.lower(
        func.concat(
            func.coalesce(Employer.country, ""),
            " ",
            func.coalesce(Employer.hiring_geography, ""),
            " ",
            func.coalesce(Employer.city, ""),
        )
    )


def _region_filter(region: str):
    geo = _geo_text()
    key = region.lower()
    if key == "europe":
        return or_(*[geo.like(f"%{c}%") for c in EU_COUNTRIES])
    if key == "usa":
        return or_(*[geo.like(f"%{c}%") for c in ["usa", "united states", "u.s."]])
    if key in ("australia/nz", "australia"):
        return or_(*[geo.like(f"%{c}%") for c in ["australia", "new zealand"]])
    if key == "india":
        return or_(*[geo.like(f"%{c}%") for c in INDIA_TERMS])
    if key in ("remote/global", "remote"):
        return True
    return True


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
    quality = classify_employer(emp)
    return {
        "id": emp.id,
        "company": emp.company,
        "website": emp.website,
        "careers_url": emp.careers_url,
        "country": emp.country,
        "city": emp.city,
        "sector": emp.sector,
        "subsector": emp.subsector,
        "company_stage": emp.company_stage,
        "company_scale": emp.company_scale,
        "employer_category": emp.employer_category,
        "remote": emp.remote,
        "visa_sponsorship": emp.visa_sponsorship,
        "eor": emp.eor,
        "hiring_geography": emp.hiring_geography,
        "target_roles": emp.target_roles,
        "tech_stack": emp.tech_stack,
        "region_eligibility": emp.region_eligibility,
        "language_requirement": emp.language_requirement,
        "hiring_confidence": emp.hiring_confidence,
        "reason_match": emp.reason_match,
        "source": emp.source,
        "visa_sponsor_register": emp.visa_sponsor_register,
        "region": _classify_region(emp),
        "score": score,
        "data_quality": quality["tier"],
        "filled_fields": quality["filled_fields"],
        "is_job_posting": quality["is_job_posting"],
        "can_enrich": quality["can_enrich"],
    }


def _base_query(
    db: Session,
    search: Optional[str],
    region: Optional[str],
    visa: Optional[str],
    quality: Optional[str] = None,
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

    if region:
        clause = _region_filter(region)
        if clause is not True:
            q = q.filter(clause)

    if quality == "verified":
        q = q.filter(
            Employer.website.isnot(None),
            func.lower(Employer.website) != "unknown",
            Employer.website != "",
            ~func.lower(Employer.careers_url).like("%indeed.com/viewjob%"),
            ~func.lower(Employer.careers_url).like("%linkedin.com/jobs/view%"),
        )
    elif quality == "exclude_scrapes":
        q = q.filter(
            or_(
                ~func.lower(Employer.reason_match).like("actively hiring%"),
                and_(
                    Employer.website.isnot(None),
                    func.lower(Employer.website) != "unknown",
                    Employer.website != "",
                ),
            )
        )

    return q


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Employer.id)).scalar() or 0
    visa_yes = (
        db.query(func.count(Employer.id))
        .filter(func.lower(Employer.visa_sponsorship) == "yes")
        .scalar()
        or 0
    )
    remote_yes = (
        db.query(func.count(Employer.id))
        .filter(func.lower(Employer.remote) == "yes")
        .scalar()
        or 0
    )
    return {"total": total, "visa_confirmed": visa_yes, "remote": remote_yes}


@router.get("/")
def list_employers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    region: Optional[str] = None,
    visa: Optional[str] = None,
    quality: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _base_query(db, search, region, visa, quality)
    total = q.count()

    if user.plan == PlanTier.free:
        total = min(total, settings.free_employer_limit)

    start = (page - 1) * limit
    if user.plan == PlanTier.free and start >= settings.free_employer_limit:
        page_items = []
    else:
        page_items = (
            q.order_by(Employer.company)
            .offset(start)
            .limit(limit if user.plan != PlanTier.free else min(limit, settings.free_employer_limit - start))
            .all()
        )

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    can_score = user.plan != PlanTier.free

    data = []
    for emp in page_items:
        emp.company = clean_company_name(emp.company)
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


@router.get("/{employer_id}")
def get_employer(
    employer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = db.get(Employer, employer_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employer not found")

    if user.plan == PlanTier.free:
        allowed = (
            db.query(Employer.id)
            .order_by(Employer.company)
            .limit(settings.free_employer_limit)
            .all()
        )
        if employer_id not in {row[0] for row in allowed}:
            raise HTTPException(status_code=402, detail="Upgrade to Pro to view full employer details.")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    can_score = user.plan != PlanTier.free
    emp.company = clean_company_name(emp.company)
    score = score_employer(emp, profile)[0] if can_score and profile else None
    return _employer_dict(emp, score)


@router.post("/{employer_id}/enrich")
def enrich_employer(
    employer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.plan == PlanTier.free:
        raise HTTPException(status_code=402, detail="Upgrade to Pro to enrich employer data.")

    emp = db.get(Employer, employer_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employer not found")

    quality = classify_employer(emp)
    if not quality["can_enrich"]:
        raise HTTPException(status_code=400, detail="No job posting URL available to enrich from.")

    result = enrich_from_job_url(emp.careers_url, emp)
    if not result.get("ok"):
        raise HTTPException(status_code=502, detail=result.get("error", "Failed to fetch job posting"))

    return {
        "employer_id": employer_id,
        "current": _employer_dict(emp, None),
        "enrichment": result,
    }