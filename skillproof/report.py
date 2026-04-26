from __future__ import annotations

from skillproof.models import ScoredAssessment, SkillResult


def roi_projection(
    candidates_per_month: int,
    manual_minutes: int,
    agent_minutes: int,
    hourly_cost_inr: int,
) -> dict[str, int | float]:
    minutes_saved = max(0, manual_minutes - agent_minutes)
    monthly_hours = round((minutes_saved * candidates_per_month) / 60, 1)
    monthly_cost = round(monthly_hours * hourly_cost_inr)
    throughput_gain = round(manual_minutes / max(1, agent_minutes), 1)
    return {
        "minutes_saved_per_candidate": minutes_saved,
        "monthly_hours_saved": monthly_hours,
        "monthly_cost_saved": monthly_cost,
        "throughput_gain": throughput_gain,
    }


def accuracy_lift_estimate(scored: ScoredAssessment | None) -> int:
    if not scored or not scored.skill_results:
        return 0
    explained = sum(1 for result in scored.skill_results if result.reason_codes)
    evidenced = sum(1 for result in scored.skill_results if result.resume_evidence_score > 0)
    assessed = sum(1 for result in scored.skill_results if result.assessment_score > 0)
    coverage = round(((explained + evidenced + assessed) / (len(scored.skill_results) * 3)) * 100)
    return min(35, max(8, round(coverage * 0.35)))


def evidence_status(result: SkillResult) -> str:
    if result.resume_evidence_score >= 18 and result.assessment_score >= 28:
        return "Verified"
    if result.resume_evidence_score > 0 or result.assessment_score >= 20:
        return "Partially verified"
    return "Unproven"


def gap_priority(result: SkillResult) -> str:
    if result.criticality == "High" and result.total_score < 60:
        return "High"
    if result.total_score < 70:
        return "Medium"
    return "Low"


def skill_choice_reason(result: SkillResult) -> str:
    if result.criticality == "High":
        return "Chosen because the JD marks this as a required or must-have skill."
    if result.criticality == "Medium":
        return "Chosen because the JD mentions this as preferred, useful, or role-relevant."
    return "Chosen because the resume mentions it and it may support adjacent learning."


def gap_reason(result: SkillResult) -> str:
    reasons = []
    if result.total_score < 70:
        reasons.append("score is below the 70/100 readiness threshold")
    if result.resume_evidence_score == 0:
        reasons.append("resume has no direct evidence")
    elif result.resume_evidence_score < 12:
        reasons.append("resume evidence is thin")
    if result.assessment_score < 25:
        reasons.append("answers need more concrete implementation detail")
    if result.depth_score < 12:
        reasons.append("answers show limited tradeoff or failure-case depth")
    if not reasons:
        return "No major gap detected; keep as a light validation item."
    return "Gap detected because " + ", ".join(reasons) + "."


def learning_style_tip(style: str, skill_name: str) -> str:
    tips = {
        "Project-based": f"Build a small {skill_name} artifact and explain the tradeoffs in a README.",
        "Video-first": f"Watch one focused lesson, then immediately reproduce the {skill_name} concept in a mini task.",
        "Docs-first": f"Read the official docs for one {skill_name} concept, then write a short implementation note.",
        "Practice drills": f"Complete short {skill_name} exercises daily and track weak concepts after each attempt.",
    }
    return tips.get(style, tips["Project-based"])


def readiness_summary(scored: ScoredAssessment) -> dict[str, int | str]:
    verified = sum(1 for result in scored.skill_results if evidence_status(result) == "Verified")
    gaps = sum(1 for result in scored.skill_results if result.total_score < 70)
    high_priority_gaps = sum(
        1
        for result in scored.skill_results
        if result.criticality == "High" and result.total_score < 70
    )
    if scored.overall_score >= 80 and high_priority_gaps == 0:
        status = "Job-ready"
    elif scored.overall_score >= 60:
        status = "Trainable with gaps"
    else:
        status = "Needs foundation work"
    return {
        "status": status,
        "verified_skills": verified,
        "gap_count": gaps,
        "high_priority_gap_count": high_priority_gaps,
    }


def learning_plan_rows(
    scored: ScoredAssessment,
    learning_style: str = "Project-based",
    weekly_hours: int = 5,
) -> list[dict[str, str | list[str]]]:
    rows = []
    for result in scored.skill_results:
        if result.total_score >= 75:
            continue
        if result.total_score >= 70:
            base_hours = 4
        elif result.total_score >= 50:
            base_hours = 8
        else:
            base_hours = 18
        weeks = max(1, round(base_hours / max(1, weekly_hours)))
        timeline = f"{base_hours} focused hours, about {weeks} week(s) at {weekly_hours} hrs/week"
        rows.append(
            {
                "Skill": result.name,
                "Priority": gap_priority(result),
                "Timeline": timeline,
                "Goal": f"Reach working proficiency in {result.name} for this JD.",
                "Adjacent skills": result.adjacent_skills,
                "Resources": result.resources,
                "Learning style": learning_style,
                "Style tip": learning_style_tip(learning_style, result.name),
                "Why this gap": gap_reason(result),
                "Plan": result.learning_plan,
            }
        )
    return rows


def build_markdown_report(scored: ScoredAssessment) -> str:
    summary = readiness_summary(scored)
    lines = [
        "# SkillProof AI Assessment Report",
        "",
        f"**Readiness status:** {summary['status']}",
        f"**Overall readiness:** {scored.overall_score}%",
        f"**Recommendation:** {scored.recommendation}",
        "",
        "## Summary",
        f"- Verified skills: {summary['verified_skills']} of {len(scored.skill_results)}",
        f"- Skills below readiness threshold: {summary['gap_count']}",
        f"- High-priority gaps: {summary['high_priority_gap_count']}",
        "",
        "## Strongest Skills",
    ]
    if scored.strongest_skills:
        lines.extend(f"- {skill}" for skill in scored.strongest_skills)
    else:
        lines.append("- No strong skill signals found.")

    lines.append("")
    lines.append("## Skill Gaps")
    gaps = [result for result in scored.skill_results if result.total_score < 70]
    if gaps:
        for result in gaps:
            lines.append(
                f"- {result.name}: {result.total_score}/100, {gap_priority(result)} priority, {evidence_status(result)}"
            )
    else:
        lines.append("- No major gaps found.")

    lines.append("")
    lines.append("## Skill Evidence And Scores")
    for result in scored.skill_results:
        lines.extend(
            [
                "",
                f"### {result.name}",
                f"- Category: {result.category}",
                f"- Criticality: {result.criticality}",
                f"- Evidence status: {evidence_status(result)}",
                f"- Gap priority: {gap_priority(result)}",
                f"- Score: {result.total_score}/100 ({result.level})",
                f"- Resume evidence: {result.resume_evidence_score}/25",
                f"- Assessment answer quality: {result.assessment_score}/45",
                f"- Practical depth: {result.depth_score}/20",
                f"- Confidence: {result.confidence_score}/10",
                f"- Reason codes: {', '.join(result.reason_codes) if result.reason_codes else 'none'}",
            ]
        )
        if result.risk_flags:
            lines.append(f"- Gap notes: {'; '.join(result.risk_flags)}")
        if result.evidence:
            lines.append("- Resume evidence snippets:")
            lines.extend(f"  - {snippet}" for snippet in result.evidence)

    lines.append("")
    lines.append("## Personalized Learning Plan")
    plans = learning_plan_rows(scored)
    if plans:
        for row in plans:
            lines.extend(
                [
                    "",
                    f"### {row['Skill']}",
                    f"- Priority: {row['Priority']}",
                    f"- Timeline: {row['Timeline']}",
                    f"- Goal: {row['Goal']}",
                    f"- Why this gap: {row['Why this gap']}",
                    f"- Adjacent skills: {', '.join(row['Adjacent skills']) if row['Adjacent skills'] else 'related fundamentals'}",
                    f"- Resources: {'; '.join(row['Resources']) if row['Resources'] else 'No curated resources available'}",
                    f"- Learning style tip: {row['Style tip']}",
                    f"- Plan: {row['Plan']}",
                ]
            )
    else:
        lines.append("- No immediate learning plan needed.")

    return "\n".join(lines)
