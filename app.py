import streamlit as st
import pandas as pd
import os
import sys
from src.utils import (
    read_docx,
    read_pdf,
    read_excel_csv,
    analyze_job_description,
    calculate_advanced_match,
    generate_initial_greeting,
    get_agent_reply,
    evaluate_final_interest
)

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(layout="wide", page_title="Catalyst AI Talent Agent")

# --- API Key Handling ---
gemini_api_key = os.environ.get("GOOGLE_API_KEY") 
if not gemini_api_key:
    try:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_api_key = None

if not gemini_api_key:
    st.error("?? API Key Missing! Please set it in .streamlit/secrets.toml")
    st.stop()

# --- Session State ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'ranked_candidates' not in st.session_state:
    st.session_state.ranked_candidates = []
if 'engagement_logs' not in st.session_state:
    st.session_state.engagement_logs = {} 

st.title("?? Catalyst AI: Advanced Talent Agent")
st.markdown("Multi-format Support: PDF, DOCX, CSV, Excel")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Input Data")
    jd_file = st.file_uploader("Upload Job Description", type=["docx", "pdf", "csv", "xlsx"])
    resume_files = st.file_uploader("Upload Resumes", type=["docx", "pdf", "csv", "xlsx"], accept_multiple_files=True)
    
    if st.button("Run AI Scout", type="primary"):
        if jd_file and resume_files:
            with st.spinner("?? AI Processing..."):
                # Parse JD
                if jd_file.name.endswith(('.csv', '.xlsx', '.xls')):
                    jd_text = read_excel_csv(jd_file)
                elif jd_file.name.endswith('.docx'):
                    jd_text = read_docx(jd_file)
                else:
                    jd_text = read_pdf(jd_file)
                
                jd_data = analyze_job_description(jd_text, gemini_api_key)
                st.session_state.jd_data = jd_data

                # Parse & Match Resumes
                candidate_data = []
                for res_file in resume_files:
                    if res_file.name.endswith(('.csv', '.xlsx', '.xls')):
                        res_text = read_excel_csv(res_file)
                    elif res_file.name.endswith('.docx'):
                        res_text = read_docx(res_file)
                    else:
                        res_text = read_pdf(res_file)
                    
                    if res_text:
                        match = calculate_advanced_match(jd_data, res_text, gemini_api_key)
                        candidate_data.append({
                            "name": res_file.name,
                            "skills": match.get("extracted_candidate_skills", []),
                            "match_percentage": match.get("match_score", 0),
                            "explanation": match.get("explanation", "N/A"),
                            "interest_score": 0,
                            "status": "Scouted"
                        })

                candidate_data.sort(key=lambda x: x['match_percentage'], reverse=True)
                st.session_state.ranked_candidates = candidate_data
                st.session_state.analysis_done = True
        else:
            st.warning("Please upload files.")

# --- Dashboard ---
if st.session_state.analysis_done:
    t1, t2, t3 = st.tabs(["?? Match Analysis", "?? AI Interview", "?? Final List"])

    with t1:
        st.header(f"Role: {st.session_state.jd_data.get('job_title')}")
        df = pd.DataFrame(st.session_state.ranked_candidates)
        st.dataframe(df[['name', 'match_percentage', 'explanation', 'status']], use_container_width=True)

    with t2:
        st.header("AI Interview")
        cand_name = st.selectbox("Interview Candidate", [c['name'] for c in st.session_state.ranked_candidates])
        sel_cand = next(c for c in st.session_state.ranked_candidates if c['name'] == cand_name)
        
        if cand_name not in st.session_state.engagement_logs:
            if st.button(f"Start Chat with {cand_name}"):
                greet = generate_initial_greeting(st.session_state.jd_data, cand_name, gemini_api_key)
                st.session_state.engagement_logs[cand_name] = [{"role": "assistant", "content": greet}]
                st.rerun()
        
        if cand_name in st.session_state.engagement_logs:
            for m in st.session_state.engagement_logs[cand_name]:
                with st.chat_message(m["role"]): st.write(m["content"])
            
            if reply := st.chat_input("Reply..."):
                st.session_state.engagement_logs[cand_name].append({"role": "user", "content": reply})
                with st.spinner("AI typing..."):
                    agent_res = get_agent_reply(st.session_state.engagement_logs[cand_name], st.session_state.jd_data, gemini_api_key)
                    st.session_state.engagement_logs[cand_name].append({"role": "assistant", "content": agent_res})
                st.rerun()
            
            if st.button("Finish & Score"):
                score = evaluate_final_interest(st.session_state.engagement_logs[cand_name], gemini_api_key)
                sel_cand['interest_score'] = score
                sel_cand['status'] = "Interviewed"
                st.success(f"Interest Score: {score}/100")
                st.rerun()

    with t3:
        st.header("Final Shortlist")
        for c in st.session_state.ranked_candidates:
            c['final_score'] = (c['match_percentage'] * 0.7) + (c['interest_score'] * 0.3)
        
        fdf = pd.DataFrame(st.session_state.ranked_candidates).sort_values(by="final_score", ascending=False)
        st.dataframe(fdf[['name', 'match_percentage', 'interest_score', 'final_score', 'status']], use_container_width=True)
