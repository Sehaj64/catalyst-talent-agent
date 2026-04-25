from __future__ import annotations

import re

from .schemas import CandidateProfile
from .taxonomy import extract_domains, extract_skills


def parse_candidate_resumes(text: str | None) -> list[CandidateProfile]:
    if not text or not text.strip():
        return []

    blocks = _split_resumes(text)
    candidates: list[CandidateProfile] = []
    for index, block in enumerate(blocks, start=1):
        if len(block.strip()) < 40:
            continue
        candidates.append(_parse_one(block, index))
    return candidates


def _split_resumes(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").strip()
    if "\n---" in normalized or "\n###" in normalized:
        return [part.strip() for part in re.split(r"\n(?:---+|###+)\n", normalized) if part.strip()]

    matches = list(re.finditer(r"(?im)^name\s*:\s*", normalized))
    if len(matches) > 1:
        blocks = []
        for idx, match in enumerate(matches):
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
            blocks.append(normalized[match.start() : end].strip())
        return blocks

    return [normalized]


def _parse_one(block: str, index: int) -> CandidateProfile:
    name = _field(block, "name") or _first_name_like_line(block) or f"Imported Candidate {index}"
    title = (
        _field(block, "current title")
        or _field(block, "title")
        or _field(block, "role")
        or _infer_title(block)
    )
    years = _years(block)
    location = _field(block, "location") or "Not specified"
    skills = extract_skills(block)
    domains = extract_domains(block)
    salary = _salary(block)
    notice = _notice(block)
    remote = bool(re.search(r"(?i)\b(remote|hybrid|work from home|wfh)\b", block))
    evidence = _evidence(block)
    projects = _section_items(block, "projects") or evidence[:2] or ["Resume mentions relevant project work."]
    achievements = _section_items(block, "achievements") or _section_items(block, "impact") or []

    if not skills:
        skills = ["python"] if re.search(r"(?i)\bpython\b", block) else ["general engineering"]
    if not domains:
        domains = ["enterprise"] if re.search(r"(?i)\benterprise|b2b|saas\b", block) else []

    return CandidateProfile(
        candidate_id=f"resume-{index:03d}",
        name=_clean_name(name),
        headline=_headline(block, title),
        current_title=title,
        years_experience=years,
        location=location,
        target_locations=_target_locations(block, location, remote),
        open_to_remote=remote,
        salary_expectation_lpa=salary,
        notice_period_days=notice,
        skills=skills,
        tools=_tools(block),
        domains=domains,
        projects=projects[:4],
        achievements=achievements[:4],
        evidence=evidence[:5],
        preferences=_preferences(block, remote),
        interest_drivers=_interest_drivers(block, skills, domains),
        reservations=_reservations(block),
        responsiveness=0.74 + min(len(evidence), 4) * 0.04,
        public_source="User-provided resume text",
    )


def _field(text: str, label: str) -> str | None:
    pattern = rf"(?im)^\s*{re.escape(label)}\s*[:\-]\s*(.+?)\s*$"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def _first_name_like_line(text: str) -> str | None:
    for raw in text.splitlines()[:5]:
        line = raw.strip()
        if not line or ":" in line or len(line) > 60:
            continue
        if re.match(r"^[A-Z][A-Za-z .'-]+$", line):
            return line
    return None


def _clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" -")


def _infer_title(text: str) -> str:
    title_words = [
        "AI Engineer",
        "LLM Engineer",
        "Machine Learning Engineer",
        "ML Engineer",
        "Data Scientist",
        "Backend Engineer",
        "Full Stack Engineer",
        "Recruiter",
        "Talent Sourcer",
    ]
    lowered = text.lower()
    for title in title_words:
        if title.lower() in lowered:
            return title
    return "Imported Candidate"


def _years(text: str) -> float:
    match = re.search(r"(?i)(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs|yoe)", text)
    return float(match.group(1)) if match else 2.0


def _salary(text: str) -> int | None:
    match = re.search(r"(?i)(\d+)\s*(?:lpa|lakhs|lakh)", text)
    return int(match.group(1)) if match else None


def _notice(text: str) -> int:
    match = re.search(r"(?i)(\d+)\s*(?:days?)\s*(?:notice|np|availability)", text)
    if match:
        return int(match.group(1))
    if re.search(r"(?i)\bimmediate\b", text):
        return 0
    return 30


def _target_locations(text: str, location: str, remote: bool) -> list[str]:
    targets = [location] if location and location != "Not specified" else []
    for city in ["Bengaluru", "Pune", "Mumbai", "Hyderabad", "Chennai", "Delhi", "Remote"]:
        if city.lower() in text.lower() and city not in targets:
            targets.append(city)
    if remote and "Remote" not in targets:
        targets.append("Remote")
    return targets or ["Remote"]


def _tools(text: str) -> list[str]:
    tools = []
    for tool in ["FastAPI", "LangGraph", "LangChain", "LlamaIndex", "Qdrant", "Pinecone", "FAISS", "PostgreSQL", "Docker", "AWS", "React"]:
        if tool.lower() in text.lower():
            tools.append(tool)
    return tools


def _section_items(text: str, section: str) -> list[str]:
    pattern = rf"(?ims)^\s*{re.escape(section)}\s*[:\-]?\s*$([\s\S]*?)(?=^\s*[A-Za-z ]{{3,30}}\s*[:\-]?\s*$|\Z)"
    match = re.search(pattern, text)
    if not match:
        return []
    return _bullet_items(match.group(1))


def _evidence(text: str) -> list[str]:
    items = []
    for section in ["projects", "experience", "achievements", "impact"]:
        items.extend(_section_items(text, section))
    if items:
        return _dedupe(items)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    useful = [sentence.strip(" -") for sentence in sentences if len(sentence.strip()) > 40]
    return useful[:5] or ["Resume provided but evidence is sparse."]


def _bullet_items(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip(" -•*\t")
        if len(line) >= 12:
            lines.append(line)
    return lines


def _headline(text: str, title: str) -> str:
    summary = _field(text, "summary")
    if summary:
        return summary[:140]
    skills = extract_skills(text)
    if skills:
        return f"{title} with {', '.join(skills[:4])}"
    return title


def _preferences(text: str, remote: bool) -> list[str]:
    prefs = []
    if remote:
        prefs.append("open to remote or hybrid")
    if re.search(r"(?i)\bstartup|early stage|ownership\b", text):
        prefs.append("likes ownership and startup pace")
    if re.search(r"(?i)\brecruit|talent|hiring\b", text):
        prefs.append("interested in recruiting technology")
    return prefs or ["preferences not explicit"]


def _interest_drivers(text: str, skills: list[str], domains: list[str]) -> list[str]:
    drivers = []
    lowered = text.lower()
    for term in ["agentic ai", "ai agents", "recruiting domain", "candidate engagement", "fast shipping", "ownership", "remote work"]:
        if term in lowered:
            drivers.append(term)
    drivers.extend(skills[:2])
    drivers.extend(domains[:1])
    return _dedupe(drivers)[:5] or ["role fit"]


def _reservations(text: str) -> list[str]:
    reservations = []
    if re.search(r"(?i)\bvisa|relocat|compensation|salary|notice\b", text):
        reservations.append("validate logistics and expectations")
    if re.search(r"(?i)\bnot actively|passive\b", text):
        reservations.append("candidate may be passive")
    return reservations or ["no explicit reservation in resume"]


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result
