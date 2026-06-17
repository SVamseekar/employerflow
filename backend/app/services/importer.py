import csv
import os

from sqlalchemy.orm import Session

from app.models import Employer
from app.services.data_quality import is_job_posting_url
from app.services.validation import clean_company_name, is_valid_company


def _is_scrape_row(row: dict) -> bool:
    website = (row.get("Website") or "").strip()
    careers = (row.get("Careers_URL") or "").strip()
    reason = (row.get("Reason_Match") or "").strip()
    if not is_job_posting_url(careers):
        return False
    if website and website.lower() not in ("unknown", "none", "n/a", ""):
        return False
    return reason.lower().startswith("actively hiring") or "indeed" in (row.get("Source") or "").lower()

FIELD_MAP = {
    "Company": "company",
    "Website": "website",
    "Careers_URL": "careers_url",
    "Country": "country",
    "City": "city",
    "Sector": "sector",
    "Subsector": "subsector",
    "Company_Stage": "company_stage",
    "Company_Scale": "company_scale",
    "Employer_Category": "employer_category",
    "Remote": "remote",
    "Visa_Sponsorship": "visa_sponsorship",
    "EOR": "eor",
    "Hiring_Geography": "hiring_geography",
    "Target_Roles": "target_roles",
    "Tech_Stack": "tech_stack",
    "Region_Eligibility": "region_eligibility",
    "Language_Requirement": "language_requirement",
    "Hiring_Confidence": "hiring_confidence",
    "Reason_Match": "reason_match",
    "Source": "source",
    "Visa_Sponsor_Register": "visa_sponsor_register",
}


def import_from_csv(db: Session, csv_path: str) -> tuple[int, int]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    existing = {e.company.lower() for e in db.query(Employer.company).all()}
    added = skipped = 0

    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            company = clean_company_name((row.get("Company") or "").strip())
            if not is_valid_company(company) or _is_scrape_row(row):
                skipped += 1
                continue
            key = company.lower()
            if key in existing:
                skipped += 1
                continue

            data = {attr: (row.get(csv_field, "") or "")[:2000] for csv_field, attr in FIELD_MAP.items()}
            data["company"] = company[:255]
            db.add(Employer(**data))
            existing.add(key)
            added += 1
            if added % 500 == 0:
                db.commit()

    db.commit()
    return added, skipped