from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    job_description: str = Field(..., min_length=80)
    top_k: int = Field(default=8, ge=3, le=12)
    simulate_outreach: bool = True


class JobSpec(BaseModel):
    original_text: str
    title: str
    seniority: Literal["junior", "mid", "senior", "lead", "unknown"]
    min_years: int | None = None
    max_years: int | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    location: str | None = None
    remote_policy: Literal["remote", "hybrid", "onsite", "unknown"] = "unknown"
    employment_type: str = "full-time"
    salary_hint_lpa: int | None = None
    keywords: list[str] = Field(default_factory=list)
    recruiter_questions: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    candidate_id: str
    name: str
    headline: str
    current_title: str
    years_experience: float
    location: str
    target_locations: list[str]
    open_to_remote: bool
    salary_expectation_lpa: int | None
    notice_period_days: int
    skills: list[str]
    tools: list[str]
    domains: list[str]
    projects: list[str]
    achievements: list[str]
    evidence: list[str]
    preferences: list[str]
    interest_drivers: list[str]
    reservations: list[str]
    responsiveness: float = Field(ge=0, le=1)
    public_source: str


class OutreachTurn(BaseModel):
    speaker: Literal["agent", "candidate"]
    intent: str
    message: str
    sentiment: Literal["positive", "neutral", "cautious", "negative"] = "neutral"


class ScoreBreakdown(BaseModel):
    skill_alignment: float
    seniority_fit: float
    domain_fit: float
    evidence_depth: float
    logistics_fit: float
    differentiation: float


class CandidateAssessment(BaseModel):
    rank: int
    candidate: CandidateProfile
    match_score: float
    interest_score: float
    combined_score: float
    decision: str
    matched_skills: list[str]
    related_skills: dict[str, list[str]]
    missing_skills: list[str]
    score_breakdown: ScoreBreakdown
    match_explanation: str
    outreach_hook: str
    transcript: list[OutreachTurn]
    reservations: list[str]
    next_steps: list[str]
    counterfactual: str


class AgentRun(BaseModel):
    generated_at: datetime
    job_spec: JobSpec
    search_strategy: dict[str, list[str]]
    ranked_shortlist: list[CandidateAssessment]
    summary: dict[str, str | int | float | list[str]]
    audit_log: list[str]
