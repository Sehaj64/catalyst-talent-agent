from __future__ import annotations

from skillproof.models import ScoredAssessment, SkillResult


COURSE_CATALOG = {
    "Python": [
        "Coursera - Python for Everybody, University of Michigan (structured course): https://www.coursera.org/specializations/python",
        "Python official tutorial (2-3 hrs): https://docs.python.org/3/tutorial/",
        "FastAPI docs - First Steps (2 hrs): https://fastapi.tiangolo.com/tutorial/first-steps/",
        "Kaggle Python micro-course (4 hrs): https://www.kaggle.com/learn/python",
    ],
    "SQL": [
        "Coursera - SQL for Data Science, UC Davis (2 weeks): https://www.coursera.org/learn/sql-for-data-science",
        "Mode SQL tutorial (4-6 hrs): https://mode.com/sql-tutorial/",
        "PostgreSQL SELECT docs (1 hr reference): https://www.postgresql.org/docs/current/sql-select.html",
        "freeCodeCamp SQL course listing (4-5 hrs): https://www.classcentral.com/course/freecodecamp-sql-tutorial-full-database-course-for-beginners-104803",
    ],
    "React": [
        "Coursera - Meta Front-End Developer certificate, React path: https://www.coursera.org/professional-certificates/meta-front-end-developer",
        "React Learn - official docs (4-6 hrs): https://react.dev/learn",
        "Next.js docs - App Router fundamentals (3 hrs): https://nextjs.org/docs",
        "Testing Library React examples (2 hrs): https://testing-library.com/docs/react-testing-library/example-intro/",
    ],
    "TypeScript": [
        "Coursera - Meta Front-End Developer certificate, typed front-end project path: https://www.coursera.org/professional-certificates/meta-front-end-developer",
        "TypeScript Handbook (4-6 hrs): https://www.typescriptlang.org/docs/handbook/intro.html",
        "React TypeScript guide (2 hrs): https://react.dev/learn/typescript",
        "TypeScript narrowing chapter (1 hr): https://www.typescriptlang.org/docs/handbook/2/narrowing.html",
    ],
    "Machine Learning": [
        "Coursera - Machine Learning Specialization, Andrew Ng / DeepLearning.AI: https://www.coursera.org/specializations/machine-learning-introduction",
        "Google Machine Learning Crash Course (15 hrs): https://developers.google.com/machine-learning/crash-course/",
        "Scikit-learn user guide - model evaluation (2 hrs): https://scikit-learn.org/stable/modules/model_evaluation.html",
        "Kaggle Intro to Machine Learning (4 hrs): https://www.kaggle.com/learn/intro-to-machine-learning",
    ],
    "LLM / Generative AI": [
        "Coursera - Generative AI with Large Language Models, DeepLearning.AI: https://www.coursera.org/learn/generative-ai-with-llms",
        "OpenAI docs - text generation (2 hrs): https://platform.openai.com/docs/guides/text-generation",
        "LangChain RAG tutorial (3 hrs): https://python.langchain.com/docs/tutorials/rag/",
        "Ragas evaluation docs (2 hrs): https://docs.ragas.io/",
    ],
    "Data Analysis": [
        "Coursera - Google Data Analytics Professional Certificate: https://www.coursera.org/professional-certificates/google-data-analytics",
        "Kaggle Data Cleaning (4 hrs): https://www.kaggle.com/learn/data-cleaning",
        "Pandas getting started (2 hrs): https://pandas.pydata.org/docs/getting_started/",
        "Storytelling with Data blog practice (2 hrs): https://www.storytellingwithdata.com/blog",
    ],
    "APIs": [
        "Coursera - Meta Back-End Developer certificate, APIs/Python/SQL path: https://www.coursera.org/professional-certificates/meta-back-end-developer",
        "FastAPI tutorial - First Steps to Path Params (3 hrs): https://fastapi.tiangolo.com/tutorial/",
        "REST API tutorial (2 hrs): https://restfulapi.net/",
        "HTTP status code reference (1 hr): https://developer.mozilla.org/en-US/docs/Web/HTTP/Status",
    ],
    "Testing": [
        "Coursera - Software Testing and Automation, University of Minnesota: https://www.coursera.org/specializations/software-testing-automation",
        "Pytest docs - Getting Started (2 hrs): https://docs.pytest.org/en/stable/getting-started.html",
        "Testing Library intro (2 hrs): https://testing-library.com/docs/",
        "FastAPI testing docs (1 hr): https://fastapi.tiangolo.com/tutorial/testing/",
    ],
    "Communication": [
        "Google Technical Writing One (3 hrs): https://developers.google.com/tech-writing/one",
        "Write the Docs guide (2 hrs): https://www.writethedocs.org/guide/",
        "Storytelling with Data blog practice (2 hrs): https://www.storytellingwithdata.com/blog",
    ],
}

DYNAMIC_CATEGORIES = {
    "Marketing / Growth",
    "Sales / Customer Operations",
    "Cloud / DevOps",
    "Data / Analytics",
    "Operations / Supply Chain",
    "Product / Design",
    "Finance / HR",
    "Healthcare / Compliance",
    "Role-specific skill",
}


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
    if result.resume_evidence_score >= 18 and result.assessment_score >= 25 and result.depth_score >= 12:
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
    if result.category in DYNAMIC_CATEGORIES:
        return "Chosen by the dynamic JD fallback because this role-specific skill appears in the job description."
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


def course_path(result: SkillResult) -> list[str]:
    catalog = COURSE_CATALOG.get(result.name, [])
    if not catalog:
        candidates = result.resources[:4]
    elif result.total_score < 50:
        candidates = catalog[:3]
    elif result.total_score < 70:
        candidates = catalog[:2] + result.resources[:1]
    else:
        candidates = catalog[:1] + result.resources[:1]
    unique = []
    seen_urls = set()
    for item in candidates:
        marker = item.split("https://", 1)[-1].strip().lower() if "https://" in item else item.lower()
        if marker in seen_urls:
            continue
        seen_urls.add(marker)
        unique.append(item)
    return unique


def practice_drill(result: SkillResult) -> str:
    drills = {
        "Python": "Parse one messy resume/JD file and return clean JSON with tests for missing fields.",
        "SQL": "Write 5 queries on one dataset: join, group by, CTE, window function, and duplicate check.",
        "React": "Build a filterable candidate table and profile one render bottleneck before optimizing it.",
        "TypeScript": "Type an API response as success/error unions and remove all unsafe any usage.",
        "Machine Learning": "Train a baseline classifier, choose precision/recall tradeoff, and explain threshold choice.",
        "LLM / Generative AI": "Build a tiny RAG evaluator with 5 questions, expected answers, and failure labels.",
        "Data Analysis": "Investigate a metric drop, segment the data, and write a 1-page insight memo.",
        "APIs": "Build one endpoint with validation, status codes, timeout handling, and idempotency notes.",
        "Testing": "Add unit, edge-case, and regression tests for a scoring function and report exporter.",
        "Communication": "Write a 5-bullet hiring-manager summary from a technical assessment report.",
    }
    return drills.get(result.name, f"Build a small role-relevant artifact proving {result.name}.")


def sprint_plan(result: SkillResult, weekly_hours: int) -> list[str]:
    hours = max(2, weekly_hours)
    return [
        f"Day 1: Review the highest-priority concept for {result.name} and write 5 notes from the course.",
        f"Day 2-3: Complete a hands-on drill for {min(hours, 4)} focused hours.",
        "Day 4: Add evidence: tests, screenshots, query outputs, notebook cells, or a short demo video.",
        "Day 5: Write a README explaining tradeoffs, failure cases, and what changed after feedback.",
        "Final: Re-answer the assessment question with the new artifact as proof.",
    ]


def readiness_summary(scored: ScoredAssessment) -> dict[str, int | str]:
    fully_verified = sum(1 for result in scored.skill_results if evidence_status(result) == "Verified")
    proof_backed = sum(1 for result in scored.skill_results if evidence_status(result) != "Unproven")
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
        "verified_skills": proof_backed,
        "proof_backed_skills": proof_backed,
        "fully_verified_skills": fully_verified,
        "gap_count": gaps,
        "high_priority_gap_count": high_priority_gaps,
    }


def primary_gap(scored: ScoredAssessment) -> SkillResult | None:
    if not scored.skill_results:
        return None
    gap_rank = {"High": 0, "Medium": 1, "Low": 2}
    criticality_rank = {"High": 0, "Medium": 1, "Resume-only": 2}
    gaps = [result for result in scored.skill_results if result.total_score < 70]
    ranked = gaps or scored.skill_results
    return sorted(
        ranked,
        key=lambda result: (
            gap_rank.get(gap_priority(result), 3),
            criticality_rank.get(result.criticality, 3),
            result.total_score,
        ),
    )[0]


def executive_summary(scored: ScoredAssessment) -> dict[str, str]:
    summary = readiness_summary(scored)
    gap = primary_gap(scored)
    strongest = ", ".join(scored.strongest_skills[:3]) if scored.strongest_skills else "No strong signals yet"
    if gap:
        risk_detail = gap.risk_flags[0] if gap.risk_flags else gap_reason(gap)
        main_risk = f"{gap.name}: {risk_detail}"
    else:
        main_risk = "No critical risk detected; use advanced calibration questions."

    next_action = (
        proof_task(gap)
        if gap
        else "Ask one advanced calibration question for each core skill and attach recent work samples."
    )
    return {
        "Decision snapshot": f"{summary['status']} at {scored.overall_score}% readiness.",
        "Proof coverage": (
            f"{summary['proof_backed_skills']} proof-backed skill(s), "
            f"{summary['fully_verified_skills']} fully verified skill(s), "
            f"{summary['gap_count']} skill(s) below threshold, "
            f"{summary['high_priority_gap_count']} high-priority gap(s). "
            "Fully verified means both resume evidence and assessment answers are strong."
        ),
        "Strongest signals": strongest,
        "Main hiring risk": main_risk,
        "Recommended next action": next_action,
        "Business value": (
            "Cuts manual claim-checking time, improves assessment accuracy with evidence and reason codes, "
            "and increases throughput by turning every skill review into a repeatable proof workflow."
        ),
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
                "Course path": course_path(result),
                "Practice drill": practice_drill(result),
                "Sprint plan": sprint_plan(result, weekly_hours),
                "Proof artifact": proof_task(result),
                "Learning style": learning_style,
                "Style tip": learning_style_tip(learning_style, result.name),
                "Why this gap": gap_reason(result),
                "Plan": result.learning_plan,
            }
        )
    return rows


def proof_ledger_rows(scored: ScoredAssessment) -> list[dict[str, str]]:
    rows = []
    for result in scored.skill_results:
        if evidence_status(result) == "Verified":
            audit_status = "Evidence-backed"
        elif result.assessment_score >= 25:
            audit_status = "Assessment-backed"
        elif result.resume_evidence_score > 0:
            audit_status = "Claim needs deeper proof"
        else:
            audit_status = "Unproven claim"

        rows.append(
            {
                "Skill claim": result.name,
                "JD priority": result.criticality,
                "Resume proof": result.evidence[0] if result.evidence else "No direct resume proof found",
                "Assessment proof": (
                    f"Answer quality {result.assessment_score}/45, depth {result.depth_score}/20"
                ),
                "Audit status": audit_status,
                "Why it matters": gap_reason(result),
                "Proof task": proof_task(result),
            }
        )
    return rows


def proof_task(result: SkillResult) -> str:
    adjacent = result.adjacent_skills[0] if result.adjacent_skills else "a related foundation"
    if result.total_score >= 75:
        return f"Ask one advanced calibration question and attach a recent {result.name} artifact."
    if result.total_score >= 50:
        return f"Build a small {result.name} artifact using {adjacent}, then explain tradeoffs and failure cases."
    return f"Complete a guided {result.name} mini-project, document the steps, and reassess with practical questions."


def build_markdown_report(scored: ScoredAssessment) -> str:
    summary = readiness_summary(scored)
    executive = executive_summary(scored)
    lines = [
        "# SkillProof AI Assessment Report",
        "",
        "## Executive Summary",
    ]
    lines.extend(f"- **{label}:** {value}" for label, value in executive.items())
    lines.extend(
        [
            "",
            "## Readiness Snapshot",
        ]
    )
    lines.extend([
        f"**Readiness status:** {summary['status']}",
        f"**Overall readiness:** {scored.overall_score}%",
        f"**Recommendation:** {scored.recommendation}",
        "",
        "## Summary",
        f"- Proof-backed skills: {summary['proof_backed_skills']} of {len(scored.skill_results)}",
        f"- Fully verified skills: {summary['fully_verified_skills']} of {len(scored.skill_results)}",
        f"- Skills below readiness threshold: {summary['gap_count']}",
        f"- High-priority gaps: {summary['high_priority_gap_count']}",
        "",
        "## Strongest Skills",
    ])
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
    lines.append("## Claim-To-Proof Ledger")
    for row in proof_ledger_rows(scored):
        lines.extend(
            [
                "",
                f"### {row['Skill claim']}",
                f"- JD priority: {row['JD priority']}",
                f"- Audit status: {row['Audit status']}",
                f"- Resume proof: {row['Resume proof']}",
                f"- Assessment proof: {row['Assessment proof']}",
                f"- Why it matters: {row['Why it matters']}",
                f"- Proof task: {row['Proof task']}",
            ]
        )

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
                    f"- Course path: {'; '.join(row['Course path']) if row['Course path'] else 'No curated course path available'}",
                    f"- Practice drill: {row['Practice drill']}",
                    f"- Proof artifact: {row['Proof artifact']}",
                    f"- Learning style tip: {row['Style tip']}",
                    f"- Sprint plan: {' / '.join(row['Sprint plan'])}",
                    f"- Plan: {row['Plan']}",
                ]
            )
    else:
        lines.append("- No immediate learning plan needed.")

    return "\n".join(lines)
