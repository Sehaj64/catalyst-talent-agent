from __future__ import annotations

from .schemas import CandidateProfile, JobSpec, OutreachTurn


def simulate_outreach(candidate: CandidateProfile, job_spec: JobSpec, match_score: float, outreach_hook: str) -> dict[str, object]:
    interest_score, reasons = _interest_score(candidate, job_spec, match_score)
    sentiment = _sentiment(interest_score)
    transcript = [
        OutreachTurn(
            speaker="agent",
            intent="personalized opener",
            message=(
                f"Hi {candidate.name.split()[0]}, I noticed your work on "
                f"{_short_evidence(candidate)}. We are hiring for {job_spec.title} and the role needs "
                f"{_skill_phrase(job_spec)}. Would you be open to a quick exploratory chat?"
            ),
            sentiment="positive",
        ),
        OutreachTurn(
            speaker="candidate",
            intent="initial interest signal",
            message=_candidate_initial_reply(candidate, job_spec, interest_score),
            sentiment=sentiment,
        ),
        OutreachTurn(
            speaker="agent",
            intent="qualification follow-up",
            message=(
                "Helpful. Before I shortlist you, I want to confirm three things: "
                "hands-on production evidence, availability, and what would make the role worth your time."
            ),
            sentiment="neutral",
        ),
        OutreachTurn(
            speaker="candidate",
            intent="constraints and motivation",
            message=_candidate_followup_reply(candidate, job_spec, reasons),
            sentiment=sentiment,
        ),
    ]

    return {
        "score": round(interest_score, 1),
        "reasons": reasons,
        "transcript": transcript,
        "reservations": candidate.reservations,
        "next_steps": _next_steps(candidate, job_spec, interest_score),
    }


def _interest_score(candidate: CandidateProfile, job_spec: JobSpec, match_score: float) -> tuple[float, list[str]]:
    score = 47.0
    reasons: list[str] = []
    jd_text = " ".join(job_spec.must_have_skills + job_spec.domains + [job_spec.title]).lower()
    driver_text = " ".join(candidate.interest_drivers + candidate.preferences).lower()

    for driver in candidate.interest_drivers:
        if driver.lower() in jd_text or any(token in jd_text for token in driver.lower().split()):
            score += 8.0
            reasons.append(f"motivated by {driver}")

    if job_spec.remote_policy == "remote" and candidate.open_to_remote:
        score += 7.0
        reasons.append("remote preference matches")
    elif job_spec.location and job_spec.location in candidate.target_locations:
        score += 6.0
        reasons.append(f"location works: {job_spec.location}")

    if "ownership" in driver_text or "fast shipping" in driver_text:
        score += 4.0
        reasons.append("responds to ownership and speed")

    if "recruiting" in jd_text and ("recruiting domain" in driver_text or "candidate engagement" in driver_text):
        score += 7.0
        reasons.append("explicit recruiting-tech pull")

    if match_score >= 82:
        score += 5.0
        reasons.append("high perceived role fit")
    elif match_score < 62:
        score -= 8.0
        reasons.append("fit uncertainty lowers excitement")

    score += (candidate.responsiveness - 0.5) * 20.0

    if candidate.notice_period_days > 45:
        score -= 5.0
        reasons.append("availability risk")

    if any("not actively" in item.lower() or "less drawn" in item.lower() for item in candidate.reservations):
        score -= 7.0
        reasons.append("candidate has stated reservations")

    if not reasons:
        reasons.append("neutral but reachable")

    return max(5.0, min(100.0, score)), reasons[:6]


def _sentiment(score: float) -> str:
    if score >= 78:
        return "positive"
    if score >= 58:
        return "cautious"
    if score >= 40:
        return "neutral"
    return "negative"


def _short_evidence(candidate: CandidateProfile) -> str:
    source = candidate.projects[0] if candidate.projects else candidate.evidence[0]
    return source.split(".")[0].lower()


def _skill_phrase(job_spec: JobSpec) -> str:
    skills = job_spec.must_have_skills[:3] or job_spec.keywords[:3]
    return ", ".join(skills) if skills else "AI product engineering"


def _candidate_initial_reply(candidate: CandidateProfile, job_spec: JobSpec, interest_score: float) -> str:
    driver = candidate.interest_drivers[0] if candidate.interest_drivers else "the problem space"
    if interest_score >= 78:
        return (
            f"Yes, this is relevant. I am especially interested in {driver}, and the {job_spec.title} scope "
            "sounds close to work I have already shipped."
        )
    if interest_score >= 58:
        return (
            f"Potentially. {driver.title()} is interesting, but I would want to understand the roadmap, "
            "data access, and how production-ready the team expects this to be."
        )
    return (
        "Thanks for reaching out. I am not actively prioritizing this kind of move right now, "
        "but I can review details if the scope is unusually strong."
    )


def _candidate_followup_reply(candidate: CandidateProfile, job_spec: JobSpec, reasons: list[str]) -> str:
    motivation = reasons[0] if reasons else "the role is close enough to explore"
    reservation = candidate.reservations[0] if candidate.reservations else "no major blockers yet"
    salary = f"{candidate.salary_expectation_lpa} LPA" if candidate.salary_expectation_lpa else "market aligned"
    return (
        f"My notice period is {candidate.notice_period_days} days and compensation expectation is around {salary}. "
        f"The strongest pull is {motivation}. Main concern: {reservation}."
    )


def _next_steps(candidate: CandidateProfile, job_spec: JobSpec, interest_score: float) -> list[str]:
    steps = []
    if interest_score >= 78:
        steps.append("Send recruiter screen invite within 24 hours.")
    elif interest_score >= 58:
        steps.append("Send a concise role brief and ask one targeted technical follow-up.")
    else:
        steps.append("Keep warm; do not spend interview bandwidth yet.")

    if candidate.notice_period_days > 45:
        steps.append("Validate notice period flexibility before technical interview.")

    if job_spec.must_have_skills:
        steps.append(f"Ask for proof around {job_spec.must_have_skills[0]} in a shipped project.")

    return steps
