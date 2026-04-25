# 🤖 Catalyst AI: AI-Powered Talent Scouting & Engagement Agent

Catalyst AI is a Streamlit-based recruiting assistant that ingests a Job Description (JD), semantically matches candidate resumes, simulates recruiter outreach, and outputs a ranked shortlist using two dimensions:

- **Match Score** (technical/profile fit)
- **Interest Score** (candidate engagement/alignment from conversation)

---

## ✅ Challenge Requirement Coverage

| Requirement | Status | Where it is implemented |
|---|---|---|
| JD parsing | ✅ | `analyze_job_description()` in `src/utils.py` |
| Candidate discovery + matching | ✅ (from uploaded resumes) | `calculate_advanced_match()` + ranking in `app.py` |
| Explainability | ✅ | `explanation` field per candidate in match table |
| Conversational outreach (simulated) | ✅ | Chat workflow in `app.py` (`generate_initial_greeting`, `get_agent_reply`) |
| Interest scoring | ✅ | `evaluate_final_interest()` |
| Combined ranked output | ✅ | Final shortlist tab in `app.py` (70% match + 30% interest) |

> Note: Current candidate discovery is **upload-based** (recruiter uploads resumes). If needed, this can be extended to pull from ATS/LinkedIn/internal DB connectors.

---

## 🏗️ Architecture & Scoring Logic

```mermaid
flowchart TD
    A[Upload JD (PDF/DOCX)] --> B[Text Extraction]
    B --> C[LLM JD Analysis\n(job title, skills, responsibilities)]

    D[Upload Candidate Resumes] --> E[Resume Text Extraction]
    E --> F[LLM Semantic Match\nscore + explanation + skills]
    C --> F

    F --> G[Candidate Match Ranking]
    G --> H[Interactive AI Outreach Chat]
    H --> I[LLM Interest & Alignment Score]

    G --> J[Final Score Engine]
    I --> J
    J --> K[Ranked Shortlist Table]
```

### Scoring formula

- **Match Score**: `0–100` from semantic resume-vs-JD evaluation.
- **Interest Score**: `0–100` from candidate conversation analysis.
- **Final Score**: `0.7 * Match Score + 0.3 * Interest Score`

The weighting is currently fixed and can be made configurable from the UI.

---

## 🚀 Working Prototype (Local Setup)

### 1) Clone repository
```bash
git clone <your-public-repo-url>
cd catalyst-talent-agent
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure API key
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_google_api_key_here"
```

Or set env var:
```bash
export GOOGLE_API_KEY="your_google_api_key_here"
```

### 4) Run app
```bash
streamlit run app.py
```

---

## 🎬 Demo Video (3–5 min)

Record a short walkthrough showing:
1. Upload JD
2. Upload 3–5 resumes
3. Run AI scout and inspect explainable match output
4. Simulate a short candidate chat
5. End interview and view ranked shortlist

Add your final link here:
- **Demo Video URL**: `PASTE_VIDEO_LINK_HERE`

---

## 🧪 Sample Input & Output

### Sample input (JD)
A backend engineer role requiring Python, FastAPI, PostgreSQL, and cloud deployment experience.

### Sample output (shortlist row)
```json
{
  "name": "candidate_a.pdf",
  "match_percentage": 86,
  "interest_score": 78,
  "final_score": 83.6,
  "status": "Interviewed",
  "explanation": "Strong overlap in Python/FastAPI/PostgreSQL with proven production experience. Minor gap in cloud cost-optimization ownership."
}
```

---

## 📦 Submission Checklist (for challenge handoff)

Before submitting, ensure these are ready:

- [ ] **Git repository URL**: `PASTE_REPO_URL_HERE`
- [ ] **Git username**: `PASTE_GITHUB_USERNAME_HERE`
- [ ] **Project documentation / README**: this file
- [ ] **Demo video link (3–5 min)**: `PASTE_VIDEO_LINK_HERE`
- [ ] **Project site URL** (if deployed): `PASTE_DEPLOYED_URL_HERE`

### Deadline note
Challenge deadline stated: **Monday, April 27, 1:00 AM IST**.

---

## 🔍 Troubleshooting

### API key missing
- Error: `API Key Missing!`
- Fix: Add `GEMINI_API_KEY` in `.streamlit/secrets.toml` or export `GOOGLE_API_KEY`.

### Parsing failures
- Ensure PDFs/DOCX files are valid and not password-protected.

### AI analysis failures
- Check internet + API quota/model access (`gemini-1.5-flash`).

---

## 📁 Project Structure

- `app.py` — Streamlit UI and candidate workflow.
- `src/utils.py` — file parsing, Gemini integration, matching, and scoring helpers.
- `requirements.txt` — Python dependencies.
