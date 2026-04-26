from __future__ import annotations

from io import BytesIO
import unittest

from skillproof.ai_assist import (
    assessment_payload,
    build_follow_up_prompt,
    build_learning_plan_prompt,
    build_question_prompt,
    build_reviewer_prompt,
    parse_json_object,
)
from skillproof.assessment import (
    answer_key,
    build_assessment,
    contextual_question_prompt,
    follow_up_key,
    follow_up_prompt,
    score_assessment,
)
from skillproof.file_readers import read_file_bytes
from skillproof.report import build_markdown_report, executive_summary, learning_plan_rows, proof_ledger_rows
from skillproof.sample_data import SAMPLE_ANSWERS, SAMPLE_JD, SAMPLE_RESUME


class SkillProofTests(unittest.TestCase):
    def test_extracts_core_skills_from_sample(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        names = {skill.name for skill in assessment.skills}
        self.assertIn("Python", names)
        self.assertIn("React", names)
        self.assertIn("Testing", names)

    def test_dynamic_fallback_covers_role_specific_jds(self) -> None:
        jd = """
        Growth Marketing Analyst
        Required skills: SEO, Google Ads, conversion rate optimization, content calendar, and A/B testing.
        Must have experience with campaign reporting and stakeholder dashboards.
        """
        resume = """
        Ran SEO audits and Google Ads experiments for a campus startup.
        Improved conversion rate by 18% and maintained a weekly content calendar.
        """
        assessment = build_assessment(jd, resume)
        skills = {skill.name: skill for skill in assessment.skills}

        self.assertIn("SEO", skills)
        self.assertIn("Google Ads", skills)
        self.assertEqual("Marketing / Growth", skills["SEO"].category)
        self.assertTrue(skills["SEO"].questions)
        self.assertTrue(skills["SEO"].resources)
        self.assertTrue(skills["SEO"].resume_evidence)

    def test_scores_and_generates_report(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        scored = score_assessment(assessment, SAMPLE_ANSWERS)
        self.assertGreater(scored.overall_score, 50)
        report = build_markdown_report(scored)
        summary = executive_summary(scored)
        self.assertIn("Main hiring risk", summary)
        self.assertIn("proof-backed", summary["Proof coverage"])
        self.assertIn("Overall readiness", report)
        self.assertIn("Executive Summary", report)
        self.assertIn("Claim-To-Proof Ledger", report)
        self.assertIn("Personalized Learning Plan", report)

    def test_adaptive_follow_up_affects_scoring(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        skill = assessment.skills[0]
        question = skill.questions[0]
        base_key = answer_key(skill.name, question.prompt)
        extra_key = follow_up_key(skill.name, question.prompt)
        prompt = follow_up_prompt(skill.name, question.prompt, "I used it in a project.", question.signals)

        self.assertTrue("Where did" in prompt or "What" in prompt)

        without_follow_up = score_assessment(assessment, {base_key: "I used it in a project."})
        with_follow_up = score_assessment(
            assessment,
            {
                base_key: "I used it in a project.",
                extra_key: (
                    "I built a validation artifact, measured a 20% quality improvement, "
                    "documented the failure case, and explained the tradeoff to the stakeholder."
                ),
            },
        )

        self.assertGreater(
            with_follow_up.skill_results[0].assessment_score,
            without_follow_up.skill_results[0].assessment_score,
        )
        self.assertIn("answered_adaptive_follow_up", with_follow_up.skill_results[0].reason_codes)

    def test_contextual_questions_change_with_resume_evidence(self) -> None:
        jd = "Required skills: Python for pricing automation."
        resume_a = "Built Python scripts for invoice cleanup and reduced errors by 20%."
        resume_b = "Used Python notebooks for customer churn analysis and retention reporting."

        assessment_a = build_assessment(jd, resume_a)
        assessment_b = build_assessment(jd, resume_b)
        skill_a = next(skill for skill in assessment_a.skills if skill.name == "Python")
        skill_b = next(skill for skill in assessment_b.skills if skill.name == "Python")

        question_a = contextual_question_prompt(skill_a, skill_a.questions[0])
        question_b = contextual_question_prompt(skill_b, skill_b.questions[0])

        self.assertNotEqual(question_a, question_b)
        self.assertIn("invoice cleanup", question_a)
        self.assertIn("churn analysis", question_b)

    def test_learning_plan_rows_include_gaps(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        scored = score_assessment(assessment, SAMPLE_ANSWERS)
        plans = learning_plan_rows(scored)
        self.assertTrue(plans)
        self.assertIn("Timeline", plans[0])
        self.assertIn("Course path", plans[0])
        self.assertIn("Practice drill", plans[0])
        self.assertIn("Sprint plan", plans[0])
        self.assertIn("Proof artifact", plans[0])

    def test_sample_answers_are_skill_specific(self) -> None:
        answers = [answer for answer in SAMPLE_ANSWERS.values() if answer.strip()]
        self.assertGreater(len(set(answers)), 15)
        self.assertEqual(len(answers), len(set(answers)))

    def test_reused_generic_answers_are_penalized(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        generic_answer = (
            "I worked on a project where I made reliable output, handled speed versus correctness, "
            "document assumptions, and explained business impact to the stakeholder."
        )
        repeated_answers = {
            answer_key(skill.name, question.prompt): generic_answer
            for skill in assessment.skills
            for question in skill.questions
        }
        scored = score_assessment(assessment, repeated_answers)

        self.assertLess(scored.overall_score, 60)
        self.assertTrue(
            any("reused_answer_pattern" in result.reason_codes for result in scored.skill_results)
        )

    def test_proof_ledger_traces_claims_to_tasks(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        scored = score_assessment(assessment, SAMPLE_ANSWERS)
        rows = proof_ledger_rows(scored)

        self.assertTrue(rows)
        self.assertIn("Resume proof", rows[0])
        self.assertIn("Assessment proof", rows[0])
        self.assertIn("Proof task", rows[0])

    def test_reads_csv_as_structured_evidence(self) -> None:
        content = b"name,skills,impact\nSehaj,Python and React,Automated 40 hours of review\n"
        text = read_file_bytes("candidate.csv", content)
        self.assertIn("skills: Python and React", text)
        self.assertIn("impact: Automated 40 hours of review", text)

    def test_reads_docx_and_xlsx_files(self) -> None:
        from docx import Document
        from openpyxl import Workbook

        docx_buffer = BytesIO()
        document = Document()
        document.add_paragraph("Built Python APIs and React dashboards.")
        document.save(docx_buffer)

        xlsx_buffer = BytesIO()
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "ATS export"
        sheet.append(["Skill", "Evidence"])
        sheet.append(["Testing", "Wrote regression tests for scoring engine"])
        workbook.save(xlsx_buffer)

        self.assertIn("Python APIs", read_file_bytes("resume.docx", docx_buffer.getvalue()))
        self.assertIn("Skill: Testing", read_file_bytes("candidate.xlsx", xlsx_buffer.getvalue()))

    def test_ai_reviewer_prompt_uses_structured_payload(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        scored = score_assessment(assessment, SAMPLE_ANSWERS)
        payload = assessment_payload(scored, "Project-based", 6)
        prompt = build_reviewer_prompt(scored, "Project-based", 6)

        self.assertIn("overall_score", payload)
        self.assertIn("Business Impact Story", prompt)
        self.assertNotIn(SAMPLE_RESUME[:80], prompt)
        self.assertNotIn(SAMPLE_JD[:80], prompt)

    def test_llm_question_prompt_is_evidence_bound_json_task(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        skill = assessment.skills[0]
        question = skill.questions[0]
        prompt = build_question_prompt(skill, question)
        parsed = parse_json_object('```json\n{"question": "What did you build?", "interviewer_intent": "Probe evidence"}\n```')

        self.assertIn(skill.name, prompt)
        self.assertIn("Return JSON only", prompt)
        self.assertEqual("What did you build?", parsed["question"])

    def test_ai_learning_plan_prompt_requests_structured_roadmap(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        scored = score_assessment(assessment, SAMPLE_ANSWERS)
        prompt = build_learning_plan_prompt(scored, "Project-based", 6)

        self.assertIn("personalized learning roadmap", prompt)
        self.assertIn("course_path", prompt)
        self.assertIn("proof_artifact", prompt)
        self.assertIn("Return JSON only", prompt)

    def test_follow_up_prompt_requests_natural_feedback(self) -> None:
        assessment = build_assessment(SAMPLE_JD, SAMPLE_RESUME)
        skill = assessment.skills[0]
        question = skill.questions[0]
        prompt = build_follow_up_prompt(skill, question, "What did you build?", "I built a dashboard.")

        self.assertIn("response_feedback", prompt)
        self.assertIn("real back-and-forth interview", prompt)


if __name__ == "__main__":
    unittest.main()
