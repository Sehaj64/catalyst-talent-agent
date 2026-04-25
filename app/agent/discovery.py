from __future__ import annotations

from .schemas import CandidateProfile, JobSpec
from .taxonomy import normalize_skill, related_for


class CandidateDiscovery:
    """Simulated discovery layer.

    The hackathon brief allows any stack, but not paid credits. This layer behaves like
    a sourcing connector while using a curated local candidate market. In production,
    the same interface can call GitHub search, ATS exports, internal CRM data, or a
    consented talent graph.
    """

    def __init__(self, candidate_pool: list[CandidateProfile]) -> None:
        self.candidate_pool = candidate_pool

    def build_search_strategy(self, job_spec: JobSpec) -> dict[str, list[str]]:
        must = job_spec.must_have_skills[:5]
        domain = job_spec.domains[:3]
        title = job_spec.title.lower()
        query_core = " ".join(must[:3] or job_spec.keywords[:3])

        return {
            "queries": [
                f'"{title}" {query_core}'.strip(),
                f'"agent" "recruiting" {" ".join(must[:2])}'.strip(),
                f'"candidate matching" {" ".join(domain or ["saas"])}'.strip(),
                f'"LangGraph" OR "RAG" "{title}"',
            ],
            "sources": [
                "public GitHub/project portfolios (simulated)",
                "LinkedIn-style profile summaries (simulated)",
                "ATS and CRM exports (simulated)",
                "technical blogs, demo videos, and talks (simulated)",
            ],
            "filters": [
                f"seniority: {job_spec.seniority}",
                f"remote policy: {job_spec.remote_policy}",
                f"domains: {', '.join(job_spec.domains) if job_spec.domains else 'not constrained'}",
                "evidence required: project, achievement, or public artifact",
            ],
        }

    def discover(self, job_spec: JobSpec, limit: int = 12) -> list[CandidateProfile]:
        ranked = sorted(
            self.candidate_pool,
            key=lambda candidate: self._retrieval_score(candidate, job_spec),
            reverse=True,
        )
        return ranked[:limit]

    def _retrieval_score(self, candidate: CandidateProfile, job_spec: JobSpec) -> float:
        candidate_skills = {normalize_skill(skill) for skill in candidate.skills + candidate.tools}
        must = job_spec.must_have_skills or job_spec.keywords[:5]

        exact_hits = sum(1 for skill in must if normalize_skill(skill) in candidate_skills)
        related_hits = sum(1 for skill in must if related_for(skill, candidate_skills))
        domain_hits = len(set(candidate.domains) & set(job_spec.domains))
        title_hit = 1 if any(token in candidate.headline.lower() for token in job_spec.title.lower().split()) else 0
        evidence_density = min(len(candidate.evidence) + len(candidate.projects), 6) / 6

        return (
            exact_hits * 5
            + related_hits * 2
            + domain_hits * 3
            + title_hit
            + evidence_density
            + candidate.responsiveness
        )
