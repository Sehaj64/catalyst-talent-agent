from __future__ import annotations

from .schemas import CandidateProfile, JobSpec, ScoreBreakdown
from .taxonomy import normalize_skill, related_for


SENIORITY_TARGETS = {
    "junior": (0, 2),
    "mid": (2, 5),
    "senior": (5, 9),
    "lead": (7, 14),
    "unknown": (0, 20),
}


def score_match(candidate: CandidateProfile, job_spec: JobSpec) -> dict[str, object]:
    candidate_skills = {normalize_skill(skill) for skill in candidate.skills + candidate.tools}
    must = job_spec.must_have_skills
    nice = job_spec.nice_to_have_skills

    must_score, matched_must, related_map, missing = _score_skill_list(must, candidate_skills)
    nice_score, matched_nice, nice_related, _ = _score_skill_list(nice, candidate_skills)
    related_map.update({key: value for key, value in nice_related.items() if key not in related_map})

    if not must:
        must_score = 0.70
    if not nice:
        nice_score = 0.60

    skill_alignment = (must_score * 45) + (nice_score * 10)
    seniority_fit = _score_seniority(candidate, job_spec)
    domain_fit = _score_domain(candidate, job_spec)
    evidence_depth = _score_evidence(candidate, job_spec)
    logistics_fit = _score_logistics(candidate, job_spec)
    differentiation = _score_differentiation(candidate, job_spec)

    total = round(
        min(
            100,
            skill_alignment + seniority_fit + domain_fit + evidence_depth + logistics_fit + differentiation,
        ),
        1,
    )

    matched = sorted(set(matched_must + matched_nice))
    explanation = _explain(candidate, job_spec, total, matched, missing, related_map)

    return {
        "score": total,
        "matched_skills": matched,
        "related_skills": related_map,
        "missing_skills": missing,
        "breakdown": ScoreBreakdown(
            skill_alignment=round(skill_alignment, 1),
            seniority_fit=round(seniority_fit, 1),
            domain_fit=round(domain_fit, 1),
            evidence_depth=round(evidence_depth, 1),
            logistics_fit=round(logistics_fit, 1),
            differentiation=round(differentiation, 1),
        ),
        "explanation": explanation,
        "outreach_hook": _outreach_hook(candidate, job_spec, matched),
        "counterfactual": _counterfactual(candidate, job_spec, missing),
    }


def decision_label(combined_score: float, match_score: float, interest_score: float) -> str:
    if combined_score >= 86 and match_score >= 78 and interest_score >= 75:
        return "Priority shortlist"
    if combined_score >= 76:
        return "Shortlist"
    if combined_score >= 65:
        return "Warm backup"
    return "Hold"


def _score_skill_list(required: list[str], candidate_skills: set[str]) -> tuple[float, list[str], dict[str, list[str]], list[str]]:
    if not required:
        return 0.0, [], {}, []

    total = 0.0
    matched: list[str] = []
    related_map: dict[str, list[str]] = {}
    missing: list[str] = []

    for skill in required:
        normalized = normalize_skill(skill)
        if normalized in candidate_skills:
            total += 1.0
            matched.append(normalized)
            continue

        related = related_for(normalized, candidate_skills)
        if related:
            total += 0.55
            related_map[normalized] = related[:4]
        else:
            missing.append(normalized)

    return total / len(required), matched, related_map, missing


def _score_seniority(candidate: CandidateProfile, job_spec: JobSpec) -> float:
    target_min, target_max = SENIORITY_TARGETS[job_spec.seniority]
    if job_spec.min_years is not None:
        target_min = job_spec.min_years
    if job_spec.max_years is not None:
        target_max = job_spec.max_years

    years = candidate.years_experience
    if target_min <= years <= target_max:
        return 15.0
    if years < target_min:
        return max(4.0, 15.0 - ((target_min - years) * 3.2))
    if years <= target_max + 3:
        return 12.0
    return 9.0


def _score_domain(candidate: CandidateProfile, job_spec: JobSpec) -> float:
    if not job_spec.domains:
        return 7.0
    overlap = len(set(candidate.domains) & set(job_spec.domains))
    if overlap == 0:
        return 3.5 if "enterprise" in candidate.domains or "saas" in candidate.domains else 1.5
    return min(10.0, 4.0 + (overlap / len(job_spec.domains)) * 6.0)


def _score_evidence(candidate: CandidateProfile, job_spec: JobSpec) -> float:
    text = " ".join(candidate.projects + candidate.achievements + candidate.evidence).lower()
    signal_terms = job_spec.must_have_skills + job_spec.domains + ["production", "shipped", "demo", "evaluation", "rank", "shortlist"]
    hits = sum(1 for term in signal_terms if term and term.lower() in text)
    artifact_bonus = min(len(candidate.projects) + len(candidate.evidence), 5)
    return min(12.0, hits * 1.2 + artifact_bonus * 1.1)


def _score_logistics(candidate: CandidateProfile, job_spec: JobSpec) -> float:
    score = 4.0
    if job_spec.remote_policy == "remote" and candidate.open_to_remote:
        score += 2.0
    elif job_spec.location and job_spec.location in candidate.target_locations:
        score += 2.0
    elif job_spec.remote_policy in ("unknown", "hybrid") and (candidate.open_to_remote or job_spec.location in candidate.target_locations):
        score += 1.5

    if candidate.notice_period_days <= 30:
        score += 1.4
    elif candidate.notice_period_days <= 45:
        score += 0.8

    if job_spec.salary_hint_lpa and candidate.salary_expectation_lpa:
        if candidate.salary_expectation_lpa <= job_spec.salary_hint_lpa:
            score += 0.6
        elif candidate.salary_expectation_lpa > job_spec.salary_hint_lpa * 1.25:
            score -= 1.0
    else:
        score += 0.4

    return max(0.0, min(8.0, score))


def _score_differentiation(candidate: CandidateProfile, job_spec: JobSpec) -> float:
    text = " ".join(candidate.skills + candidate.projects + candidate.achievements + candidate.evidence + candidate.domains).lower()
    differentiators = [
        "agent",
        "evaluation",
        "audit",
        "privacy",
        "human",
        "recruit",
        "ranking",
        "shortlist",
        "production",
        "demo",
    ]
    hits = sum(1 for term in differentiators if term in text)
    if "hrtech" in job_spec.domains and "hrtech" in candidate.domains:
        hits += 2
    return min(10.0, hits * 1.15)


def _explain(
    candidate: CandidateProfile,
    job_spec: JobSpec,
    total: float,
    matched: list[str],
    missing: list[str],
    related_map: dict[str, list[str]],
) -> str:
    strengths = []
    if matched:
        strengths.append(f"direct coverage in {', '.join(matched[:5])}")
    if related_map:
        strengths.append(f"adjacent depth for {', '.join(list(related_map)[:3])}")
    if set(candidate.domains) & set(job_spec.domains):
        strengths.append(f"domain overlap in {', '.join(sorted(set(candidate.domains) & set(job_spec.domains)))}")
    if not strengths:
        strengths.append("general engineering evidence but limited direct overlap")

    gap_text = f" Main gaps: {', '.join(missing[:4])}." if missing else " No critical skill gap detected."
    return f"{candidate.name} scores {total}/100 because of " + "; ".join(strengths) + "." + gap_text


def _outreach_hook(candidate: CandidateProfile, job_spec: JobSpec, matched: list[str]) -> str:
    evidence = candidate.evidence[0] if candidate.evidence else candidate.projects[0]
    matched_text = ", ".join(matched[:3]) if matched else job_spec.title
    return f"Lead with their {matched_text} work: {evidence}"


def _counterfactual(candidate: CandidateProfile, job_spec: JobSpec, missing: list[str]) -> str:
    if missing:
        return f"Would move up materially if they can show hands-on evidence for {missing[0]}."
    if candidate.notice_period_days > 45:
        return "Would move up if availability can be negotiated below 45 days."
    if job_spec.domains and not (set(candidate.domains) & set(job_spec.domains)):
        return f"Would move up if they can show context in {job_spec.domains[0]}."
    return "Already has the core evidence; next improvement is validating production depth in a live conversation."
