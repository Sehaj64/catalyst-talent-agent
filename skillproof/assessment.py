from __future__ import annotations

import re

from skillproof.extraction import evidence_quality, extract_candidates, normalize
from skillproof.models import Assessment, ScoredAssessment, SkillCandidate, SkillResult


WEAK_PHRASES = (
    "i don't know",
    "not sure",
    "no experience",
    "never used",
    "just basic",
    "only theoretical",
)

DEPTH_SIGNALS = (
    "tradeoff",
    "edge case",
    "latency",
    "cost",
    "scale",
    "security",
    "validation",
    "monitor",
    "debug",
    "metric",
    "baseline",
    "failure",
)

SPECIFICITY_RE = re.compile(r"(\d+%|\d+\s*(users|hours|mins|minutes|seconds|x|tables|apis|models|projects))", re.I)


def build_assessment(jd_text: str, resume_text: str) -> Assessment:
    skills = extract_candidates(jd_text, resume_text)
    return Assessment(jd_text=jd_text, resume_text=resume_text, skills=skills)


def answer_key(skill_name: str, prompt: str) -> str:
    return f"{skill_name}::{prompt}"


def score_answer(text: str, signals: tuple[str, ...]) -> tuple[int, int, int, list[str]]:
    cleaned = normalize(text)
    if not cleaned:
        return 0, 0, 0, ["no_answer"]

    words = cleaned.split()
    reason_codes: list[str] = []
    length_score = min(12, max(0, len(words) // 8))
    signal_hits = sum(1 for signal in signals if signal.lower() in cleaned)
    signal_score = min(15, signal_hits * 3)
    specificity_score = min(8, len(SPECIFICITY_RE.findall(text)) * 4)
    practical_score = 6 if any(word in cleaned for word in ("built", "implemented", "debugged", "deployed", "designed", "analyzed")) else 0
    weak_penalty = 12 if any(phrase in cleaned for phrase in WEAK_PHRASES) else 0

    assessment = max(0, min(45, length_score + signal_score + specificity_score + practical_score - weak_penalty))

    depth_hits = sum(1 for signal in DEPTH_SIGNALS if signal in cleaned)
    depth = min(20, depth_hits * 4 + (4 if "because" in cleaned else 0))
    confidence = min(10, 4 + signal_hits + (2 if specificity_score else 0) - (4 if weak_penalty else 0))
    confidence = max(0, confidence)

    if signal_hits:
        reason_codes.append("uses_skill_specific_language")
    if specificity_score:
        reason_codes.append("mentions_measurable_outcome")
    if practical_score:
        reason_codes.append("gives_practical_example")
    if depth >= 8:
        reason_codes.append("discusses_tradeoffs_or_failures")
    if weak_penalty:
        reason_codes.append("low_confidence_language")

    return assessment, depth, confidence, reason_codes


def classify(score: int) -> str:
    if score >= 85:
        return "Strong"
    if score >= 70:
        return "Ready with checks"
    if score >= 50:
        return "Developing"
    return "Gap"


def learning_plan(skill: SkillCandidate, level: str) -> str:
    if level == "Strong":
        return "No immediate learning plan needed. Use this skill as assessment evidence and ask one advanced calibration question."

    if level == "Ready with checks":
        time = "3-5 focused hours"
        priority = "Low"
    elif level == "Developing":
        time = "1-2 weeks"
        priority = "Medium"
    else:
        time = "2-4 weeks"
        priority = "High"

    adjacent = ", ".join(skill.adjacent_skills[:2]) if skill.adjacent_skills else "related fundamentals"
    resources = "; ".join(skill.resources[:2])
    return (
        f"Priority: {priority}. Estimated time to job-ready: {time}. "
        f"Start from adjacent strengths in {adjacent}. "
        f"Resources: {resources}. "
        f"Proof task: build a small role-relevant artifact demonstrating {skill.name} and document the tradeoffs."
    )


def score_skill(skill: SkillCandidate, answers: dict[str, str]) -> SkillResult:
    resume_score = evidence_quality(skill.resume_evidence)
    answer_scores: list[int] = []
    depth_scores: list[int] = []
    confidence_scores: list[int] = []
    reason_codes = []

    for question in skill.questions:
        key = answer_key(skill.name, question.prompt)
        assessment, depth, confidence, reasons = score_answer(answers.get(key, ""), question.signals)
        answer_scores.append(assessment)
        depth_scores.append(depth)
        confidence_scores.append(confidence)
        reason_codes.extend(reasons)

    assessment_score = round(sum(answer_scores) / max(1, len(answer_scores)))
    depth_score = round(sum(depth_scores) / max(1, len(depth_scores)))
    confidence_score = round(sum(confidence_scores) / max(1, len(confidence_scores)))
    total = min(100, resume_score + assessment_score + depth_score + confidence_score)
    level = classify(total)

    if resume_score >= 18:
        reason_codes.append("strong_resume_evidence")
    elif resume_score == 0:
        reason_codes.append("missing_resume_evidence")
    else:
        reason_codes.append("partial_resume_evidence")

    risk_flags = []
    if skill.criticality == "High" and total < 70:
        risk_flags.append("Critical JD skill below readiness threshold")
    if resume_score == 0 and skill.criticality in {"High", "Medium"}:
        risk_flags.append("Required skill has no resume evidence")
    if assessment_score < 18:
        risk_flags.append("Assessment answers lack concrete detail")

    return SkillResult(
        name=skill.name,
        category=skill.category,
        criticality=skill.criticality,
        total_score=total,
        level=level,
        resume_evidence_score=resume_score,
        assessment_score=assessment_score,
        depth_score=depth_score,
        confidence_score=confidence_score,
        reason_codes=sorted(set(reason_codes)),
        risk_flags=risk_flags,
        evidence=skill.resume_evidence[:3],
        learning_plan=learning_plan(skill, level),
        adjacent_skills=skill.adjacent_skills[:3],
        resources=skill.resources[:3],
    )


def recommendation(overall: int, results: list[SkillResult]) -> str:
    high_risks = [result for result in results if result.criticality == "High" and result.total_score < 70]
    if overall >= 82 and not high_risks:
        return "Candidate shows strong proficiency across the required skills. Use one advanced calibration question per core skill."
    if overall >= 65:
        return "Candidate has usable foundations but needs targeted upskilling on the flagged skill gaps."
    return "Candidate needs foundation work before being considered ready for this JD. Follow the learning plan and reassess."


def score_assessment(assessment: Assessment, answers: dict[str, str]) -> ScoredAssessment:
    results = [score_skill(skill, answers) for skill in assessment.skills]
    if not results:
        return ScoredAssessment([], 0, "No relevant skills found. Recheck input quality.", [], [])

    weighted_total = 0
    weight_sum = 0
    weights = {"High": 3, "Medium": 2, "Resume-only": 1}
    for result in results:
        weight = weights.get(result.criticality, 1)
        weighted_total += result.total_score * weight
        weight_sum += weight
    overall = round(weighted_total / weight_sum)

    strongest = [result.name for result in sorted(results, key=lambda item: item.total_score, reverse=True)[:3]]
    risks = []
    for result in results:
        risks.extend([f"{result.name}: {flag}" for flag in result.risk_flags])

    return ScoredAssessment(
        skill_results=results,
        overall_score=overall,
        recommendation=recommendation(overall, results),
        strongest_skills=strongest,
        highest_risks=risks[:5],
    )
