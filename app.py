import streamlit as st
import pandas as pd
import os
import sys

# Ensure the root directory is in sys.path for robust imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

demo_mode = not bool(gemini_api_key)
if demo_mode:
    st.warning("⚠️ Running in Demo Mode (no Gemini API key detected). AI calls use local heuristic fallbacks.")
    st.info("To enable live Gemini responses, set GOOGLE_API_KEY or .streamlit/secrets.toml with GEMINI_API_KEY.")

# --- Session State Initialization ---
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'ranked_candidates' not in st.session_state:
    st.session_state.ranked_candidates = []
if 'engagement_logs' not in st.session_state:
    st.session_state.engagement_logs = {} 
if 'jd_data' not in st.session_state:
    st.session_state.jd_data = {}

st.title("🤖 Catalyst AI: Advanced Talent Agent")
st.markdown("Semantic Job Matching & Autonomous Candidate Engagement using Gemini 1.5")

# --- Sidebar ---
with st.sidebar:
    st.header("1. Input Data")
    st.caption(f"Mode: {'Demo (heuristics)' if demo_mode else 'Live Gemini'}")
    job_description_file = st.file_uploader("Upload Job Description", type=["docx", "pdf"])
    resume_files = st.file_uploader("Upload Resumes", type=["docx", "pdf"], accept_multiple_files=True)
    
    if st.button("Run Advanced AI Scout", type="primary"):
        if job_description_file and resume_files:
            try:
                with st.spinner("🧠 AI is comprehending the Job Description..."):
                    if job_description_file.type == "application/pdf":
                        jd_text = read_pdf(job_description_file)
                    else:
                        jd_text = read_docx(job_description_file)
                    
                    if not jd_text:
                        st.error("Could not extract text from Job Description. Please check the file.")
                        st.stop()
                        
                    jd_data = analyze_job_description(jd_text, gemini_api_key)
                    st.session_state.jd_data = jd_data

                with st.spinner("🔍 Performing Semantic Resume Matching..."):
                    candidate_data = []
                    for resume_file in resume_files:
                        if resume_file.type == "application/pdf":
                            res_text = read_pdf(resume_file)
                        else:
                            res_text = read_docx(resume_file)
                            
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
                        else:
                            st.warning(f"Could not read resume: {resume_file.name}")

                    if not candidate_data:
                        st.error("No resumes could be processed.")
                    else:
                        # Sort by semantic match
                        candidate_data.sort(key=lambda x: x['match_percentage'], reverse=True)
                        st.session_state.ranked_candidates = candidate_data
                        st.session_state.analysis_done = True
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
        else:
            st.error("Please provide both a Job Description and at least one resume.")

# --- Main Dashboard ---
if st.session_state.analysis_done:
    tab1, tab2, tab3 = st.tabs(["📊 Semantic Match", "💬 Agent Chat", "🏆 Final Shortlist"])

    with tab1:
        st.header(f"Target Role: {st.session_state.jd_data.get('job_title', 'Unknown')}")
        st.write(f"**Required Skills Identified:** {', '.join(st.session_state.jd_data.get('core_skills', []))}")
        
        if st.session_state.ranked_candidates:
            df = pd.DataFrame(st.session_state.ranked_candidates)
            st.dataframe(df[['name', 'match_percentage', 'explanation', 'status']], use_container_width=True)
        else:
            st.info("No candidates to display.")

    with tab2:
        st.header("Autonomous Candidate Engagement")
        st.markdown("The AI Agent dynamically interviews candidates based on the parsed JD context.")
        
        if st.session_state.ranked_candidates:
            cand_names = [c['name'] for c in st.session_state.ranked_candidates]
            selected_cand_name = st.selectbox("Select Candidate to Interview", cand_names)
            selected_cand = next((c for c in st.session_state.ranked_candidates if c['name'] == selected_cand_name), None)
            
            if selected_cand:
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
        else:
            st.info("Run the AI Scout first to see candidates.")

    with tab3:
        st.header("ROI-Ranked Shortlist")
        st.markdown("Ranked by combining Semantic Match (70%) and Conversational Interest (30%).")
        
        if st.session_state.ranked_candidates:
            for cand in st.session_state.ranked_candidates:
                cand['final_score'] = (cand.get('match_percentage', 0) * 0.7) + (cand.get('interest_score', 0) * 0.3)
            
            final_df = pd.DataFrame(st.session_state.ranked_candidates)
            final_df = final_df.sort_values(by="final_score", ascending=False)
            
            st.dataframe(final_df[['name', 'match_percentage', 'interest_score', 'final_score', 'status']], use_container_width=True)
        else:
            st.info("No candidates to display.")
