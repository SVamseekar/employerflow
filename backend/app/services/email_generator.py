"""Template-based cold email generation — no LLM."""

import json
import re

from app.models import Employer, User, UserProfile

_INDIA_TERMS = {
    "india", "hyderabad", "bangalore", "bengaluru", "mumbai", "pune",
    "chennai", "delhi", "noida", "gurgaon", "gurugram", "kolkata",
}


def _load_projects(profile: UserProfile) -> list[dict]:
    try:
        return json.loads(profile.projects_json) or []
    except json.JSONDecodeError:
        return []


def _load_skills(profile: UserProfile) -> list[str]:
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


def _load_languages(profile: UserProfile) -> dict[str, str]:
    try:
        return json.loads(profile.languages_json) or {}
    except json.JSONDecodeError:
        return {}


def get_best_project(profile: UserProfile, sector: str, reason: str = "", tech_stack: str = "") -> dict:
    combined = f"{sector} {reason} {tech_stack}".lower()
    projects = _load_projects(profile)
    if not projects:
        return {"one_liner": profile.summary or "relevant production experience in data and AI engineering"}
    best = projects[0]
    best_score = 0
    for project in projects:
        themes = project.get("themes", [])
        score = sum(1 for theme in themes if theme.lower() in combined)
        if score > best_score:
            best_score = score
            best = project
    return best


def get_skill_overlap(profile: UserProfile, tech_stack: str, max_skills: int = 4) -> list[str]:
    stack_lower = tech_stack.lower()
    matched = [s for s in _load_skills(profile) if s.lower() in stack_lower]
    return sorted(matched, key=len, reverse=True)[:max_skills]


def get_visa_line(profile: UserProfile, country: str, remote: str = "") -> str:
    combined = country.lower()
    eu_countries = [
        "germany", "netherlands", "ireland", "france", "sweden", "austria",
        "denmark", "finland", "belgium", "switzerland", "norway", "europe",
    ]
    visa = profile.visa_status or "eligible for work authorization"

    if any(c in combined for c in _INDIA_TERMS):
        return "I'm currently based locally — no relocation or visa overhead on your end."
    if any(c in combined for c in eu_countries):
        return f"I'm {visa} and ready to relocate — no visa sponsorship complexity on your end."
    if remote.lower() == "yes":
        return "I work fully remotely in production and can join a remote team immediately."
    return f"I'm {visa} and open to relocation, which means zero visa friction for you."


def get_language_line(profile: UserProfile, language_req: str) -> str:
    if not language_req or language_req.strip().lower() in ("", "unknown", "none", "english"):
        return ""
    lang = language_req.replace("(Learning)", "").strip().rstrip("(").strip()
    languages = _load_languages(profile)
    level = languages.get(lang, "beginner")
    if level in ("native", "fluent"):
        return ""
    return (
        f"On the language front — I'm currently learning {lang} and am at {level} level. "
        f"I'm actively studying and committed to reaching professional proficiency. "
        f"In the meantime I'm fully productive in English."
    )


def _subject(company: str, country: str, profile: UserProfile) -> str:
    roles = json.loads(profile.role_targets_json) if profile.role_targets_json else ["Data Engineer"]
    role = roles[0] if roles else "Data Engineer"
    if any(t in country.lower() for t in _INDIA_TERMS):
        return f"{role} — {company} | Available Immediately"
    visa = profile.visa_status or "Work Authorized"
    return f"{role} — {company} | {visa}"


def guess_to_email(company: str, website: str) -> str:
    domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    if domain and domain != "Unknown":
        return f"careers@{domain}"
    slug = re.sub(r"[^a-z0-9]", "", company.lower())
    return f"careers@{slug}.com"


def generate_email(
    user: User,
    profile: UserProfile,
    employer: Employer,
    open_role: str = "",
) -> str:
    project = get_best_project(profile, employer.sector, employer.reason_match, employer.tech_stack)
    skill_overlap = get_skill_overlap(profile, employer.tech_stack)
    visa_line = get_visa_line(profile, employer.country, employer.remote)
    lang_line = get_language_line(profile, employer.language_requirement)

    role_line = f"regarding the {open_role} role" if open_role else "about potential opportunities"
    role_intro = f"I'm reaching out {role_line}."

    if skill_overlap:
        tech_mention = f"I noticed your stack includes {', '.join(skill_overlap[:3])} — tools I use daily in production."
    elif employer.tech_stack and employer.tech_stack not in ("Unknown", ""):
        tech_mention = f"Your work in {employer.sector} maps closely to what I've been building."
    else:
        tech_mention = f"Your focus on {employer.sector} aligns with my background."

    one_liner = project.get("one_liner") or project.get("highlight") or profile.summary
    stack = profile.stack_highlight or ", ".join(_load_skills(profile)[:8])
    lang_block = f"\n{lang_line}\n" if lang_line else ""

    signature = f"""{user.full_name or user.email}
{user.email} | {profile.linkedin}
{profile.certification}
{profile.visa_status}"""

    email = f"""Subject: {_subject(employer.company, employer.country, profile)}

Hi {employer.company} Team,

I came across {employer.company} while researching {employer.sector} companies and wanted to reach out directly.

{role_intro} {tech_mention}

One example of my work: {one_liner}.

My current stack: {stack}.

{visa_line}
{lang_block}
Would you be open to a 20-minute call to see if there's a fit?

{signature}"""

    return email.strip()