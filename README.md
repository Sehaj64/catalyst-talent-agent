# 🛡️ SkillProof AI: Claim-to-Proof Agent

> A resume tells you what someone claims to know — not how well they actually know it.

**SkillProof AI** is a production-minded talent assessment engine built for the Deccan AI Catalyst 2026 Hackathon. It conversationally assesses real proficiency, identifies gaps, and generates a personalized learning plan focused on adjacent skills.

## 🚀 The "Why" and The Business ROI
We built this agent to solve measurable business problems:
1. **Cost Reduction**: Replaces expensive manual resume screening and 1st-round technical screening.
2. **Accuracy Lift**: Moves away from "vibe-checks" and keyword matching to actual **conversational proof** using Senior Architect level scenarios.
3. **Workflow Throughput**: Automatically generates a Claim-to-Proof Ledger and a concrete Learning Roadmap, enabling hiring managers to make fast, evidence-backed decisions.

## 🏗️ Architecture & Scoring Logic

The system is built on an **Agentic AI** framework utilizing `gemini-2.5-pro` (the smartest model in the 2026 sandbox) acting as a Principal Systems Architect.

```mermaid
graph TD;
    A[Upload JD & Resume] --> B[Skill Extraction Engine]
    B --> C{Priority Filter}
    C -->|Top 5 Skills| D[Dynamic Interviewer Agent]
    D -->|Initial Scenario| E[Candidate Answer]
    E --> F[Proof-Hunter Agent]
    F -->|Vague Answer| G[Probe for Metrics/Details]
    F -->|Strong Answer| H[Probe for Edge-Cases/Scale]
    G --> I[Scoring Engine]
    H --> I
    I --> J[Claim-to-Proof Ledger]
    I --> K[Career Architect Agent]
    K --> L[Personalized Learning Plan]
```

### 🧠 The Scoring Logic
Instead of a simple 1-10 rating, SkillProof uses a rigorous **100-point rubric**:
- **Resume Evidence (Max 25):** Are their claims backed by the conversation?
- **Answer Quality (Max 45):** Technical accuracy, specific tool mentions, and metrics.
- **Practical Depth (Max 20):** Evidence of hands-on experience, tradeoffs, and troubleshooting.
- **Confidence (Max 10):** Communication certainty and lack of "weak phrases".

## ✨ Key Features
- **God-Tier Prompts**: The AI is strictly instructed to NEVER repeat a topic and to push candidates on high-stakes failures (Memory Leaks, P99 Latency).
- **Claim-to-Proof Ledger**: A transparent audit trail showing exactly which resume claims were proven and which were unproven.
- **Zero-to-Expert Roadmaps**: The AI generates a customized learning plan with mandatory **Proof Artifacts** (mini-projects) instead of generic advice.

## 💻 Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hackathon-deccan-ai/your-repo-name.git
   cd catalyst_agent
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API Key:**
   (Required for Gemini-generated interview questions and the AI-personalized learning roadmap. Core extraction, scoring, and the local roadmap still run without it.)
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
   On Streamlit Cloud, add the same key as `GEMINI_API_KEY` or `GOOGLE_API_KEY` in App settings -> Secrets. The Learning Plan tab uses this same Gemini 2.5 Pro key and no longer has a separate API-key field.

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
