"""Deterministic employer scoring — no LLM."""

import json
from typing import Any

from app.models import Employer, UserProfile

AI_KEYWORDS = {
    "ai", "ml", "machine learning", "deep learning", "llm", "nlp", "data",
    "analytics", "platform", "infrastructure", "cloud", "mlops", "databricks",
    "spark", "kafka", "dbt", "pipeline", "warehouse", "lakehouse", "rag",
    "fastapi", "spring boot", "azure", "gcp", "geospatial", "compliance",
    "event-driven", "distributed", "backend",
}

EU_COUNTRIES = {
    "germany", "netherlands", "france", "sweden", "spain", "portugal",
    "denmark", "finland", "austria", "belgium", "poland", "czech", "ireland",
    "switzerland", "norway", "estonia", "latvia", "lithuania", "europe", "eu",
}

INDIA_TERMS = {
    "india", "hyderabad", "bangalore", "bengaluru", "mumbai", "pune",
    "chennai", "delhi", "noida", "gurgaon", "gurugram", "kolkata",
}

PORTFOLIO_THEMES = {
    "ai assurance": ["ai assurance", "ai safety", "ai audit", "model governance"],
    "ai governance": ["ai governance", "ai policy", "responsible ai", "ai regulation"],
    "eu policy": ["eu policy", "eu regulation", "gdpr", "ai act", "european"],
    "workforce analytics": ["workforce", "hr analytics", "people analytics", "talent analytics"],
    "transport analytics": ["transport", "mobility", "logistics", "fleet", "transit", "rail"],
    "smart cities": ["smart city", "smart cities", "urban", "city data", "municipal"],
    "geospatial": ["geospatial", "gis", "mapping", "location", "spatial", "satellite"],
    "fintech infrastructure": ["fintech", "payments", "banking", "financial infrastructure"],
    "compliance systems": ["compliance", "regtech", "regulatory", "aml", "kyc", "audit"],
    "public sector analytics": ["govtech", "public sector", "government", "civic"],
    "enterprise data platforms": ["data platform", "data warehouse", "lakehouse", "enterprise data"],
}

HIGH_VALUE_STAGES = {"startup", "series a", "series b", "series c", "scale", "growth", "scaleup"}
HIGH_VALUE_CATEGORIES = {
    "yc", "remote-first", "eu startup", "eu remote", "eu tech",
    "github signal", "remotive", "hn hiring",
    "australia tech", "new zealand tech",
    "india tech", "india gcc", "india data", "india fintech",
    "india product", "india ai", "india mnc",
}


def _profile_themes(profile: UserProfile | None) -> dict[str, list[str]]:
    if not profile or not profile.projects_json:
        return PORTFOLIO_THEMES
    try:
        projects = json.loads(profile.projects_json)
    except json.JSONDecodeError:
        return PORTFOLIO_THEMES
    custom: dict[str, list[str]] = {}
    for p in projects:
        themes = p.get("themes", [])
        if themes:
            custom[p.get("name", "project").lower()] = [t.lower() for t in themes]
    return {**PORTFOLIO_THEMES, **custom}


def _profile_skills(profile: UserProfile | None) -> list[str]:
    if not profile:
        return []
    try:
        skills = json.loads(profile.skills_json)
    except json.JSONDecodeError:
        return []
    if isinstance(skills, dict):
        out = []
        for group in skills.values():
            out.extend(group)
        return out
    return skills if isinstance(skills, list) else []


def employer_to_row(emp: Employer) -> dict[str, str]:
    return {
        "Sector": emp.sector,
        "Tech_Stack": emp.tech_stack,
        "Employer_Category": emp.employer_category,
        "Company_Stage": emp.company_stage,
        "Visa_Sponsorship": emp.visa_sponsorship,
        "Visa_Sponsor_Register": emp.visa_sponsor_register,
        "EOR": emp.eor,
        "Hiring_Geography": emp.hiring_geography,
        "Country": emp.country,
        "City": emp.city,
        "Remote": emp.remote,
        "Language_Requirement": emp.language_requirement,
        "Target_Roles": emp.target_roles,
        "Region_Eligibility": emp.region_eligibility,
        "Hiring_Confidence": emp.hiring_confidence,
        "Reason_Match": emp.reason_match,
        "Source": emp.source,
        "Subsector": emp.subsector,
    }


def score_employer(
    emp: Employer,
    profile: UserProfile | None = None,
    active_hiring: bool = False,
) -> tuple[int, str]:
    row = employer_to_row(emp)
    themes = _profile_themes(profile)
    user_skills = [s.lower() for s in _profile_skills(profile)]

    s = 0
    notes: list[str] = []

    sector = (row.get("Sector", "") + " " + row.get("Tech_Stack", "")).lower()
    category = row.get("Employer_Category", "").lower()
    stage = row.get("Company_Stage", "").lower()
    visa = row.get("Visa_Sponsorship", "").lower()
    sponsor = row.get("Visa_Sponsor_Register", "").lower()
    remote = row.get("Remote", "").lower()
    geo = (row.get("Hiring_Geography", "") + " " + row.get("Country", "") + " " + row.get("City", "")).lower()
    confidence = row.get("Hiring_Confidence", "").lower()
    reason = row.get("Reason_Match", "").lower()
    source = row.get("Source", "").lower()
    language_req = row.get("Language_Requirement", "").lower()

    matched_kw = [kw for kw in AI_KEYWORDS if kw in sector or kw in reason]
    if user_skills:
        stack_lower = sector
        skill_hits = [sk for sk in user_skills if sk in stack_lower or sk in reason]
        matched_kw = list(dict.fromkeys(matched_kw + skill_hits[:5]))
    kw_score = min(len(matched_kw) * 6, 30)
    s += kw_score
    if matched_kw:
        notes.append(f"Tech: {', '.join(matched_kw[:3])}")

    all_text = f"{sector} {reason} {row.get('Tech_Stack', '')} {row.get('Subsector', '')}".lower()
    matched_themes = []
    for theme, keywords in themes.items():
        if any(kw in all_text for kw in keywords):
            matched_themes.append(theme)
    theme_score = min(len(matched_themes) * 8, 25)
    s += theme_score
    if matched_themes:
        notes.append(f"Portfolio: {', '.join(matched_themes[:2])}")

    is_india = any(c in geo for c in INDIA_TERMS)
    profile_location = (profile.location if profile else "").lower()
    user_in_india = any(t in profile_location for t in INDIA_TERMS)

    if not is_india:
        if visa == "yes" or "uk skilled worker" in sponsor or "ireland" in sponsor or "netherlands" in sponsor:
            s += 25
            notes.append("Confirmed visa sponsor")
        elif "eu blue card" in sponsor or "possible" in visa:
            s += 15
            notes.append("EU Blue Card country")
        elif sponsor not in ("not found", "unknown", ""):
            s += 8

    if row.get("EOR", "").lower() == "yes":
        s += 10
        notes.append("EOR available")

    if is_india and user_in_india:
        s += 15
        notes.append("India (local, no visa)")
    elif any(c in geo for c in EU_COUNTRIES):
        s += 15
        notes.append("EU based")
    elif remote == "yes":
        s += 8
        notes.append("Remote")

    if any(c in geo for c in ["australia", "new zealand"]):
        s += 10
        notes.append("AU/NZ")

    if any(c in category for c in HIGH_VALUE_CATEGORIES):
        s += 8

    if any(st in stage for st in HIGH_VALUE_STAGES):
        s += 5
        notes.append("Growth stage")

    if "(learning)" in language_req and language_req not in ("unknown", "english", "none", ""):
        s -= 8
        notes.append("Lang barrier")

    target_roles = row.get("Target_Roles", "").lower()
    if any(kw in target_roles for kw in ["data", "ai", "machine learning", "ml", "engineer", "analytics", "platform"]):
        s += 15
        notes.append("Target role match")

    region_elig = row.get("Region_Eligibility", "").lower()
    if any(x in region_elig for x in ["eligible", "open", "global", "worldwide", "india", "yes"]):
        s += 10
        notes.append("Region eligible")

    if confidence == "high":
        s += 5
    elif confidence == "medium":
        s += 2

    if "yc" in category or "yc" in source:
        s += 5
        notes.append("YC backed")

    if active_hiring:
        s += 20
        notes.append("Active hiring signal")

    return s, "; ".join(notes)


def score_all(
    employers: list[Employer],
    profile: UserProfile | None,
    min_score: int = 20,
    limit: int = 500,
    active_hiring: set[str] | None = None,
) -> list[dict[str, Any]]:
    active = active_hiring or set()
    scored = []
    for emp in employers:
        score, notes = score_employer(
            emp, profile, active_hiring=emp.company.lower().strip() in active
        )
        if score >= min_score:
            scored.append({"employer": emp, "score": score, "match_notes": notes})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]