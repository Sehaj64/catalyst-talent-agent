from __future__ import annotations
import json
import urllib.error
import urllib.request
import re
from typing import Any
from skillproof.models import Question, SkillCandidate, ScoredAssessment
from skillproof.report import evidence_status, gap_priority, gap_reason, learning_plan_rows

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
GEMINI_MODEL = "gemini-2.5-pro"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/auto"
DEFAULT_ENDPOINT = GEMINI_ENDPOINT
DEFAULT_MODEL = GEMINI_MODEL

def assessment_payload(scored: ScoredAssessment, learning_style: str, weekly_hours: int) -> dict[str, Any]:
    return {
        "overall_score": scored.overall_score,
        "recommendation": scored.recommendation,
        "skills": [
            {
                "name": r.name,
                "score": r.total_score,
                "level": r.level,
                "gap_reason": gap_reason(r),
                "evidence": r.evidence[:3]
            } for r in scored.skill_results
        ]
    }

def call_gemini_native(api_key: str, system_message: str, user_prompt: str, history: list[dict[str, str]] = None) -> str:
    # Convert history (role/content) to Gemini contents (role/parts)
    contents = []
    if history:
        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn["content"]}]})
    
    # Add the current prompt
    contents.append({"role": "user", "parts": [{"text": user_prompt}]})

    body = {
        "system_instruction": {"parts": [{"text": system_message}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500}
    }
    
    url = f"{GEMINI_ENDPOINT}?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        # Fallback to a very simple prompt if complex one fails
        raise RuntimeError(f"Gemini Error: {str(e)}")

def parse_json_object(text: str) -> dict[str, Any]:
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except: pass
    return {}

def generate_assessment_question(skill: SkillCandidate, question: Question, api_key: str, endpoint: str, model: str, prior_turns: list[dict[str, str]] = None) -> dict[str, str]:
    system = "You are a Principal Systems Architect. Ask exactly ONE deep technical question to verify the candidate's claim. No fluff. Return JSON: {\"question\": \"...\", \"interviewer_intent\": \"...\"}"
    user = f"Skill: {skill.name}\nJD Mentions: {skill.jd_mentions[:2]}\nResume Claims: {skill.resume_evidence[:2]}"
    
    res = call_gemini_native(api_key, system, user, prior_turns)
    data = parse_json_object(res)
    return {"question": data.get("question", res), "interviewer_intent": data.get("interviewer_intent", "Verify depth")}

def generate_adaptive_follow_up(skill: SkillCandidate, question: Question, displayed_question: str, answer_text: str, api_key: str, endpoint: str, model: str) -> dict[str, str]:
    system = "You are a Proof-Hunter. Audit the candidate's answer. If vague, demand metrics/details. If strong, throw a curveball. Return JSON: {\"response_feedback\": \"...\", \"follow_up\": \"...\"}"
    user = f"Skill: {skill.name}\nQuestion Asked: {displayed_question}\nAnswer: {answer_text}"
    
    res = call_gemini_native(api_key, system, user)
    data = parse_json_object(res)
    return {"response_feedback": data.get("response_feedback", "Got it."), "follow_up": data.get("follow_up", res)}

def generate_personalized_learning_plan(scored: ScoredAssessment, learning_style: str, weekly_hours: int, api_key: str, endpoint: str, model: str) -> list[dict[str, Any]]:
    system = "Architect an elite 'Zero-to-Hero' roadmap for the gaps found. Return JSON: {\"plans\": [{\"skill\": \"...\", \"priority\": \"...\", \"target_level\": \"...\", \"why_now\": \"...\", \"estimated_hours\": \"...\", \"course_path\": [], \"proof_artifact\": \"...\", \"retest_prompt\": \"...\"}]}"
    user = json.dumps(assessment_payload(scored, learning_style, weekly_hours))
    
    res = call_gemini_native(api_key, system, user)
    data = parse_json_object(res)
    return data.get("plans", [])

def generate_ai_review(scored: ScoredAssessment, learning_style: str, weekly_hours: int, api_key: str, endpoint: str, model: str) -> str:
    system = "Provide a 1-paragraph high-level executive summary of this candidate's technical readiness and upskilling ROI."
    user = json.dumps(assessment_payload(scored, learning_style, weekly_hours))
    return call_gemini_native(api_key, system, user)
