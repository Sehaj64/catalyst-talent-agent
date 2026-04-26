from __future__ import annotations

from skillproof.taxonomy import SKILLS


SAMPLE_JD = """
Frontend AI Product Engineer

We need a developer who can build production-minded assessment tools for hiring teams.
Required skills: Python, React, TypeScript, REST APIs, testing, and clear communication.
The role will work with LLM / Generative AI workflows, prompt evaluation, and data analysis dashboards.
Must have strong experience turning messy business requirements into reliable user-facing software.
Preferred: SQL, machine learning basics, and product workflow understanding.
"""


SAMPLE_RESUME = """
Sehaj Kumar

Built a Python resume analyzer that parsed candidate profiles and generated structured reports.
Implemented a React and TypeScript dashboard for project tracking with filters, reusable components, typed API responses, and REST API integration.
Created data analysis notebooks using pandas and basic SQL joins for college placement insights.
Worked on a GenAI chatbot prototype using prompts and retrieval-style context.
Wrote unit tests for scoring utilities and documented setup steps for teammates.
Improved project delivery speed by 30% by writing documentation, presenting tradeoffs to stakeholders, and fixing deployment issues.
"""


def _sample_answers() -> dict[str, str]:
    answers: dict[str, str] = {}
    for skill_name, config in SKILLS.items():
        for question in config["questions"]:
            key = f"{skill_name}::{question.prompt}"
            signals = ", ".join(question.signals[:4])
            answers[key] = (
                f"I implemented {skill_name} in a project where I had to design the input, validate edge cases, "
                "debug failures, and produce a reliable output. The main tradeoff was speed versus correctness, "
                f"so I focused on {signals}. I started with a simple baseline, measured errors, and improved "
                "the workflow until it saved about 30% manual effort. I would document assumptions, add tests, "
                "monitor failure cases, and explain the business impact to the stakeholder."
            )
    return answers


SAMPLE_ANSWERS = _sample_answers()
