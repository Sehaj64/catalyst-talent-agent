from __future__ import annotations

from .schemas import BusinessImpact, CandidateAssessment, CandidateProfile, EvidencePath, JobSpec, RecruiterBrief, RiskSignal


def build_evidence_paths(
    candidate: CandidateProfile,
    job_spec: JobSpec,
    matched_skills: list[str],
    related_skills: dict[str, list[str]],
) -> list[EvidencePath]:
    paths: list[EvidencePath] = []
    evidence_pool = candidate.evidence + candidate.projects + candidate.achievements

    for skill in matched_skills[:4]:
        evidence = _best_evidence(evidence_pool, skill) or evidence_pool[0]
        paths.append(
            EvidencePath(
                claim=f"Direct evidence for {skill}",
                evidence=evidence,
                source=candidate.public_source,
                confidence=0.88,
            )
        )

    for required, adjacent in list(related_skills.items())[:2]:
        evidence = _best_evidence(evidence_pool, adjacent[0]) or evidence_pool[0]
        paths.append(
            EvidencePath(
                claim=f"Adjacent evidence for missing/implicit {required}",
                evidence=f"{evidence} Related skills observed: {', '.join(adjacent[:3])}.",
                source=candidate.public_source,
                confidence=0.68,
            )
        )

    if set(candidate.domains) & set(job_spec.domains):
        domain = sorted(set(candidate.domains) & set(job_spec.domains))[0]
        paths.append(
            EvidencePath(
                claim=f"Domain context in {domain}",
                evidence=_best_evidence(evidence_pool, domain) or f"Profile lists project/domain experience in {domain}.",
                source=candidate.public_source,
                confidence=0.78,
            )
        )

    return paths[:6]


def confidence_score(
    candidate: CandidateProfile,
    match_score: float,
    interest_score: float,
    missing_skills: list[str],
    evidence_paths: list[EvidencePath],
) -> float:
    evidence_strength = min(len(evidence_paths), 5) * 12
    score_agreement = 20 - min(abs(match_score - interest_score), 30) * 0.35
    source_strength = 12 if len(candidate.evidence) >= 3 else 8
    missing_penalty = min(len(missing_skills) * 7, 18)
    responsiveness = candidate.responsiveness * 18
    return round(max(5, min(100, evidence_strength + score_agreement + source_strength + responsiveness - missing_penalty)), 1)


def risk_signals(candidate: CandidateProfile, job_spec: JobSpec, missing_skills: list[str], interest_score: float) -> list[RiskSignal]:
    risks: list[RiskSignal] = []

    if missing_skills:
        risks.append(
            RiskSignal(
                label="Skill validation needed",
                severity="medium" if len(missing_skills) <= 2 else "high",
                rationale=f"Missing direct evidence for {', '.join(missing_skills[:3])}.",
                mitigation=f"Ask for a shipped example involving {missing_skills[0]} before final shortlist.",
            )
        )

    if candidate.notice_period_days > 45:
        risks.append(
            RiskSignal(
                label="Availability risk",
                severity="medium",
                rationale=f"Notice period is {candidate.notice_period_days} days.",
                mitigation="Confirm buyout, early release, or phased start before technical rounds.",
            )
        )

    if interest_score < 65:
        risks.append(
            RiskSignal(
                label="Engagement risk",
                severity="medium",
                rationale="Simulated outreach shows cautious or weak motivation.",
                mitigation="Send a sharper role brief tied to the candidate's strongest motivation.",
            )
        )

    if job_spec.domains and not (set(candidate.domains) & set(job_spec.domains)):
        risks.append(
            RiskSignal(
                label="Domain transfer risk",
                severity="low",
                rationale=f"No direct domain overlap with {', '.join(job_spec.domains[:3])}.",
                mitigation="Use the first screen to test how quickly they map prior systems to this domain.",
            )
        )

    if candidate.salary_expectation_lpa and job_spec.salary_hint_lpa and candidate.salary_expectation_lpa > job_spec.salary_hint_lpa * 1.2:
        risks.append(
            RiskSignal(
                label="Compensation risk",
                severity="medium",
                rationale="Candidate expectation is materially above the salary hint.",
                mitigation="Clarify range and non-cash upside before scheduling panels.",
            )
        )

    return risks[:5]


def interview_questions(candidate: CandidateProfile, job_spec: JobSpec, missing_skills: list[str]) -> list[str]:
    questions = [
        f"Walk me through a shipped project where you used {candidate.skills[0]} to solve a real user problem.",
        "What would your first version of this talent-scouting agent do in week one, and what would you intentionally leave out?",
        "How would you evaluate whether the agent's shortlist is actually useful to recruiters?",
    ]
    if job_spec.must_have_skills:
        questions.append(f"Show the trade-offs you would make around {job_spec.must_have_skills[0]} for speed versus reliability.")
    if missing_skills:
        questions.append(f"Where have you built something closest to {missing_skills[0]}, even if the stack name was different?")
    if "privacy" in job_spec.must_have_skills or "privacy" in job_spec.nice_to_have_skills:
        questions.append("How would you prevent the agent from overusing sensitive candidate information?")
    return questions[:6]


def build_recruiter_brief(ranked: list[CandidateAssessment], job_spec: JobSpec) -> RecruiterBrief:
    if not ranked:
        return RecruiterBrief(
            hiring_thesis="No candidates met the minimum threshold.",
            shortlist_strategy="Broaden the source pool and relax nice-to-have filters.",
            top_tradeoffs=["Insufficient candidate evidence."],
            recommended_sequence=["Rewrite JD with clearer must-have skills.", "Run discovery again."],
            compliance_audit=["No candidate ranking was produced."],
            demo_talking_points=["The system fails closed when evidence is insufficient."],
        )

    top = ranked[0]
    tradeoffs = []
    for item in ranked[:3]:
        if item.risk_signals:
            tradeoffs.append(f"{item.candidate.name}: {item.risk_signals[0].label}.")
        else:
            tradeoffs.append(f"{item.candidate.name}: strong evidence with no major first-pass risk.")

    recommended_sequence = [
        f"Start with {top.candidate.name} because combined score and confidence are strongest.",
        "Use candidate-specific interview questions instead of a generic screen.",
        "Validate the highest-severity risk before scheduling deep technical panels.",
        "Keep the next two candidates warm as backups with tailored outreach hooks.",
    ]

    compliance = [
        "Scores use skills, evidence, domain context, logistics, and stated preferences.",
        "Protected attributes such as gender, age, religion, caste, and ethnicity are not model inputs.",
        "Location is used only as a logistics constraint and should be reviewed by a human recruiter.",
        "Outreach is simulated in this prototype; production use should require consent-aware messaging.",
    ]

    talking_points = [
        "This is an auditable agent workflow, not a single black-box prompt.",
        "The system separates role match from candidate interest, then combines them transparently.",
        "Every top candidate includes evidence paths, risk mitigations, transcript, and next-best action.",
        "The discovery layer is swappable for GitHub, ATS, CRM, or a consented talent graph.",
    ]

    return RecruiterBrief(
        hiring_thesis=(
            f"For {job_spec.title}, prioritize candidates with shipped agent/RAG evidence, "
            "recruiting-domain pull, and enough availability to enter process quickly."
        ),
        shortlist_strategy=(
            f"Interview {top.candidate.name} first, compare against {ranked[1].candidate.name if len(ranked) > 1 else 'the next backup'}, "
            "and use risk mitigations to avoid wasting panel time."
        ),
        top_tradeoffs=tradeoffs,
        recommended_sequence=recommended_sequence,
        compliance_audit=compliance,
        demo_talking_points=talking_points,
    )


def build_business_impact(ranked: list[CandidateAssessment], profiles_analyzed: int) -> BusinessImpact:
    manual_minutes_per_profile = 12
    assisted_minutes_per_profile = 2
    recruiter_cost_per_hour_inr = 1200
    profiles = max(profiles_analyzed, len(ranked))

    manual_hours = profiles * manual_minutes_per_profile / 60
    assisted_hours = profiles * assisted_minutes_per_profile / 60
    hours_saved = round(max(0, manual_hours - assisted_hours), 1)
    cost_saved = int(round(hours_saved * recruiter_cost_per_hour_inr, -2))

    top_three = ranked[:3]
    avg_confidence = sum(item.confidence_score for item in top_three) / len(top_three) if top_three else 0
    avg_match = sum(item.match_score for item in top_three) / len(top_three) if top_three else 0
    high_risk_count = sum(
        1
        for item in top_three
        for risk in item.risk_signals
        if risk.severity == "high"
    )
    accuracy_proxy = round((avg_match * 0.6) + (avg_confidence * 0.4), 1)

    return BusinessImpact(
        profiles_analyzed=profiles,
        recruiter_hours_saved=hours_saved,
        estimated_cost_saved_inr=cost_saved,
        throughput_lift=(
            f"~{manual_minutes_per_profile / assisted_minutes_per_profile:.1f}x faster first-pass screening "
            f"under the stated assumptions."
        ),
        quality_lift=(
            f"Top-three evidence-weighted fit proxy is {accuracy_proxy}/100, "
            "using match plus confidence rather than keyword overlap alone."
        ),
        accuracy_proxy=accuracy_proxy,
        wasted_screen_reduction=(
            "High-risk candidates are flagged before recruiter screens."
            if high_risk_count
            else "No high-risk top-three candidate detected; medium risks are still surfaced before screens."
        ),
        roi_summary=(
            f"For this run, the agent reviewed {profiles} profiles and estimates {hours_saved} recruiter hours "
            f"saved, or about INR {cost_saved:,} of screening effort before interviews."
        ),
        baseline_assumptions=[
            "Manual first-pass profile review takes about 12 minutes per candidate.",
            "Agent-assisted review takes about 2 minutes per candidate because the recruiter reviews ranked evidence.",
            "Recruiter loaded cost is estimated at INR 1,200 per hour.",
            "Quality lift is treated as an evidence-weighted proxy, not a final hiring accuracy claim.",
        ],
        recommended_kpis=[
            "Time from JD intake to first shortlist",
            "Recruiter minutes per qualified candidate",
            "Top-3 shortlist acceptance rate by hiring manager",
            "Candidate reply rate after personalized outreach",
            "False positive screen rate",
        ],
    )


def _best_evidence(evidence_pool: list[str], term: str) -> str | None:
    lowered = term.lower()
    for evidence in evidence_pool:
        if lowered in evidence.lower():
            return evidence
    return None
