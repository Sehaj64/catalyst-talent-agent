from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import quote_plus

from skillproof.models import Question, SkillCandidate
from skillproof.taxonomy import CRITICALITY_CUES, SKILLS


WORD_RE = re.compile(r"[A-Za-z0-9+#./-]+")

SKILL_SECTION_CUES = (
    "required",
    "requirements",
    "required skills",
    "must have",
    "must-have",
    "preferred",
    "nice to have",
    "qualifications",
    "skills",
    "technical skills",
    "tools",
    "tech stack",
    "experience with",
    "knowledge of",
    "proficiency in",
    "familiarity with",
    "working with",
    "work with",
)

DYNAMIC_HEADER_CAPTURE_RE = re.compile(
    r"\b(?:required skills?|requirements?|preferred|nice to have|"
    r"qualifications?|skills?|technical skills?|tools?|tech stack)\b\s*[:\-]\s*([^.!?\n]+)",
    re.I,
)

DYNAMIC_PHRASE_CAPTURE_RE = re.compile(
    r"\b(?:must[- ]have|experience with|knowledge of|proficiency in|"
    r"familiarity with|working with|work with)\b\s*[:\-]?\s*([^.!?\n]+)",
    re.I,
)

SECTION_HEADER_RE = re.compile(
    r"\b(?:required skills?|requirements?|preferred|nice to have|"
    r"qualifications?|skills?|technical skills?|tools?|tech stack)\b\s*[:\-]",
    re.I,
)

SPLIT_RE = re.compile(r"[,;|•]+")

LEADING_QUALIFIERS_RE = re.compile(
    r"^(?:and|or|for|with|plus|strong|solid|deep|hands[- ]on|working|basic|advanced|"
    r"practical|good|excellent|clear|demonstrated|required|preferred|must[- ]have|"
    r"nice[- ]to[- ]have|knowledge of|experience with|familiarity with|proficiency in|"
    r"ability to|understanding of)\s+",
    re.I,
)

TRAILING_QUALIFIERS_RE = re.compile(
    r"\s+(?:skills?|experience|knowledge|understanding|basics|fundamentals|tools?|workflows?)$",
    re.I,
)

STOP_PHRASES = {
    "job description",
    "candidate",
    "resume",
    "email",
    "deadline",
    "salary",
    "location",
    "apply",
    "team",
    "role",
    "responsibilities",
    "requirements",
    "qualifications",
    "business requirements",
    "business outcomes",
    "cost reduction",
    "accuracy lift",
    "workflow throughput",
    "user-facing software",
    "hiring teams",
    "for hiring teams",
    "product",
    "product workflow",
}

STOP_FRAGMENTS = (
    "years of",
    "minimum",
    "bachelor",
    "degree",
    "excellent written",
    "excellent verbal",
    "warm regards",
    "submit by",
    "registration",
    "hackathon",
    "project site",
)

GENERIC_SINGLE_WORDS = {
    "business",
    "dashboard",
    "dashboards",
    "process",
    "product",
    "reporting",
    "software",
    "system",
    "systems",
    "tool",
    "tools",
    "workflow",
}

SPECIAL_TOKEN_CASE = {
    "abm": "ABM",
    "api": "API",
    "apis": "APIs",
    "ats": "ATS",
    "aws": "AWS",
    "b2b": "B2B",
    "b2c": "B2C",
    "bi": "BI",
    "ci/cd": "CI/CD",
    "cpa": "CPA",
    "crm": "CRM",
    "css": "CSS",
    "cvr": "CVR",
    "erp": "ERP",
    "etl": "ETL",
    "figma": "Figma",
    "ga4": "GA4",
    "gdpr": "GDPR",
    "html": "HTML",
    "kpi": "KPI",
    "kpis": "KPIs",
    "okr": "OKR",
    "okrs": "OKRs",
    "p&l": "P&L",
    "qa": "QA",
    "roi": "ROI",
    "saas": "SaaS",
    "seo": "SEO",
    "sop": "SOP",
    "sql": "SQL",
    "ui": "UI",
    "ux": "UX",
}

DYNAMIC_CATEGORY_KEYWORDS = (
    ("Marketing / Growth", ("seo", "ads", "campaign", "conversion", "content", "crm", "email marketing", "growth")),
    ("Sales / Customer Operations", ("salesforce", "hubspot", "pipeline", "account", "lead", "customer success")),
    ("Cloud / DevOps", ("aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ci/cd", "devops")),
    ("Data / Analytics", ("analytics", "forecast", "forecasting", "tableau", "power bi", "looker", "excel", "dashboard")),
    ("Operations / Supply Chain", ("inventory", "supply", "vendor", "procurement", "logistics", "demand planning")),
    ("Product / Design", ("figma", "wireframe", "prototype", "user research", "ux", "ui", "roadmap")),
    ("Finance / HR", ("payroll", "accounting", "finance", "reconciliation", "recruiting", "onboarding")),
    ("Healthcare / Compliance", ("clinical", "healthcare", "hipaa", "icd", "medical", "compliance")),
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def contains_alias(text: str, alias: str) -> bool:
    alias_norm = normalize(alias)
    if len(alias_norm) <= 3:
        return re.search(rf"(?<![a-z0-9]){re.escape(alias_norm)}(?![a-z0-9])", text) is not None
    return alias_norm in text


def meaningful_tokens(text: str) -> list[str]:
    return [
        token
        for token in WORD_RE.findall(normalize(text))
        if len(token) > 2 and token not in {"and", "for", "the", "with", "from", "into", "using"}
    ]


def known_alias_norms() -> set[str]:
    aliases = set()
    for skill_name, config in SKILLS.items():
        aliases.add(normalize(skill_name))
        aliases.update(normalize(alias) for alias in config["aliases"])
    return aliases


def is_known_skill_candidate(candidate: str) -> bool:
    candidate_norm = normalize(candidate)
    aliases = known_alias_norms()
    if candidate_norm in aliases:
        return True
    candidate_tokens = set(meaningful_tokens(candidate_norm))
    for alias in aliases:
        alias_tokens = set(meaningful_tokens(alias))
        if not alias_tokens:
            continue
        if len(alias_tokens) >= 2 and alias_tokens.issubset(candidate_tokens):
            return True
        if len(alias) >= 4 and alias in candidate_norm and len(candidate_tokens) <= 3:
            return True
    return False


def find_skill_mentions(text: str) -> dict[str, list[str]]:
    text_norm = normalize(text)
    sentences = split_sentences(text)
    mentions: dict[str, list[str]] = defaultdict(list)
    for skill_name, config in SKILLS.items():
        aliases = [skill_name, *config["aliases"]]
        if not any(contains_alias(text_norm, alias) for alias in aliases):
            continue
        for sentence in sentences:
            sentence_norm = normalize(sentence)
            if any(contains_alias(sentence_norm, alias) for alias in aliases):
                mentions[skill_name].append(sentence[:280])
    return dict(mentions)


def strip_candidate(raw: str) -> str:
    candidate = raw.strip().strip(":-–—[](){}.")
    candidate = re.sub(r"^\d+\+?\s*(?:years?|yrs?)\s+(?:of\s+)?", "", candidate, flags=re.I)
    previous = None
    while previous != candidate:
        previous = candidate
        candidate = LEADING_QUALIFIERS_RE.sub("", candidate).strip()
    candidate = TRAILING_QUALIFIERS_RE.sub("", candidate).strip()
    candidate = re.sub(r"\s+", " ", candidate)
    return candidate.strip(":-–—[](){}.")


def display_candidate_name(candidate: str) -> str:
    words = []
    for word in candidate.split():
        stripped = word.strip()
        key = stripped.lower()
        if key in SPECIAL_TOKEN_CASE:
            words.append(SPECIAL_TOKEN_CASE[key])
        elif re.fullmatch(r"[A-Z0-9+#./&-]{2,}", stripped):
            words.append(stripped)
        elif re.search(r"[+#./&-]", stripped):
            words.append(stripped)
        else:
            words.append(stripped[:1].upper() + stripped[1:].lower())
    return " ".join(words)


def plausible_dynamic_candidate(candidate: str) -> bool:
    candidate_norm = normalize(candidate)
    tokens = meaningful_tokens(candidate_norm)
    if not tokens or len(candidate_norm) < 2:
        return False
    if len(tokens) > 5:
        return False
    if len(tokens) == 1 and tokens[0] in GENERIC_SINGLE_WORDS:
        return False
    if candidate_norm in STOP_PHRASES:
        return False
    if any(fragment in candidate_norm for fragment in STOP_FRAGMENTS):
        return False
    if candidate_norm.startswith(("build ", "work ", "turning ", "own ", "manage the ", "support ")):
        return False
    if is_known_skill_candidate(candidate_norm):
        return False
    return True


def chunk_skill_text(text: str) -> list[str]:
    normalized = re.sub(r"\b(?:including|such as|like)\b", ",", text, flags=re.I)
    chunks = []
    for part in SPLIT_RE.split(normalized):
        part = part.strip()
        if not part:
            continue
        if len(part.split()) <= 8:
            pieces = re.split(r"\s+(?:and|or)\s+", part, flags=re.I)
        else:
            pieces = [part]
        chunks.extend(piece.strip() for piece in pieces if piece.strip())
    return chunks


def skill_windows(text: str) -> list[str]:
    windows: list[str] = []
    lines = [line.strip(" \t-*•") for line in text.splitlines()]
    in_skill_section = False
    for line in lines:
        if not line:
            in_skill_section = False
            continue
        line_norm = normalize(line)
        has_cue = SECTION_HEADER_RE.search(line_norm) is not None
        if has_cue:
            in_skill_section = True
            if ":" in line:
                windows.append(line.split(":", 1)[1])
            else:
                windows.append(line)
            continue
        if in_skill_section:
            windows.append(line)

    for match in DYNAMIC_HEADER_CAPTURE_RE.finditer(text):
        windows.append(match.group(1))
    for match in DYNAMIC_PHRASE_CAPTURE_RE.finditer(text):
        windows.append(match.group(1))
    return windows


def dynamic_category(skill_name: str) -> str:
    skill_norm = normalize(skill_name)
    for category, keywords in DYNAMIC_CATEGORY_KEYWORDS:
        if any(keyword in skill_norm for keyword in keywords):
            return category
    return "Role-specific skill"


def dynamic_adjacent_skills(skill_name: str) -> list[str]:
    skill_norm = normalize(skill_name)
    if any(term in skill_norm for term in ("seo", "ads", "campaign", "conversion", "content")):
        return ["Analytics", "Experiment design", "Customer research"]
    if any(term in skill_norm for term in ("salesforce", "hubspot", "crm", "pipeline")):
        return ["Data hygiene", "Workflow automation", "Stakeholder reporting"]
    if any(term in skill_norm for term in ("forecast", "inventory", "vendor", "procurement", "logistics")):
        return ["Spreadsheet modeling", "Operations metrics", "Scenario planning"]
    if any(term in skill_norm for term in ("aws", "kubernetes", "docker", "terraform", "ci/cd")):
        return ["Observability", "Incident response", "Infrastructure documentation"]
    if any(term in skill_norm for term in ("figma", "ux", "ui", "prototype", "user research")):
        return ["Usability testing", "Product thinking", "Design critique"]
    return ["Domain fundamentals", "Measurement and reporting", "Documentation"]


def dynamic_resources(skill_name: str) -> list[str]:
    query = quote_plus(skill_name)
    return [
        f"Official docs or vendor quickstart for {skill_name} (2 hrs): search the primary tool/vendor documentation and complete one quickstart.",
        f"Coursera course search for {skill_name} (4-8 hrs): https://www.coursera.org/search?query={query}",
        f"Class Central course search for {skill_name} (4-8 hrs): https://www.classcentral.com/search?q={query}",
        f"Unacademy topic search for {skill_name} if the skill is domain/exam aligned (2-4 hrs): https://unacademy.com/search?query={query}",
    ]


def dynamic_questions(skill_name: str) -> list[Question]:
    skill_signals = tuple(meaningful_tokens(skill_name)[:4])
    proof_signals = ("project", "artifact", "metric", "tradeoff", "failure", "validate")
    return [
        Question(
            prompt=(
                f"Describe one real project or task where you used {skill_name}. "
                "What problem did you solve, what tools or process did you use, and what measurable result came out?"
            ),
            difficulty="Practical",
            signals=skill_signals + proof_signals,
        ),
        Question(
            prompt=(
                f"If this JD required {skill_name} tomorrow, what proof artifact would you build in one week, "
                "and how would you validate quality or business impact?"
            ),
            difficulty="Scenario",
            signals=skill_signals + ("artifact", "validate", "quality", "impact", "stakeholder"),
        ),
    ]


def find_dynamic_skill_mentions(text: str) -> dict[str, list[str]]:
    mentions: dict[str, list[str]] = defaultdict(list)
    for window in skill_windows(text):
        for chunk in chunk_skill_text(window):
            candidate = strip_candidate(chunk)
            if not plausible_dynamic_candidate(candidate):
                continue
            name = display_candidate_name(candidate)
            if name not in mentions:
                mentions[name] = []
            mentions[name].append(window.strip()[:280])
    return dict(mentions)


def dynamic_sentence_matches(sentence: str, skill_name: str) -> bool:
    sentence_norm = normalize(sentence)
    skill_norm = normalize(skill_name)
    if contains_alias(sentence_norm, skill_norm):
        return True
    tokens = meaningful_tokens(skill_norm)
    return len(tokens) >= 2 and all(contains_alias(sentence_norm, token) for token in tokens)


def find_dynamic_resume_evidence(text: str, skill_name: str) -> list[str]:
    snippets = []
    for sentence in split_sentences(text):
        if dynamic_sentence_matches(sentence, skill_name):
            snippets.append(sentence[:280])
    return snippets


def infer_criticality(skill_mentions: list[str]) -> str:
    combined = normalize(" ".join(skill_mentions))
    for level, cues in CRITICALITY_CUES.items():
        if any(cue in combined for cue in cues):
            return level
    return "Medium"


def evidence_quality(snippets: list[str]) -> int:
    if not snippets:
        return 0
    action_words = (
        "built",
        "created",
        "designed",
        "implemented",
        "deployed",
        "optimized",
        "improved",
        "automated",
        "analyzed",
        "led",
    )
    metric_re = re.compile(r"(\d+%|\d+\s*(users|hours|mins|minutes|seconds|x|projects|models|apis))", re.I)
    score = min(14, 6 + len(snippets) * 4)
    joined = normalize(" ".join(snippets))
    score += min(8, sum(3 for word in action_words if word in joined))
    score += min(5, len(metric_re.findall(" ".join(snippets))) * 3)
    return min(25, score)


def extract_candidates(jd_text: str, resume_text: str) -> list[SkillCandidate]:
    jd_mentions = find_skill_mentions(jd_text)
    resume_mentions = find_skill_mentions(resume_text)
    all_names = set(jd_mentions) | set(resume_mentions)
    dynamic_jd_mentions = find_dynamic_skill_mentions(jd_text)

    candidates: list[SkillCandidate] = []
    for name in sorted(all_names):
        config = SKILLS[name]
        criticality = infer_criticality(jd_mentions.get(name, []))
        if name not in jd_mentions:
            criticality = "Resume-only"
        candidates.append(
            SkillCandidate(
                name=name,
                category=config["category"],
                criticality=criticality,
                jd_mentions=jd_mentions.get(name, []),
                resume_evidence=resume_mentions.get(name, []),
                questions=list(config["questions"]),
                adjacent_skills=list(config["adjacent"]),
                resources=list(config["resources"]),
            )
        )

    known_names = {normalize(name) for name in all_names}
    for name, mentions in dynamic_jd_mentions.items():
        if normalize(name) in known_names:
            continue
        candidates.append(
            SkillCandidate(
                name=name,
                category=dynamic_category(name),
                criticality=infer_criticality(mentions),
                jd_mentions=mentions,
                resume_evidence=find_dynamic_resume_evidence(resume_text, name),
                questions=dynamic_questions(name),
                adjacent_skills=dynamic_adjacent_skills(name),
                resources=dynamic_resources(name),
            )
        )

    priority = {"High": 0, "Medium": 1, "Resume-only": 2}
    candidates.sort(
        key=lambda skill: (
            priority.get(skill.criticality, 3),
            -evidence_quality(skill.resume_evidence),
            0 if skill.category != "Role-specific skill" else 1,
            skill.name,
        )
    )
    return candidates[:12]
