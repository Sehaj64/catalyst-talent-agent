from __future__ import annotations

from datetime import datetime, timezone

from .data import SAMPLE_CANDIDATES
from .decision_intelligence import (
    build_evidence_paths,
    build_recruiter_brief,
    confidence_score,
    interview_questions,
    risk_signals,
)
from .discovery import CandidateDiscovery
from .jd_parser import parse_job_description
from .outreach import simulate_outreach
from .resume_parser import parse_candidate_resumes
from .schemas import AgentRun, CandidateAssessment, CandidateProfile, OutreachTurn
from .scorer import decision_label, score_match


class TalentScoutingAgent:
    """End-to-end agent pipeline for talent scouting and engagement."""

    def __init__(self, candidate_pool: list[CandidateProfile] | None = None) -> None:
        self.candidate_pool = candidate_pool or SAMPLE_CANDIDATES
        self.discovery = CandidateDiscovery(self.candidate_pool)

    def run(
        self,
        job_description: str,
        top_k: int = 8,
        simulate: bool = True,
        candidate_resumes: str | None = "",
        include_sample_market: bool = True,
    ) -> AgentRun:
        audit_log: list[str] = ["Received job description and initialized scouting run."]
        job_spec = parse_job_description(job_description)
        audit_log.append(
            f"Parsed JD into title={job_spec.title}, seniority={job_spec.seniority}, "
            f"skills={len(job_spec.must_have_skills)} must-have/{len(job_spec.nice_to_have_skills)} nice-to-have."
        )

        imported_candidates = parse_candidate_resumes(candidate_resumes)
        candidate_pool = []
        if include_sample_market:
            candidate_pool.extend(self.candidate_pool)
        candidate_pool.extend(imported_candidates)
        if not candidate_pool:
            candidate_pool.extend(self.candidate_pool)
            audit_log.append("No resume candidates were provided, so the simulated market was used as fallback.")
        elif imported_candidates:
            audit_log.append(
                f"Parsed {len(imported_candidates)} user-provided resume profile(s) and "
                f"{'included' if include_sample_market else 'excluded'} the simulated market."
            )

        discovery = CandidateDiscovery(candidate_pool)
        search_strategy = discovery.build_search_strategy(job_spec)
        if imported_candidates:
            search_strategy["sources"].insert(0, "user-provided resumes / pasted candidate profiles")
            search_strategy["filters"].append("resume evidence parsed into candidate profiles")
        discovered = discovery.discover(job_spec, limit=max(top_k + 4, min(12, len(candidate_pool))))
        source_label = "resume and market sources" if imported_candidates else "simulated public and ATS sources"
        audit_log.append(f"Discovered {len(discovered)} candidate profiles from {source_label}.")

        assessments: list[CandidateAssessment] = []
        for candidate in discovered:
            match = score_match(candidate, job_spec)
            if simulate:
                outreach = simulate_outreach(
                    candidate=candidate,
                    job_spec=job_spec,
                    match_score=float(match["score"]),
                    outreach_hook=str(match["outreach_hook"]),
                )
            else:
                outreach = {
                    "score": 50.0,
                    "transcript": [
                        OutreachTurn(
                            speaker="agent",
                            intent="not simulated",
                            message="Outreach simulation disabled for this run.",
                        )
                    ],
                    "reservations": candidate.reservations,
                    "next_steps": ["Run outreach simulation or contact candidate manually."],
                }

            evidence_paths = build_evidence_paths(
                candidate=candidate,
                job_spec=job_spec,
                matched_skills=match["matched_skills"],  # type: ignore[arg-type]
                related_skills=match["related_skills"],  # type: ignore[arg-type]
            )
            confidence = confidence_score(
                candidate=candidate,
                match_score=float(match["score"]),
                interest_score=float(outreach["score"]),
                missing_skills=match["missing_skills"],  # type: ignore[arg-type]
                evidence_paths=evidence_paths,
            )
            candidate_risks = risk_signals(
                candidate=candidate,
                job_spec=job_spec,
                missing_skills=match["missing_skills"],  # type: ignore[arg-type]
                interest_score=float(outreach["score"]),
            )
            combined = round((float(match["score"]) * 0.65) + (float(outreach["score"]) * 0.35), 1)
            assessments.append(
                CandidateAssessment(
                    rank=0,
                    candidate=candidate,
                    match_score=float(match["score"]),
                    interest_score=float(outreach["score"]),
                    confidence_score=confidence,
                    combined_score=combined,
                    decision=decision_label(combined, float(match["score"]), float(outreach["score"])),
                    matched_skills=match["matched_skills"],  # type: ignore[arg-type]
                    related_skills=match["related_skills"],  # type: ignore[arg-type]
                    missing_skills=match["missing_skills"],  # type: ignore[arg-type]
                    score_breakdown=match["breakdown"],  # type: ignore[arg-type]
                    match_explanation=str(match["explanation"]),
                    evidence_paths=evidence_paths,
                    outreach_hook=str(match["outreach_hook"]),
                    transcript=outreach["transcript"],  # type: ignore[arg-type]
                    interview_questions=interview_questions(
                        candidate=candidate,
                        job_spec=job_spec,
                        missing_skills=match["missing_skills"],  # type: ignore[arg-type]
                    ),
                    risk_signals=candidate_risks,
                    reservations=outreach["reservations"],  # type: ignore[arg-type]
                    next_steps=outreach["next_steps"],  # type: ignore[arg-type]
                    counterfactual=str(match["counterfactual"]),
                )
            )

        ranked = sorted(assessments, key=lambda item: item.combined_score, reverse=True)[:top_k]
        for index, assessment in enumerate(ranked, start=1):
            assessment.rank = index

        audit_log.append("Computed match, interest, and combined ranking scores with explainable breakdowns.")
        audit_log.append("Generated evidence paths, confidence scores, risk mitigations, and interview questions.")
        audit_log.append(f"Returned top {len(ranked)} candidates with next actions for the recruiter.")

        return AgentRun(
            generated_at=datetime.now(timezone.utc),
            job_spec=job_spec,
            search_strategy=search_strategy,
            ranked_shortlist=ranked,
            recruiter_brief=build_recruiter_brief(ranked, job_spec),
            summary=self._summary(ranked, job_spec),
            audit_log=audit_log,
        )

    def _summary(self, ranked: list[CandidateAssessment], job_spec) -> dict[str, str | int | float | list[str]]:
        if not ranked:
            return {
                "total_shortlisted": 0,
                "average_match_score": 0,
                "average_interest_score": 0,
                "top_candidate": "None",
                "recommended_action": "Broaden search strategy.",
                "risk_flags": [],
            }

        avg_match = round(sum(item.match_score for item in ranked) / len(ranked), 1)
        avg_interest = round(sum(item.interest_score for item in ranked) / len(ranked), 1)
        avg_confidence = round(sum(item.confidence_score for item in ranked) / len(ranked), 1)
        risk_flags = []
        if any(item.missing_skills for item in ranked[:3]):
            risk_flags.append("Top candidates still have at least one skill gap to validate.")
        if any(item.candidate.notice_period_days > 45 for item in ranked[:3]):
            risk_flags.append("Availability may slow the first hiring wave.")
        if job_spec.domains and not any(set(item.candidate.domains) & set(job_spec.domains) for item in ranked[:3]):
            risk_flags.append("Domain familiarity is weak among the top three.")

        return {
            "total_shortlisted": len(ranked),
            "average_match_score": avg_match,
            "average_interest_score": avg_interest,
            "average_confidence_score": avg_confidence,
            "top_candidate": ranked[0].candidate.name,
            "recommended_action": f"Start with {ranked[0].candidate.name}; they have the strongest combined evidence and interest signal.",
            "risk_flags": risk_flags,
        }
