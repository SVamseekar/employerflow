import html
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

JOB_URL_PATTERNS = (
    r"indeed\.com/viewjob",
    r"linkedin\.com/jobs/view",
    r"glassdoor\.[a-z]+/job",
    r"monster\.com/job",
)

ENRICHABLE_FIELDS = (
    "company", "target_roles", "tech_stack", "city", "country",
    "remote", "language_requirement", "sector",
)

TECH_KEYWORDS = (
    "python", "java", "scala", "spark", "sql", "aws", "gcp", "azure",
    "kubernetes", "docker", "terraform", "dbt", "databricks", "snowflake",
    "kafka", "airflow", "pytorch", "tensorflow", "react", "node", "typescript",
    "postgresql", "mongodb", "redis", "elasticsearch", "tableau", "power bi",
    "machine learning", "deep learning", "llm", "genai",
)


def _blank(val: str | None) -> bool:
    if not val:
        return True
    return val.strip().lower() in ("", "unknown", "none", "not found", "n/a")


def is_job_posting_url(url: str | None) -> bool:
    if not url:
        return False
    lower = url.lower()
    return any(re.search(p, lower) for p in JOB_URL_PATTERNS)


def count_filled_fields(emp) -> int:
    count = 0
    for attr in (
        "website", "careers_url", "country", "city", "sector", "subsector",
        "company_stage", "company_scale", "employer_category", "remote",
        "visa_sponsorship", "eor", "hiring_geography", "target_roles",
        "tech_stack", "region_eligibility", "language_requirement",
        "hiring_confidence", "reason_match", "visa_sponsor_register",
    ):
        if not _blank(getattr(emp, attr, None)):
            count += 1
    return count


def classify_employer(emp) -> dict:
    careers = getattr(emp, "careers_url", "") or ""
    website = getattr(emp, "website", "") or ""
    reason = getattr(emp, "reason_match", "") or ""
    source = getattr(emp, "source", "") or ""
    filled = count_filled_fields(emp)

    is_job_url = is_job_posting_url(careers)
    is_scrape = (
        is_job_url
        and _blank(website)
        and (
            reason.lower().startswith("actively hiring")
            or "indeed" in source.lower()
            or "linkedin" in source.lower()
        )
    )

    if is_scrape:
        tier = "job_posting"
    elif not _blank(website) and filled >= 10:
        tier = "verified"
    elif filled >= 6:
        tier = "partial"
    else:
        tier = "sparse"

    return {
        "tier": tier,
        "filled_fields": filled,
        "is_job_posting": is_job_url,
        "is_scrape_record": is_scrape,
        "can_enrich": is_job_url and not _blank(careers),
    }


def _meta_tag(page: str, prop: str) -> str | None:
    for pattern in (
        rf'<meta[^>]+property=["\']{prop}["\'][^>]+content=["\']([^"\']+)',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{prop}',
        rf'<meta[^>]+name=["\']{prop}["\'][^>]+content=["\']([^"\']+)',
        rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{prop}',
    ):
        m = re.search(pattern, page, re.I)
        if m:
            return html.unescape(m.group(1).strip())
    return None


def _title_tag(page: str) -> str | None:
    m = re.search(r"<title[^>]*>([^<]+)</title>", page, re.I)
    return html.unescape(m.group(1).strip()) if m else None


def _looks_like_location(text: str) -> bool:
    if not text:
        return False
    if "," in text:
        return True
    markers = (
        "india", "ahmedabad", "mumbai", "bangalore", "hyderabad", "delhi",
        "pune", "chennai", "kolkata", "gujarat", "maharashtra", "karnataka",
        "germany", "london", "usa", "remote",
    )
    lower = text.lower()
    return any(m in lower for m in markers)


def _parse_job_title(raw: str) -> dict:
    text = re.sub(r"\s*[-|]\s*Indeed.*$", "", raw, flags=re.I).strip()
    text = re.sub(r"\s*[-|]\s*LinkedIn.*$", "", text, flags=re.I).strip()
    parts = [p.strip() for p in re.split(r"\s*[-–|]\s*", text) if p.strip()]

    role = company = location = None
    if len(parts) >= 3:
        role, company, location = parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        role, second = parts[0], parts[1]
        if _looks_like_location(second):
            location = second
        else:
            company = second
    elif len(parts) == 1:
        role = parts[0]

    if company and _looks_like_location(company):
        location = location or company
        company = None

    city = country = None
    loc_text = location or ""
    if loc_text:
        loc_parts = [p.strip() for p in loc_text.split(",")]
        if loc_parts:
            city = loc_parts[0]
        if len(loc_parts) > 1:
            country = loc_parts[-1]

    return {"role": role, "company": company, "city": city, "country": country}


def _extract_tech(text: str) -> str | None:
    if not text:
        return None
    lower = text.lower()
    found = []
    for kw in TECH_KEYWORDS:
        if kw in lower and kw not in found:
            found.append(kw.title() if len(kw) <= 4 else kw)
    return ", ".join(found[:8]) if found else None


def _enrich_from_record(emp) -> dict:
    suggestions = {}
    reason = (getattr(emp, "reason_match", None) or "").strip()
    roles = getattr(emp, "target_roles", None) or ""
    city = getattr(emp, "city", None) or ""
    country = getattr(emp, "country", None) or ""

    m = re.match(r"Actively hiring in\s+([^:]+):\s*(.+)", reason, re.I)
    if m:
        if not _blank(city):
            suggestions.setdefault("city", city)
        else:
            loc = m.group(1).strip()
            if "," in loc:
                suggestions["city"] = loc.split(",")[0].strip()
            else:
                suggestions["city"] = loc
        if _blank(roles):
            suggestions["target_roles"] = m.group(2).strip()
    elif not _blank(roles):
        suggestions["target_roles"] = roles.strip()

    if not _blank(city):
        suggestions.setdefault("city", city.strip())
    if not _blank(country):
        suggestions.setdefault("country", country.strip())
    if not _blank(getattr(emp, "language_requirement", None)):
        suggestions.setdefault("language_requirement", emp.language_requirement.strip())

    sector = getattr(emp, "sector", None) or ""
    if not _blank(sector) and sector.lower() != "tech":
        suggestions.setdefault("sector", sector.strip())

    return suggestions


def _enrich_via_jobspy(url: str, emp=None) -> dict | None:
    try:
        from jobspy import scrape_jobs
    except ImportError:
        return None

    jk_match = re.search(r"[?&]jk=([a-f0-9]+)", url, re.I)
    if not jk_match:
        return None

    jk = jk_match.group(1)
    search_term = ""
    location = ""
    country = "india"
    if emp:
        parts = [getattr(emp, "target_roles", ""), getattr(emp, "company", ""), getattr(emp, "city", "")]
        search_term = " ".join(p.strip() for p in parts if p and not _blank(p))[:120]
        location = (getattr(emp, "city", "") or "").strip()
        geo = (getattr(emp, "country", "") or "").lower()
        if any(t in geo for t in ("usa", "united states", "u.s.")):
            country = "usa"
        elif "germany" in geo:
            country = "germany"
        elif "uk" in geo or "united kingdom" in geo:
            country = "uk"

    try:
        jobs = scrape_jobs(
            site_name=["indeed"],
            search_term=search_term or "engineer",
            location=location,
            results_wanted=20,
            country_indeed=country,
            verbose=0,
        )
        if jobs is None or jobs.empty:
            return None

        matched = jobs[jobs["job_url"].astype(str).str.contains(jk, na=False)]
        if matched.empty and "id" in jobs.columns:
            matched = jobs[jobs["id"].astype(str).str.contains(jk, na=False)]
        if matched.empty:
            return None

        row = matched.iloc[0]
        out = {}
        company = str(row.get("company") or "").strip()
        title = str(row.get("title") or "").strip()
        desc = str(row.get("description") or "")
        if company and company.lower() not in ("unknown", "nan"):
            out["company"] = company
        if title and title.lower() not in ("unknown", "nan"):
            out["target_roles"] = title
        tech = _extract_tech(desc)
        if tech:
            out["tech_stack"] = tech
        loc = str(row.get("location") or "").strip()
        if loc and loc.lower() not in ("unknown", "nan"):
            loc_parts = [p.strip() for p in loc.split(",")]
            if loc_parts:
                out["city"] = loc_parts[0]
            if len(loc_parts) > 1:
                out["country"] = loc_parts[-1]
        return out or None
    except Exception:
        return None


def enrich_from_job_url(url: str, emp=None) -> dict:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urlopen(req, timeout=12) as resp:
            page = resp.read().decode("utf-8", errors="ignore")
    except (URLError, TimeoutError, OSError):
        page = None

    if not page:
        suggestions = _enrich_from_record(emp) if emp else {}
        jobspy_data = _enrich_via_jobspy(url, emp)
        if jobspy_data:
            suggestions = {**suggestions, **jobspy_data}
        if suggestions:
            return {
                "ok": True,
                "source": "record" if not jobspy_data else "jobspy",
                "source_url": url,
                "suggestions": suggestions,
                "note": "Live page blocked — filled from listing metadata and job index.",
            }
        return {"ok": False, "error": "Could not fetch job posting (site blocked automated access)."}

    og_title = _meta_tag(page, "og:title")
    title = og_title or _title_tag(page) or ""
    description = _meta_tag(page, "og:description") or _meta_tag(page, "description") or ""

    parsed = _parse_job_title(title)
    tech = _extract_tech(description)

    suggestions = {}
    if parsed.get("company"):
        suggestions["company"] = parsed["company"]
    if parsed.get("role"):
        suggestions["target_roles"] = parsed["role"]
    if parsed.get("city"):
        suggestions["city"] = parsed["city"]
    if parsed.get("country"):
        suggestions["country"] = parsed["country"]
    if tech:
        suggestions["tech_stack"] = tech

    remote = None
    if description:
        dl = description.lower()
        if "remote" in dl or "work from home" in dl:
            remote = "yes"
        elif "on-site" in dl or "on site" in dl:
            remote = "no"
    if remote:
        suggestions["remote"] = remote

    local = _enrich_from_record(emp) if emp else {}
    jobspy_data = _enrich_via_jobspy(url, emp) or {}
    merged = {**local, **suggestions, **jobspy_data}

    return {
        "ok": True,
        "source": "page",
        "source_url": url,
        "page_title": title,
        "description_snippet": description[:400] if description else None,
        "suggestions": merged,
    }