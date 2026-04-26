from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from skillproof.models import Question, SkillCandidate, ScoredAssessment
from skillproof.report import evidence_status, gap_priority, gap_reason, learning_plan_rows


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
GEMINI_MODEL = "gemini-2.5-pro"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/auto"
DEFAULT_ENDPOINT = GEMINI_ENDPOINT
DEFAULT_MODEL = GEMINI_MODEL


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
                "adjacent_skills": result.adjacent_skills,
                "resources": result.resources,
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
    system_message: str = (
        "You are a Senior Principal Engineer and Technical Architect. "
        "Your responses are high-density, technically precise, and focused on real-world implementation depth."
    ),
    temperature: float = 0.3,
    max_tokens: int = 1500,
) -> str:
    if "googleapis.com" in endpoint:
        # Native Gemini REST endpoint format
        url = f"{endpoint}?key={api_key}"
        body = {
            "system_instruction": {"parts": [{"text": system_message + " DO NOT use any restricted or unsafe language. Stay focused on professional technical architecture. Do not use markdown formatting in the question itself."}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95,
            }
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
            data = json.loads(response_body)
            
            # Robust parsing of Gemini response
            if "candidates" not in data or not data["candidates"]:
                if "error" in data:
                    raise RuntimeError(f"Gemini Error: {data['error'].get('message', 'Unknown error')}")
                raise RuntimeError("Gemini returned no candidates. This usually means the prompt was blocked or filtered.")
            
            candidate = data["candidates"][0]
            content = candidate.get("content")
            if not content or "parts" not in content or not content["parts"]:
                finish_reason = candidate.get("finishReason", "Unknown")
                safety_ratings = candidate.get("safetyRatings", [])
                raise RuntimeError(f"Gemini blocked or returned empty content. Reason: {finish_reason}. Safety: {safety_ratings}")
                
            return content["parts"][0]["text"].strip()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini API request failed: HTTP {error.code}. {detail[:240]}") from error
        except Exception as error:
            raise RuntimeError(f"Gemini API request failed: {error}") from error

    # Default to OpenAI / OpenRouter format
    body = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": system_message,
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


def build_question_prompt(
    skill: SkillCandidate,
    question: Question,
    prior_turns: list[dict[str, str]] | None = None,
) -> str:
    payload = {
        "skill": skill.name,
        "history": prior_turns or [],
    }
    return (
        "TASK: Senior-Level Technical Assessment for a high-stakes engineering role. \n"
        "IDENTITY: Principal Systems Architect. \n"
        "QUALITY PROTOCOL:\n"
        "1. ANALYSIS: Review the 'history'. Identify unverified areas (concurrency, data integrity, cost).\n"
        "2. SCENARIO: Design a complex, real-world failure or scaling bottleneck related to the skill. \n"
        "3. PRECISION: Ask about specific implementation details.\n"
        "4. BREVITY: Exactly 1 sentence. No preambles.\n\n"
        "Return JSON: { \"question\": \"...\", \"interviewer_intent\": \"...\" }\n\n"
        + json.dumps(payload, indent=2)
    )


import re

def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    # Try finding an object or array using regex
    match = re.search(r'(\{.*\}|\[.*\])', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise ValueError(f"Regex found JSON-like structure but it was invalid: {e}. Text: {text}")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON: {e}. Text: {text}")


def coerce_string_list(value: Any, limit: int) -> list[str]:
    if isinstance(value, list):
        items = value
    elif value:
        items = [value]
    else:
        items = []
    return [str(item).strip() for item in items if str(item).strip()][:limit]


def generate_assessment_question(
    skill: SkillCandidate,
    question: Question,
    api_key: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
    prior_turns: list[dict[str, str]] | None = None,
) -> dict[str, str]:
    response = call_openai_compatible(
        api_key,
        endpoint,
        model,
        build_question_prompt(skill, question, prior_turns),
        timeout_seconds=18,
        system_message=(
            "You are an expert skill interviewer. Ask natural, practical, role-specific, "
            "evidence-bound questions from the exact JD, resume evidence, and interview context. "
            "Return valid JSON only."
        ),
        temperature=0.62,
        max_tokens=360,
    )
    data = parse_json_object(response)
    generated = str(data.get("question", "")).strip()
    intent = str(data.get("interviewer_intent", "")).strip()
    if len(generated) < 20:
        raise RuntimeError("AI question was too short to use.")
    return {"question": generated, "interviewer_intent": intent}


def build_follow_up_prompt(
    skill: SkillCandidate,
    question: Question,
    displayed_question: str,
    answer_text: str,
) -> str:
    payload = {
        "skill": skill.name,
        "asked": displayed_question,
        "answer": answer_text,
    }
    return (
        "TASK: Audit technical authenticity. \n"
        "IDENTITY: Lead Engineer. \n"
        "INSTRUCTIONS:\n"
        "1. FLUFF: If generic, call it out and demand an exact tool or metric.\n"
        "2. PIVOT: If strong, ask about a 'Deep Constraint' (memory, throughput, cost).\n"
        "3. STRUCTURE: 1 short feedback sentence + 1 high-stakes question.\n\n"
        "Return JSON: { \"response_feedback\": \"...\", \"follow_up\": \"...\", \"why\": \"...\" }\n\n"
        + json.dumps(payload, indent=2)
    )


def generate_adaptive_follow_up(
    skill: SkillCandidate,
    question: Question,
    displayed_question: str,
    answer_text: str,
    api_key: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
) -> dict[str, str]:
    response = call_openai_compatible(
        api_key,
        endpoint,
        model,
        build_follow_up_prompt(skill, question, displayed_question, answer_text),
        timeout_seconds=18,
        system_message=(
            "You are an expert interviewer. Ask one concise follow-up based only on the candidate answer. "
            "Return valid JSON only."
        ),
        temperature=0.35,
        max_tokens=300,
    )
    data = parse_json_object(response)
    feedback = str(data.get("response_feedback", "")).strip()
    follow_up = str(data.get("follow_up", "")).strip()
    why = str(data.get("why", "")).strip()
    if len(follow_up) < 20:
        raise RuntimeError("AI follow-up was too short to use.")
    return {"response_feedback": feedback, "follow_up": follow_up, "why": why}


def build_learning_plan_prompt(
    scored: ScoredAssessment,
    learning_style: str,
    weekly_hours: int,
) -> str:
    payload = assessment_payload(scored, learning_style, weekly_hours)
    return (
        "TASK: Create a technical upskilling roadmap for a Senior Engineer. \n"
        "IDENTITY: Technical Architect. \n"
        "RULES:\n"
        "1. NO FLUFF: Use technical bullet points. Focus on implementation over theory.\n"
        "2. GAP FOCUS: Only list skills where the candidate failed verification.\n"
        "3. PROOF TASK: Provide exactly ONE measurable project (the 'Proof Artifact') per gap.\n"
        "4. ESTIMATES: Provide realistic, aggressive timelines.\n\n"
        "Return JSON EXACTLY in this format:\n"
        "{\n"
        "  \"plans\": [\n"
        "    {\n"
        "      \"skill\": \"Skill Name\",\n"
        "      \"priority\": \"High/Medium/Low\",\n"
        "      \"target_level\": \"E.g., Master distributed sharding\",\n"
        "      \"why_now\": \"High-level risk explanation\",\n"
        "      \"adjacent_bridge\": \"Short link to what they already know\",\n"
        "      \"estimated_hours\": \"Time\",\n"
        "      \"course_path\": [\"Documentation link\", \"Advanced course\"],\n"
        "      \"weekly_schedule\": [\"Action 1\", \"Action 2\"],\n"
        "      \"practice_drill\": \"Short technical exercise\",\n"
        "      \"proof_artifact\": \"THE PROJECT TO BUILD\",\n"
        "      \"retest_prompt\": \"One killer technical question\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        + json.dumps(payload, indent=2)
    )


def generate_personalized_learning_plan(
    scored: ScoredAssessment,
    learning_style: str,
    weekly_hours: int,
    api_key: str,
    endpoint: str = DEFAULT_ENDPOINT,
    model: str = DEFAULT_MODEL,
) -> list[dict[str, Any]]:
    response = call_openai_compatible(
        api_key,
        endpoint,
        model,
        build_learning_plan_prompt(scored, learning_style, weekly_hours),
        timeout_seconds=30,
        system_message=(
            "You are an expert career coach and hiring enablement analyst. "
            "Create realistic, skill-specific learning roadmaps with courses, drills, proof artifacts, and time estimates. "
            "Return valid JSON only."
        ),
        temperature=0.38,
        max_tokens=1800,
    )
    data = parse_json_object(response)
    plans = data.get("plans", [])
    if not isinstance(plans, list) or not plans:
        raise RuntimeError("AI learning planner returned no plans.")

    cleaned_plans: list[dict[str, Any]] = []
    for plan in plans[:8]:
        if not isinstance(plan, dict):
            continue
        cleaned_plans.append(
            {
                "skill": str(plan.get("skill", "")).strip(),
                "priority": str(plan.get("priority", "")).strip(),
                "target_level": str(plan.get("target_level", "")).strip(),
                "why_now": str(plan.get("why_now", "")).strip(),
                "adjacent_bridge": str(plan.get("adjacent_bridge", "")).strip(),
                "estimated_hours": str(plan.get("estimated_hours", "")).strip(),
                "course_path": coerce_string_list(plan.get("course_path", []), 4),
                "weekly_schedule": coerce_string_list(plan.get("weekly_schedule", []), 7),
                "practice_drill": str(plan.get("practice_drill", "")).strip(),
                "proof_artifact": str(plan.get("proof_artifact", "")).strip(),
                "retest_prompt": str(plan.get("retest_prompt", "")).strip(),
            }
        )
    if not cleaned_plans:
        raise RuntimeError("AI learning planner returned an unexpected response shape.")
    return cleaned_plans
