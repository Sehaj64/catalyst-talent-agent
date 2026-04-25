from __future__ import annotations

import re

from .schemas import JobSpec
from .taxonomy import extract_domains, extract_skills


CITY_HINTS = [
    "bengaluru",
    "bangalore",
    "mumbai",
    "pune",
    "delhi",
    "gurgaon",
    "gurugram",
    "hyderabad",
    "chennai",
    "noida",
    "remote",
]


TITLE_PATTERNS = [
    "ai engineer",
    "agentic ai engineer",
    "llm engineer",
    "machine learning engineer",
    "ml engineer",
    "data scientist",
    "backend engineer",
    "full-stack engineer",
    "product engineer",
    "talent intelligence engineer",
]


RESPONSIBILITY_VERBS = (
    "build",
    "design",
    "own",
    "ship",
    "integrate",
    "evaluate",
    "parse",
    "discover",
    "rank",
    "engage",
    "automate",
    "deploy",
)


def parse_job_description(text: str) -> JobSpec:
    normalized = _normalize(text)
    skills = extract_skills(text)
    must_have, nice_to_have = _classify_skills(text, skills)
    domains = extract_domains(text)
    min_years, max_years = _extract_years(normalized)
    title = _infer_title(normalized)
    seniority = _infer_seniority(normalized, min_years, title)
    location = _infer_location(normalized)
    remote_policy = _infer_remote_policy(normalized)
    responsibilities = _extract_responsibilities(text)
    salary_hint = _extract_salary(normalized)
    keywords = _extract_keywords(normalized, skills, domains)

    return JobSpec(
        original_text=text.strip(),
        title=title,
        seniority=seniority,
        min_years=min_years,
        max_years=max_years,
        must_have_skills=must_have,
        nice_to_have_skills=nice_to_have,
        domains=domains,
        responsibilities=responsibilities,
        location=location,
        remote_policy=remote_policy,
        employment_type="contract" if "contract" in normalized else "full-time",
        salary_hint_lpa=salary_hint,
        keywords=keywords,
        recruiter_questions=_recruiter_questions(title, must_have, domains, remote_policy),
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _classify_skills(text: str, skills: list[str]) -> tuple[list[str], list[str]]:
    lowered = text.lower()
    must: list[str] = []
    nice: list[str] = []

    for skill in skills:
        index = lowered.find(skill)
        if index == -1:
            # Search aliases already normalized by the taxonomy.
            index = 0
        context = lowered[max(0, index - 90) : index + 90]
        if any(marker in context for marker in ("nice to have", "good to have", "preferred", "bonus", "plus")):
            nice.append(skill)
        else:
            must.append(skill)

    if not must and nice:
        must.append(nice.pop(0))

    return _dedupe(must), _dedupe(nice)


def _extract_years(text: str) -> tuple[int | None, int | None]:
    range_match = re.search(r"(\d+)\s*[-to]+\s*(\d+)\s*(?:years|yrs|yoe)", text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))

    plus_match = re.search(r"(\d+)\s*\+?\s*(?:years|yrs|yoe)", text)
    if plus_match:
        return int(plus_match.group(1)), None

    return None, None


def _infer_title(text: str) -> str:
    explicit = re.search(r"(?:job title|role|position)\s*[:\-]\s*([a-z0-9 ,/&+-]+)", text)
    if explicit:
        candidate = explicit.group(1).split(".")[0].strip(" -")
        if 3 <= len(candidate) <= 80:
            return candidate.title()

    for pattern in TITLE_PATTERNS:
        if pattern in text:
            return pattern.title().replace("Ml ", "ML ").replace("Ai ", "AI ").replace("Llm", "LLM")

    return "AI Talent Scouting Engineer"


def _infer_seniority(text: str, min_years: int | None, title: str) -> str:
    title_text = title.lower()
    if any(word in text or word in title_text for word in ("principal", "staff", "lead")):
        return "lead"
    if any(word in text or word in title_text for word in ("senior", "sr.")):
        return "senior"
    if any(word in text or word in title_text for word in ("junior", "entry level", "intern")):
        return "junior"
    if min_years is not None:
        if min_years >= 7:
            return "lead"
        if min_years >= 5:
            return "senior"
        if min_years <= 1:
            return "junior"
        return "mid"
    return "unknown"


def _infer_location(text: str) -> str | None:
    for city in CITY_HINTS:
        if city in text:
            return "Bengaluru" if city == "bangalore" else city.title()
    return None


def _infer_remote_policy(text: str) -> str:
    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    if "onsite" in text or "on-site" in text or "office" in text:
        return "onsite"
    return "unknown"


def _extract_responsibilities(text: str) -> list[str]:
    lines = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
    chosen: list[str] = []
    for line in lines:
        lowered = line.lower()
        if len(line) > 180:
            continue
        if any(lowered.startswith(verb) or f" {verb} " in lowered for verb in RESPONSIBILITY_VERBS):
            chosen.append(line)
        elif line.startswith(("-", "*", "•")):
            chosen.append(line.strip(" -*•"))

    if chosen:
        return _dedupe(chosen)[:8]

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    for sentence in sentences:
        lowered = sentence.lower()
        if any(f" {verb} " in f" {lowered} " for verb in RESPONSIBILITY_VERBS):
            chosen.append(sentence.strip())
    return _dedupe(chosen)[:8]


def _extract_salary(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:lpa|lakhs|lakh)", text)
    return int(match.group(1)) if match else None


def _extract_keywords(text: str, skills: list[str], domains: list[str]) -> list[str]:
    role_words = [word for word in ("agent", "shortlist", "outreach", "matching", "ranking", "recruiter", "candidate") if word in text]
    return _dedupe(skills + domains + role_words)[:18]


def _recruiter_questions(title: str, skills: list[str], domains: list[str], remote_policy: str) -> list[str]:
    questions = [
        f"Can the candidate show a working {title.lower()} project with real users or realistic data?",
        "What evidence proves the candidate can ship an end-to-end prototype quickly?",
    ]
    if skills:
        questions.append(f"Can they explain trade-offs around {', '.join(skills[:3])}?")
    if domains:
        questions.append(f"Do they understand domain-specific risks in {domains[0]}?")
    if remote_policy != "unknown":
        questions.append(f"Are they comfortable with the role's {remote_policy} operating model?")
    return questions


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result
