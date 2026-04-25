import json
import re
import docx
import pypdf
import pandas as pd
import google.generativeai as genai
import streamlit as st
from typing import List, Dict, Any, Union

# --- API Configuration ---
def configure_gemini(api_key: str):
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")

# --- File Parsers (PDF, DOCX, CSV, EXCEL) ---
def read_docx(file: Any) -> str:
    try:
        doc = docx.Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except Exception: return ""

def read_pdf(file: Any) -> str:
    try:
        pdf_reader = pypdf.PdfReader(file)
        text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        return text.strip()
    except Exception: return ""

def read_excel_csv(file: Any) -> str:
    """Parses CSV and Excel files into a text format for the AI."""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return df.to_string(index=False)
    except Exception: return ""

# --- Helper for Robust JSON Extraction ---
def safe_json_loads(text: str, fallback: Any) -> Any:
    try:
        # Clean markdown code blocks
        clean_text = re.sub(r'```json\s*|\s*```', '', text).strip()
        # Find the first { and last }
        start = clean_text.find('{')
        end = clean_text.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(clean_text[start:end])
        return json.loads(clean_text)
    except Exception:
        return fallback

# --- Advanced AI Extraction ---
def analyze_job_description(jd_text: str, api_key: str) -> Dict[str, Any]:
    configure_gemini(api_key)
    # Using a stable model config to avoid Schema errors
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    Analyze this Job Description and extract key requirements.
    Return ONLY a JSON object:
    {{
        "job_title": "string",
        "core_skills": ["string"],
        "years_experience_required": "string",
        "key_responsibilities": ["string"]
    }}
    
    Job Description: {jd_text[:4000]}
    """
    fallback = {"job_title": "Unknown", "core_skills": [], "years_experience_required": "N/A", "key_responsibilities": []}
    try:
        response = model.generate_content(prompt)
        return safe_json_loads(response.text, fallback)
    except Exception: return fallback

def calculate_advanced_match(jd_data: Dict[str, Any], resume_text: str, api_key: str) -> Dict[str, Any]:
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    Evaluate the resume against these requirements.
    Return ONLY a JSON object:
    {{
        "match_score": integer (0-100),
        "explanation": "2-3 sentences explaining fit",
        "extracted_candidate_skills": ["string"]
    }}
    
    Requirements: {json.dumps(jd_data)}
    Resume: {resume_text[:5000]}
    """
    fallback = {"match_score": 0, "explanation": "Failed to analyze.", "extracted_candidate_skills": []}
    try:
        response = model.generate_content(prompt)
        return safe_json_loads(response.text, fallback)
    except Exception: return fallback

# --- Conversational Engagement ---
def generate_initial_greeting(jd_data: Dict[str, Any], candidate_name: str, api_key: str) -> str:
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = f"Write a 1-2 sentence recruiter opening for {candidate_name} for the {jd_data.get('job_title')} role. Mention one skill from {jd_data.get('core_skills', [])[:2]}."
    try:
        return model.generate_content(prompt).text.strip()
    except Exception: return f"Hi {candidate_name}, interested in the {jd_data.get('job_title')} role?"

def get_agent_reply(chat_history: List[Dict[str, str]], jd_data: Dict[str, Any], api_key: str) -> str:
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    history = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    prompt = f"You are a recruiter interviewing for {jd_data.get('job_title')}. Ask ONE follow-up question based on this history: {history}"
    try:
        return model.generate_content(prompt).text.strip()
    except Exception: return "Tell me more about your experience."

def evaluate_final_interest(chat_history: List[Dict[str, str]], api_key: str) -> int:
    configure_gemini(api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    history = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    prompt = f"Rate candidate interest (0-100) from this chat: {history}. Return ONLY the number."
    try:
        res = model.generate_content(prompt).text
        return int(re.search(r'\d+', res).group())
    except Exception: return 50
