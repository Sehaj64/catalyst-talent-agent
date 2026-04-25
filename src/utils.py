import json
import re
import docx
import pypdf
import google.generativeai as genai
import streamlit as st
from typing import List, Dict, Any

# --- API Configuration Helper ---
def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)

# --- File Parsers ---
def read_docx(file: Any) -> str:
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

def read_pdf(file: Any) -> str:
    try:
        pdf_reader = pypdf.PdfReader(file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    except Exception:
        return ""

# --- Advanced AI Extraction (Replaces legacy spaCy) ---
def analyze_job_description(jd_text: str, api_key: str) -> Dict[str, Any]:
    """Uses LLM to deeply understand the Job Description requirements."""
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
    {jd_text[:3000]}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"job_title": "Unknown", "core_skills": [], "years_experience_required": "N/A", "key_responsibilities": []}

def calculate_advanced_match(jd_data: Dict[str, Any], resume_text: str, api_key: str) -> Dict[str, Any]:
    """Semantic matching engine returning score and reasoning."""
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert technical recruiter. Evaluate the candidate's resume against the job requirements.
    Output a JSON object with a strict match score (0-100) and specific reasoning.
    
    Job Requirements:
    {json.dumps(jd_data)}
    
    Resume:
    {resume_text[:4000]}
    
    Required Schema:
    {{
        "match_score": integer (0-100),
        "explanation": "2-3 sentences explaining exactly why they fit or what is missing",
        "extracted_candidate_skills": ["string"]
    }}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception:
        return {"match_score": 0, "explanation": "Analysis failed.", "extracted_candidate_skills": []}

# --- Dynamic Conversational Engagement ---
def generate_initial_greeting(jd_data: Dict[str, Any], candidate_name: str, api_key: str) -> str:
    """Starts the conversation dynamically based on JD context."""
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Act as an AI recruiter. Write a friendly, 1-2 sentence opening message to {candidate_name} 
    about the {jd_data.get('job_title', 'open')} role. Ask a qualifying question about one of these core skills: {jd_data.get('core_skills', [])[:3]}.
    """
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return f"Hi {candidate_name}, I'm the AI recruiter for the open role. Are you still interested?"

def get_agent_reply(chat_history: List[Dict[str, str]], jd_data: Dict[str, Any], api_key: str) -> str:
    """Generates the next reply from the AI Recruiter."""
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
        return model.generate_content(prompt).text.strip()
    except:
        return "Thank you for sharing."

def evaluate_final_interest(chat_history: List[Dict[str, str]], api_key: str) -> int:
    """Calculates final interest and alignment score (0-100) from the conversation."""
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
        score_match = re.search(r'\d+', response.text)
        return int(score_match.group()) if score_match else 50
    except:
        return 50
