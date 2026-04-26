from __future__ import annotations

import importlib

import streamlit as st

from skillproof.assessment import answer_key, build_assessment, score_assessment
import skillproof.file_readers as file_readers
from skillproof.report import (
    accuracy_lift_estimate,
    build_markdown_report,
    evidence_status,
    gap_reason,
    gap_priority,
    learning_plan_rows,
    roi_projection,
    readiness_summary,
    skill_choice_reason,
)
from skillproof.sample_data import SAMPLE_ANSWERS, SAMPLE_JD, SAMPLE_RESUME


file_readers = importlib.reload(file_readers)
UPLOAD_TYPES = file_readers.supported_upload_types()
FORMAT_LABEL = "PDF, DOCX, TXT/MD, CSV, or XLSX"


st.set_page_config(
    page_title="SkillProof AI",
    page_icon="SP",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.25rem; }
    .hero {
        border: 1px solid #d0d7e2;
        background: #f8fafc;
        padding: 18px 20px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    .hero h1 {
        margin: 0 0 6px 0;
        font-size: 2rem;
        line-height: 1.15;
    }
    .hero p {
        margin: 0;
        color: #475467;
        font-size: 1rem;
    }
    .metric-card {
        border: 1px solid #d0d7e2;
        border-radius: 8px;
        padding: 14px 16px;
        background: white;
        min-height: 104px;
    }
    .metric-card .label {
        color: #667085;
        font-size: .82rem;
        margin-bottom: 8px;
    }
    .metric-card .value {
        color: #101828;
        font-size: 1.45rem;
        font-weight: 720;
        margin-bottom: 5px;
    }
    .metric-card .note {
        color: #475467;
        font-size: .86rem;
    }
    .section-note {
        color: #475467;
        font-size: .92rem;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_state() -> None:
    defaults = {
        "jd_text": "",
        "resume_text": "",
        "assessment": None,
        "answers": {},
        "scored": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_sample() -> None:
    st.session_state.jd_text = SAMPLE_JD
    st.session_state.resume_text = SAMPLE_RESUME
    st.session_state.answers = SAMPLE_ANSWERS.copy()
    st.session_state.assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
    st.session_state.scored = None


def run_sample() -> None:
    load_sample()
    st.session_state.scored = score_assessment(
        st.session_state.assessment,
        st.session_state.answers,
    )


def analyze_inputs() -> None:
    st.session_state.assessment = build_assessment(
        st.session_state.jd_text,
        st.session_state.resume_text,
    )
    st.session_state.scored = None


def score_current_assessment() -> None:
    st.session_state.scored = score_assessment(
        st.session_state.assessment,
        st.session_state.answers,
    )


def apply_upload(target_key: str, uploaded_file) -> None:
    if uploaded_file is None:
        return
    text = file_readers.read_uploaded_file(uploaded_file)
    if text:
        st.session_state[target_key] = text
        st.caption(f"Parsed {len(text):,} characters from {uploaded_file.name}.")
    else:
        st.warning(f"Could not read {uploaded_file.name}. Please paste the text manually.")


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def skill_matrix_rows() -> list[dict[str, str | int]]:
    assessment = st.session_state.assessment
    if not assessment:
        return []
    return [
        {
            "Skill": skill.name,
            "Category": skill.category,
            "JD priority": skill.criticality,
            "Resume evidence snippets": len(skill.resume_evidence),
            "Questions": len(skill.questions),
            "Why chosen": (
                "Required or role-relevant skill from the JD"
                if skill.criticality in {"High", "Medium"}
                else "Resume skill that may support adjacent learning"
            ),
        }
        for skill in assessment.skills
    ]


ensure_state()

st.markdown(
    """
    <div class="hero">
        <h1>SkillProof AI</h1>
        <p>Assess real proficiency from a JD and resume, identify gaps, and generate a personalized adjacent-skill learning plan.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Personalization")
    learning_style = st.selectbox(
        "Preferred learning style",
        ["Project-based", "Video-first", "Docs-first", "Practice drills"],
    )
    weekly_hours = st.slider("Available learning hours / week", 2, 20, 6, 1)
    st.divider()
    st.header("ROI assumptions")
    candidates = st.slider("Candidates assessed / month", 10, 500, 60, 10)
    manual_minutes = st.slider("Manual assessment minutes", 20, 90, 55, 5)
    agent_minutes = st.slider("SkillProof assessment minutes", 5, 30, 14, 1)
    hourly_cost = st.slider("Reviewer cost / hour (INR)", 300, 3000, 1000, 100)
    st.divider()
    st.caption("No API key required. The prototype uses deterministic scoring so the demo is reliable.")
    with st.expander("Demo helper"):
        st.button("Load sample inputs", use_container_width=True, on_click=load_sample)
        st.button("Run sample end-to-end", use_container_width=True, on_click=run_sample)

scored = st.session_state.scored
summary = readiness_summary(scored) if scored else None
roi = roi_projection(candidates, manual_minutes, agent_minutes, hourly_cost)

if scored:
    top_cols = st.columns(4)
    with top_cols[0]:
        metric_card("Readiness status", str(summary["status"]), "Generated after the skill conversation.")
    with top_cols[1]:
        metric_card("Overall score", f"{scored.overall_score}%", "Weighted by JD skill priority.")
    with top_cols[2]:
        metric_card("Verified skills", str(summary["verified_skills"]), "Backed by evidence and answers.")
    with top_cols[3]:
        metric_card("Skill gaps", str(summary["gap_count"]), "Below readiness threshold.")

tabs = st.tabs(
    [
        "Inputs",
        "Skill Conversation",
        "Gap Analysis",
        "Learning Plan",
        "ROI Dashboard",
        "Export",
    ]
)

with tabs[0]:
    st.subheader("Inputs")
    st.markdown(
        f'<div class="section-note">Upload {FORMAT_LABEL} files or paste text manually. Spreadsheets are flattened with row and column labels so ATS exports and skill matrices still become assessment evidence.</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**Job Description**")
        jd_file = st.file_uploader(f"Upload JD as {FORMAT_LABEL}", type=UPLOAD_TYPES, key="jd_upload")
        apply_upload("jd_text", jd_file)
        st.session_state.jd_text = st.text_area(
            "Paste or edit job description",
            value=st.session_state.jd_text,
            height=340,
        )
    with right:
        st.markdown("**Candidate Resume**")
        resume_file = st.file_uploader(f"Upload resume as {FORMAT_LABEL}", type=UPLOAD_TYPES, key="resume_upload")
        apply_upload("resume_text", resume_file)
        st.session_state.resume_text = st.text_area(
            "Paste or edit candidate resume",
            value=st.session_state.resume_text,
            height=340,
        )

    if st.button("Extract required skills", type="primary"):
        if not st.session_state.jd_text.strip() or not st.session_state.resume_text.strip():
            st.warning("Paste both the JD and resume first.")
        else:
            analyze_inputs()
            st.success("Skills extracted. Continue to Skill Conversation.")

    with st.expander("Real workflow fit", expanded=False):
        st.dataframe(
            [
                {
                    "Business workflow": "Recruiter receives JD/resume documents",
                    "Covered by": "PDF, DOCX, TXT/MD upload or paste",
                    "Impact": "Less manual copying before assessment",
                },
                {
                    "Business workflow": "ATS or spreadsheet export",
                    "Covered by": "CSV/XLSX ingestion with row and column context",
                    "Impact": "Batch-style evidence can be converted into auditable text",
                },
                {
                    "Business workflow": "Manager needs proof, not claims",
                    "Covered by": "Question answers, evidence snippets, score breakdown, reason codes",
                    "Impact": "Higher accuracy and fewer unstructured review cycles",
                },
            ],
            hide_index=True,
            use_container_width=True,
        )

    if st.session_state.assessment:
        st.markdown("**Extracted skill matrix**")
        st.dataframe(skill_matrix_rows(), hide_index=True, use_container_width=True)

with tabs[1]:
    st.subheader("Skill Conversation")
    assessment = st.session_state.assessment
    if not assessment:
        st.info("Extract required skills from the Inputs tab first.")
    else:
        st.markdown(
            '<div class="section-note">Answer the targeted questions for each required skill. Good answers mention examples, tradeoffs, failures, and measurable outcomes.</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Fill sample answers"):
                st.session_state.answers.update(SAMPLE_ANSWERS)
                st.success("Sample answers filled.")
        with col_b:
            if st.button("Score proficiency", type="primary"):
                score_current_assessment()
                st.success("Assessment scored. Continue to Gap Analysis.")

        for skill in assessment.skills:
            with st.expander(f"{skill.name} | {skill.criticality} priority", expanded=skill.criticality == "High"):
                if skill.resume_evidence:
                    st.markdown("**Resume evidence**")
                    for snippet in skill.resume_evidence[:2]:
                        st.code(snippet)
                else:
                    st.warning("No direct resume evidence found for this skill.")

                st.markdown("**Assessment questions**")
                for question in skill.questions:
                    key = answer_key(skill.name, question.prompt)
                    st.session_state.answers[key] = st.text_area(
                        question.prompt,
                        value=st.session_state.answers.get(key, ""),
                        height=105,
                        key=key,
                    )

with tabs[2]:
    st.subheader("Gap Analysis")
    scored = st.session_state.scored
    if not scored:
        st.info("Score the skill conversation first.")
    else:
        rows = []
        for result in scored.skill_results:
            rows.append(
                {
                    "Skill": result.name,
                    "Score": result.total_score,
                    "Level": result.level,
                    "JD priority": result.criticality,
                    "Evidence": evidence_status(result),
                    "Gap priority": gap_priority(result),
                    "Why chosen": skill_choice_reason(result),
                    "Why gap was detected": gap_reason(result),
                    "Notes": "; ".join(result.risk_flags) if result.risk_flags else "No major gap",
                }
            )
        st.dataframe(rows, hide_index=True, use_container_width=True)

        st.markdown("**Score breakdown**")
        for result in scored.skill_results:
            with st.expander(f"{result.name}: {result.total_score}/100 ({result.level})"):
                st.write("Resume evidence:", f"{result.resume_evidence_score}/25")
                st.write("Answer quality:", f"{result.assessment_score}/45")
                st.write("Practical depth:", f"{result.depth_score}/20")
                st.write("Confidence:", f"{result.confidence_score}/10")
                st.write("Reason codes:", ", ".join(result.reason_codes))
                st.write("Why this skill was chosen:", skill_choice_reason(result))
                st.write("Why this gap was detected:", gap_reason(result))

with tabs[3]:
    st.subheader("Personalized Learning Plan")
    scored = st.session_state.scored
    if not scored:
        st.info("Score the skill conversation first.")
    else:
        st.markdown(
            f"Learning style: **{learning_style}** | Available time: **{weekly_hours} hrs/week**"
        )
        plans = learning_plan_rows(scored, learning_style, weekly_hours)
        if not plans:
            st.success("No major learning gaps found.")
        for row in plans:
            with st.expander(f"{row['Skill']} | {row['Priority']} priority | {row['Timeline']}", expanded=True):
                st.write(row["Goal"])
                st.write(row["Why this gap"])
                st.write(
                    "Adjacent skills:",
                    ", ".join(row["Adjacent skills"]) if row["Adjacent skills"] else "related fundamentals",
                )
                st.write("Learning style adaptation:", row["Style tip"])
                st.markdown("**Curated resources**")
                for resource in row["Resources"]:
                    st.write(f"- {resource}")
                st.write(row["Plan"])

with tabs[4]:
    st.subheader("ROI Dashboard")
    st.markdown(
        '<div class="section-note">Estimated business impact from replacing manual claim-checking with structured skill assessment.</div>',
        unsafe_allow_html=True,
    )
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        metric_card("Cost saved", f"INR {roi['monthly_cost_saved']:,}", "Estimated monthly review cost saved.")
    with r2:
        metric_card("Throughput gain", f"{roi['throughput_gain']}x", "More candidates assessed in the same time.")
    with r3:
        metric_card("Time saved", f"{roi['monthly_hours_saved']} hrs", "Estimated monthly hours saved.")
    with r4:
        metric_card("Accuracy improved", f"+{accuracy_lift_estimate(scored)}%", "Estimated lift from evidence and answer coverage.")

    st.dataframe(
        [
            {
                "Metric": "Manual process",
                "Value": f"{manual_minutes} minutes per candidate",
                "Meaning": "Resume claims checked manually.",
            },
            {
                "Metric": "SkillProof process",
                "Value": f"{agent_minutes} minutes per candidate",
                "Meaning": "Structured assessment plus explainable scoring.",
            },
            {
                "Metric": "Monthly cost saved",
                "Value": f"INR {roi['monthly_cost_saved']:,}",
                "Meaning": "Based on candidate volume, time saved, and hourly cost assumptions.",
            },
            {
                "Metric": "Estimated accuracy improved",
                "Value": f"+{accuracy_lift_estimate(scored)}%",
                "Meaning": "Heuristic lift from evidence coverage, answers, and reason codes.",
            },
        ],
        hide_index=True,
        use_container_width=True,
    )

with tabs[5]:
    st.subheader("Export")
    scored = st.session_state.scored
    if not scored:
        st.info("Score the assessment first.")
    else:
        report = build_markdown_report(scored)
        st.markdown("**Report preview**")
        st.markdown(report)
        st.download_button(
            "Download assessment report",
            data=report,
            file_name="skillproof-assessment-report.md",
            mime="text/markdown",
        )
