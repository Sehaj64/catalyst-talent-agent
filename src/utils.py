import json
import re
import docx
import pypdf
import google.generativeai as genai
import streamlit as st
from typing import List, Dict, Any

# --- API Configuration Helper ---
def configure_gemini(api_key: str | None):
    if not api_key:
        return
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")

def _extract_top_keywords(text: str, max_items: int = 8) -> List[str]:
    ignore_words = {
        "the", "and", "for", "with", "that", "this", "have", "from", "your", "you",
        "our", "are", "will", "must", "years", "experience", "role", "job", "work",
        "team", "ability", "using", "skills", "required", "preferred", "strong"
    }
    words = re.findall(r"[A-Za-z][A-Za-z\+\#\.\-]{2,}", text.lower())
    freq: Dict[str, int] = {}
    for word in words:
        if word in ignore_words:
            continue
        freq[word] = freq.get(word, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda item: item[1], reverse=True)[:max_items]]

# --- File Parsers ---
def read_docx(file: Any) -> str:
    try:
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except Exception as e:
        st.error(f"Error reading DOCX ({file.name}): {e}")
        return ""

def read_pdf(file: Any) -> str:
    try:
        pdf_reader = pypdf.PdfReader(file)
        text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF ({file.name}): {e}")
        return ""

# --- Helper for JSON parsing from LLM ---
def safe_json_loads(text: str, fallback: Any) -> Any:
    """Attempt to parse JSON, cleaning common LLM markdown noise."""
    try:
        # Remove markdown code blocks if present
        clean_text = re.sub(r'```json\s*|\s*```', '', text).strip()
        return json.loads(clean_text)
    except Exception as e:
        st.warning(f"Failed to parse AI response as JSON. Using fallback. Error: {e}")
        # Try finding anything that looks like a JSON object
        try:
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        return fallback

# --- Advanced AI Extraction ---
def analyze_job_description(jd_text: str, api_key: str | None) -> Dict[str, Any]:
    """Uses LLM to deeply understand the Job Description requirements."""
    fallback = {
        "job_title": "Unknown Position",
        "core_skills": _extract_top_keywords(jd_text),
        "years_experience_required": "N/A",
        "key_responsibilities": []
    }

    if not api_key:
        return fallback

    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Analyze this Job Description and extract the key requirements in JSON format.
    Required Schema:
    {{
        "job_title": "string",
        "core_skills": ["string"],
        "years_experience_required": "string or number",
        "key_responsibilities": ["string"]
    }}
    
    Job Description:
    {jd_text[:4000]}
    """
    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            return fallback
        return safe_json_loads(response.text, fallback)
    except Exception as e:
        st.error(f"AI Job Analysis failed: {e}")
        return fallback

def calculate_advanced_match(jd_data: Dict[str, Any], resume_text: str, api_key: str | None) -> Dict[str, Any]:
    """Semantic matching engine returning score and reasoning."""
    if not api_key:
        core_skills = [s.lower() for s in jd_data.get("core_skills", []) if isinstance(s, str)]
        resume_lower = resume_text.lower()
        matched_skills = [s for s in core_skills if s in resume_lower]
        match_score = int((len(matched_skills) / max(len(core_skills), 1)) * 100) if core_skills else 50
        explanation = (
            f"Demo mode heuristic: matched {len(matched_skills)} of {len(core_skills)} identified skills."
            if core_skills else
            "Demo mode heuristic: no JD skills were extracted; assigned a neutral score."
        )
        return {
            "match_score": max(0, min(match_score, 100)),
            "explanation": explanation,
            "extracted_candidate_skills": _extract_top_keywords(resume_text)
        }

    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert technical recruiter. Evaluate the candidate's resume against the job requirements.
    Output a JSON object with a strict match score (0-100) and specific reasoning.
    
    Job Requirements:
    {json.dumps(jd_data)}
    
    Resume:
    {resume_text[:5000]}
    
    Required Schema:
    {{
        "match_score": integer (0-100),
        "explanation": "2-3 sentences explaining exactly why they fit or what is missing",
        "extracted_candidate_skills": ["string"]
    }}
    """
    fallback = {"match_score": 0, "explanation": "Could not complete analysis.", "extracted_candidate_skills": []}
    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            return fallback
        return safe_json_loads(response.text, fallback)
    except Exception as e:
        st.error(f"AI Match Calculation failed: {e}")
        return fallback

# --- Dynamic Conversational Engagement ---
def generate_initial_greeting(jd_data: Dict[str, Any], candidate_name: str, api_key: str | None) -> str:
    """Starts the conversation dynamically based on JD context."""
    if not api_key:
        top_skill = (jd_data.get("core_skills") or ["the role requirements"])[0]
        return (
            f"Hi {candidate_name}, thanks for your application. "
            f"Are you currently open to opportunities where {top_skill} is a core requirement?"
        )

    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Act as an AI recruiter. Write a friendly, 1-2 sentence opening message to {candidate_name} 
    about the {jd_data.get('job_title', 'open')} role. Ask a qualifying question about one of these core skills: {jd_data.get('core_skills', [])[:3]}.
    """
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return f"Hi {candidate_name}, I'm the AI recruiter for the {jd_data.get('job_title', 'open')} role. Are you interested in discussing your experience?"
    except Exception as e:
        return f"Hi {candidate_name}, I'm the AI recruiter. Are you still interested in the {jd_data.get('job_title', 'open')} role?"

def get_agent_reply(chat_history: List[Dict[str, str]], jd_data: Dict[str, Any], api_key: str | None) -> str:
    """Generates the next reply from the AI Recruiter."""
    if not api_key:
        user_turns = [msg for msg in chat_history if msg.get("role") == "user"]
        scripted_questions = [
            "Thanks! What compensation range are you targeting for your next move?",
            "Got it. Do you prefer remote, hybrid, or onsite work?",
            "Great. How soon could you start if selected?",
            "Thank you, I have all the information I need."
        ]
        return scripted_questions[min(len(user_turns), len(scripted_questions) - 1)]

    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    
    prompt = f"""
    You are an AI Recruiter chatting with a candidate for the {jd_data.get('job_title', 'open')} position.
    Core requirements: {jd_data.get('core_skills', [])}.
    
    Your goal is to assess their technical fit, salary expectations, and work model preference (remote/hybrid).
    Ask ONE concise question at a time. Be natural and professional. If you have enough info, say "Thank you, I have all the information I need."
    
    Chat History:
    {history_text}
    
    AI Recruiter's Next Reply:
    """
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        return "Thank you for sharing that. Could you tell me more about your experience with the core skills mentioned?"
    except Exception:
        return "Interesting. Tell me more."

def evaluate_final_interest(chat_history: List[Dict[str, str]], api_key: str | None) -> int:
    """Calculates final interest and alignment score (0-100) from the conversation."""
    if not api_key:
        candidate_text = " ".join(
            msg.get("content", "").lower() for msg in chat_history if msg.get("role") == "user"
        )
        positive_signals = ["interested", "excited", "yes", "open", "available", "flexible"]
        signal_hits = sum(1 for signal in positive_signals if signal in candidate_text)
        response_count = sum(1 for msg in chat_history if msg.get("role") == "user")
        heuristic_score = 45 + (signal_hits * 8) + min(response_count, 5) * 5
        return max(0, min(heuristic_score, 100))

    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    prompt = f"""
    Analyze this recruiter-candidate chat. 
    Score the candidate's 'Interest & Alignment' from 0 to 100 based on their enthusiasm, salary alignment, and responsiveness.
    Return ONLY the integer number.
    
    Chat History:
    {history_text}
    """
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            score_match = re.search(r'\d+', response.text)
            return int(score_match.group()) if score_match else 50
        return 50
    except Exception:
        return 50
