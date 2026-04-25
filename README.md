# Catalyst AI: Talent Scouting & Engagement Agent

## Overview
Catalyst AI is an intelligent recruitment agent designed to automate the most time-consuming parts of the hiring funnel: **discovery, screening, and engagement.**

Unlike traditional ATS systems that only parse keywords, Catalyst AI acts as an autonomous agent that not only finds candidates but actively engages them to assess genuine interest and cultural alignment.

## Core Features
1. **AI-Powered Scouting:** Uses LLM-based analysis to go beyond simple keyword matching. It provides **Explainable AI** summaries for every candidate, telling the recruiter *why* a candidate is a fit.
2. **Autonomous Engagement (Simulated):** Generates candidate-specific screening questions based on the Job Description and simulates a conversational outreach to assess interest.
3. **Dual-Dimension Scoring:** Ranks candidates on a weighted score:
   - **Match Score (70%):** Technical proficiency and experience overlap.
   - **Interest Score (30%):** Enthusiasm, availability, and alignment discovered during the engagement phase.

## Technical Architecture
- **Frontend:** Streamlit for a fast, responsive recruiter dashboard.
- **LLM Engine:** Google Gemini (1.5 Flash) for high-speed, cost-effective reasoning and NLP.
- **NLP Pipeline:** spaCy for structured entity extraction and initial skill filtering.
- **State Management:** Streamlit session state handles multi-step candidate engagement tracking.

## Measurable Business Impact (ROI)
- **Workflow Throughput:** Reduces initial screening time by an estimated **60%** by automating the first touchpoint.
- **Accuracy Lift:** "Explainable Matching" reduces the false-positive rate of keyword-based filters.
- **Cost Reduction:** Eliminates the need for expensive third-party screening tools by integrating intelligence directly into the discovery phase.

## Installation & Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Google AI API Key:
   ```bash
   export GOOGLE_API_KEY='your_api_key_here'
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Demo Use Case
1. Upload a **Senior Data Scientist** JD.
2. Upload 5 sample resumes.
3. Run the "Scouting Agent" to see the explained matches.
4. Select a top candidate and click "Begin Outreach."
5. Chat with the candidate (simulated) and click "Finalize Engagement" to see the final ROI-ranked shortlist.
