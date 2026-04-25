import streamlit as st
import pandas as pd
import os
from src.utils import (
    read_docx,
    read_pdf,
    analyze_job_description,
    calculate_advanced_match,
    generate_initial_greeting,
    get_agent_reply,
    evaluate_final_interest
)

st.set_page_config(layout="wide", page_title="Catalyst AI Talent Agent")

# --- API Key Handling ---
gemini_api_key = os.environ.get("GOOGLE_API_KEY") 
if not gemini_api_key:
    try:
        gemini_api_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_api_key = None

# --- Session State Initialization ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'ranked_candidates' not in st.session_state:
    st.session_state.ranked_candidates = []
if 'engagement_logs' not in st.session_state:
    st.session_state.engagement_logs = {} 

st.title("?? Catalyst AI: Advanced Talent Agent")
st.markdown("Semantic Job Matching & Autonomous Candidate Engagement using Gemini 1.5")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Input Data")
    job_description_file = st.file_uploader("Upload Job Description", type=["docx", "pdf"])
    resume_files = st.file_uploader("Upload Resumes", type=["docx", "pdf"], accept_multiple_files=True)
    
    if st.button("Run Advanced AI Scout", type="primary"):
        if job_description_file and resume_files and gemini_api_key:
            with st.spinner("?? AI is comprehending the Job Description..."):
                jd_text = read_docx(job_description_file) if "wordprocessingml" in job_description_file.type else read_pdf(job_description_file)
                jd_data = analyze_job_description(jd_text, gemini_api_key)
                st.session_state.jd_data = jd_data

            with st.spinner("?? Performing Semantic Resume Matching..."):
                candidate_data = []
                for resume_file in resume_files:
                    res_text = read_docx(resume_file) if "wordprocessingml" in resume_file.type else read_pdf(resume_file)     
                    if res_text:
                        match_results = calculate_advanced_match(jd_data, res_text, gemini_api_key)
                        candidate_data.append({
                            "name": resume_file.name,
                            "skills": match_results.get("extracted_candidate_skills", []),
                            "match_percentage": match_results.get("match_score", 0),
                            "explanation": match_results.get("explanation", "N/A"),
                            "interest_score": 0,
                            "status": "Scouted"
                        })

                # Sort by semantic match
                candidate_data.sort(key=lambda x: x['match_percentage'], reverse=True)
                st.session_state.ranked_candidates = candidate_data
                st.session_state.analysis_done = True
        else:
            st.error("Please provide JD, Resumes, and ensure API Key is set.")

# --- Main Dashboard ---
if st.session_state.analysis_done:
    tab1, tab2, tab3 = st.tabs(["?? Semantic Match", "?? Agent Chat", "?? Final Shortlist"])

    with tab1:
        st.header(f"Target Role: {st.session_state.jd_data.get('job_title', 'Unknown')}")
        st.write(f"**Required Skills Identified:** {', '.join(st.session_state.jd_data.get('core_skills', []))}")
        
        df = pd.DataFrame(st.session_state.ranked_candidates)
        st.dataframe(df[['name', 'match_percentage', 'explanation', 'status']], use_container_width=True)

    with tab2:
        st.header("Autonomous Candidate Engagement")
        st.markdown("The AI Agent dynamically interviews candidates based on the parsed JD context.")
        
        cand_names = [c['name'] for c in st.session_state.ranked_candidates]
        selected_cand_name = st.selectbox("Select Candidate to Interview", cand_names)
        selected_cand = next(c for c in st.session_state.ranked_candidates if c['name'] == selected_cand_name)
        
        if selected_cand_name not in st.session_state.engagement_logs:
            if st.button(f"Initiate Agent Chat with {selected_cand_name}"):
                greeting = generate_initial_greeting(st.session_state.jd_data, selected_cand_name, gemini_api_key)
                st.session_state.engagement_logs[selected_cand_name] = [{"role": "assistant", "content": greeting}]
                st.rerun()
        
        if selected_cand_name in st.session_state.engagement_logs:
            chat_history = st.session_state.engagement_logs[selected_cand_name]
            
            for msg in chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
            
            if user_reply := st.chat_input("Candidate's reply..."):
                chat_history.append({"role": "user", "content": user_reply})
                # Auto-generate agent reply
                with st.spinner("Agent is typing..."):
                    agent_reply = get_agent_reply(chat_history, st.session_state.jd_data, gemini_api_key)
                    chat_history.append({"role": "assistant", "content": agent_reply})
                st.session_state.engagement_logs[selected_cand_name] = chat_history
                st.rerun()
            
            if st.button("End Interview & Score Interest"):
                with st.spinner("Calculating Engagement Metrics..."):
                    score = evaluate_final_interest(chat_history, gemini_api_key)
                    selected_cand['interest_score'] = score
                    selected_cand['status'] = "Interviewed"
                    st.success(f"Final Interest Score: {score}/100")
                    st.rerun()

    with tab3:
        st.header("ROI-Ranked Shortlist")
        st.markdown("Ranked by combining Semantic Match (70%) and Conversational Interest (30%).")
        
        for cand in st.session_state.ranked_candidates:
            cand['final_score'] = (cand['match_percentage'] * 0.7) + (cand['interest_score'] * 0.3)
        
        final_df = pd.DataFrame(st.session_state.ranked_candidates)
        final_df = final_df.sort_values(by="final_score", ascending=False)
        
        st.dataframe(final_df[['name', 'match_percentage', 'interest_score', 'final_score', 'status']], use_container_width=True)
