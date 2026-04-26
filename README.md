# 🛡️ SkillProof AI: Claim-to-Proof Agent

> A resume tells you what someone claims to know — not how well they actually know it.

**SkillProof AI** is a production-minded talent assessment engine built for the Deccan AI Catalyst 2026 Hackathon. It conversationally assesses real proficiency, identifies gaps, and generates a personalized learning plan focused on adjacent skills.

## 🚀 The "Why" and The Business ROI
We built this agent to solve measurable business problems:
1. **Cost Reduction**: Replaces expensive manual resume screening and 1st-round technical screening.
2. **Accuracy Lift**: Moves away from "vibe-checks" and keyword matching to actual **conversational proof** using Senior Architect level scenarios.
3. **Workflow Throughput**: Automatically generates a Claim-to-Proof Ledger and a concrete Learning Roadmap, enabling hiring managers to make fast, evidence-backed decisions.

## 🏗️ Architecture & Scoring Logic

The system is built on an **Agentic AI** framework utilizing `gemini-3-pro-preview` (the latest experimental model in the 2026 sandbox) acting as a Principal Systems Architect.

```mermaid
graph TD;
    A[Upload JD & Resume] --> B[Skill Extraction Engine]
    B --> C{Seniority Detector}
    C -->|Junior/Mid/Senior| D[Relative Difficulty Logic]
    D --> E[Dynamic Interviewer Agent]
    E -->|Architect Scenario| F[Candidate Answer]
    F --> G[Proof-Hunter Agent]
    G -->|Vague Answer| H[Identify Critical Risk]
    G -->|Strong Answer| I[Verify Mastery]
    H --> J[Scoring Engine]
    I --> J
    J --> K[Claim-to-Proof Ledger]
    J --> L[Career Architect Agent]
    L --> M[Personalized Learning Plan]
```

### 🧠 The Scoring Logic
Instead of a simple 1-10 rating, SkillProof uses a rigorous **100-point rubric**:
- **Resume Evidence (Max 25):** Are their claims backed by the conversation?
- **Answer Quality (Max 45):** Technical accuracy, specific tool mentions, and metrics.
- **Practical Depth (Max 20):** Evidence of hands-on experience, tradeoffs, and troubleshooting.
- **Confidence (Max 10):** Communication certainty and professional clarity.

## ✨ Key Features
- **God-Tier Prompts**: The AI acts as a Principal Architect and is strictly instructed to NEVER repeat a topic.
- **Relative Difficulty**: Automatically detects seniority (Junior/Mid/Senior) from the JD and adapts question complexity accordingly.
- **Claim-to-Proof Ledger**: A transparent audit trail showing exactly which resume claims were proven and which were unproven.
- **Zero-to-Expert Roadmaps**: The AI generates a customized learning plan with mandatory **Proof Artifacts** (mini-projects) instead of generic advice.

## 💻 Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sehaj64/SkillProof-.git
   cd catalyst_agent
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API Key:**
   (Required for Gemini-generated interview questions and the AI-personalized learning roadmap.)
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
   On Streamlit Cloud, add the same key as `GEMINI_API_KEY` or `GOOGLE_API_KEY` in App settings -> Secrets.

4. **Run the App:**
   ```bash
   streamlit run app.py
   ```

## 🎥 Demo Video
[Link to Demo Video] (Add your YouTube/Loom link here)

## 📁 Sample Inputs & Outputs
Included in the `sample-data/` folder:
- `sample-jd.txt`: Senior AI Engineer JD
- `sample-resume.txt`: High-impact candidate resume
- *Outputs are generated dynamically in the UI tabs (Gap Analysis, Learning Plan).*

---
Built with ⚡ for Deccan AI Catalyst 2026.
