import html
import re


def clean_company_name(name: str) -> str:
    if not name:
        return ""
    name = html.unescape(name)
    name = name.strip("'\"` \t\n\r")
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\[.*?\]", "", name)
    return name.strip("'\"` \t\n\r")


def is_valid_company(name: str) -> bool:
    if not name:
        return False
    if not re.match(r"^[a-zA-Z0-9]", name):
        return False

    lower_name = name.lower()
    junk_patterns = [
        r"\bwe're\b", r"\bwe are\b", r"\bi am\b", r"\blooking for\b",
        r"\bposition\b", r"\brole\b", r"\bjob\b", r"\bhiring\b",
        r"\bapply\b", r"\bcareers?\b", r"\bcv\b", r"\bresume\b",
        r"\bhttp\b", r"\bwww\b", r"\bclick\b", r"\blink\b",
        r"\bemail\b", r"\bcontact\b", r"\bsentence\b", r"\bpoint by\b",
        r"\bago\b", r"\bupvote\b", r"\bdownvote\b", r"\bthanks\b",
        r"\bappreciate\b", r"\bblog\b", r"\bpost\b", r"\beligible\b",
        r"\bsponsor\b", r"\bvisa\b", r"\bwork in\b", r"\bcomment\b",
        r"\bthread\b", r"\bposted by\b", r"your blog",
    ]
    if any(re.search(p, lower_name) for p in junk_patterns):
        return False

    words = name.split()
    if len(words) > 4:
        connectors = {
            "to", "for", "the", "and", "our", "you", "your", "with", "from",
            "is", "a", "of", "in", "on", "at", "by", "that", "this", "it", "us",
        }
        connector_count = sum(1 for w in words if w.lower() in connectors)
        if connector_count >= 2 or connector_count / len(words) > 0.3:
            return False

    job_titles = [
        r"\bsoftware engineer\b", r"\bfrontend engineer\b", r"\bbackend engineer\b",
        r"\bdata engineer\b", r"\bfull stack engineer\b", r"\bdata scientist\b",
    ]
    if any(re.search(title, lower_name) for title in job_titles):
        return False

    if len(name) < 2 or len(name) > 80:
        return False

    return True