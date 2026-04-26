from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skillproof.models import ScoredAssessment
from skillproof.report import evidence_status, gap_priority, gap_reason, learning_plan_rows


DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/auto"


def assessment_payload(
    scored: ScoredAssessment,
    learning_style: str,
    weekly_hours: int,
) -> dict[str, Any]:
    return {
        "overall_score": scored.overall_score,
        "recommendation": scored.recommendation,
        "strongest_skills": scored.strongest_skills,
        "highest_risks": scored.highest_risks,
        "skills": [
            {
                "name": result.name,
                "category": result.category,
                "criticality": result.criticality,
                "score": result.total_score,
                "level": result.level,
                "evidence_status": evidence_status(result),
                "gap_priority": gap_priority(result),
                "gap_reason": gap_reason(result),
                "reason_codes": result.reason_codes,
                "risk_flags": result.risk_flags,
            }
            for result in scored.skill_results
        ],
        "learning_plan": learning_plan_rows(scored, learning_style, weekly_hours),
    }


def build_reviewer_prompt(
    scored: ScoredAssessment,
    learning_style: str,
    weekly_hours: int,
) -> str:
    payload = assessment_payload(scored, learning_style, weekly_hours)
    return (
        "Review this structured skill assessment payload. Do not invent candidate facts. "
        "Use only the scores, reason codes, gap reasons, and learning plan rows. "
        "Write concise judge-ready notes with these sections: "
        "1) Calibration Summary, 2) Highest Assessment Risks, "
        "3) Learning Plan Tightening, 4) Business Impact Story. "
        "Avoid hire/no-hire decisions; focus on proficiency evidence, gaps, and upskilling ROI.\n\n"
        + json.dumps(payload, indent=2)
    )


def call_openai_compatible(
    api_key: str,
    endpoint: str,
    model: str,
    prompt: str,
    timeout_seconds: int = 30,
) -> str:
    body = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 900,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful skill-assessment calibration reviewer. "
                    "Be specific, concise, and evidence-bound."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Sehaj64/catalyst-talent-agent",
            "X-Title": "SkillProof AI",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"AI reviewer request failed: HTTP {error.code}. {detail[:240]}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"AI reviewer request failed: {error.reason}") from error

    data = json.loads(response_body)
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("AI reviewer returned an unexpected response shape.") from error


def generate_ai_review(
    scored: ScoredAssessment,
    learning_style: str,
    weekly_hours: int,
    api_key: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
) -> str:
    prompt = build_reviewer_prompt(scored, learning_style, weekly_hours)
    return call_openai_compatible(api_key, endpoint, model, prompt)
