from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Question:
    prompt: str
    difficulty: str
    signals: tuple[str, ...]


@dataclass
class SkillCandidate:
    name: str
    category: str
    criticality: str
    jd_mentions: list[str] = field(default_factory=list)
    resume_evidence: list[str] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    adjacent_skills: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)


@dataclass
class Assessment:
    jd_text: str
    resume_text: str
    skills: list[SkillCandidate]
    seniority: str = "Mid-Level"


@dataclass
class SkillResult:
    name: str
    category: str
    criticality: str
    total_score: int
    level: str
    resume_evidence_score: int
    assessment_score: int
    depth_score: int
    confidence_score: int
    reason_codes: list[str]
    risk_flags: list[str]
    evidence: list[str]
    learning_plan: str
    adjacent_skills: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)


@dataclass
class ScoredAssessment:
    skill_results: list[SkillResult]
    overall_score: int
    recommendation: str
    strongest_skills: list[str]
    highest_risks: list[str]
