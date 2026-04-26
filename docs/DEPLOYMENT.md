# Deployment Guide

## Streamlit Community Cloud

Live deployed app: `https://aiagent0.streamlit.app/`

1. Use the GitHub repo: `https://github.com/Sehaj64/catalyst-talent-agent`.
2. Go to Streamlit Community Cloud.
3. Create a new app from the repo.
4. Set the main file path to:

```text
app.py
```

5. Deploy.

No API key is required for the default demo because the core scoring engine is deterministic and offline.

The app accepts pasted text, TXT/MD, PDF, DOCX, CSV, and XLSX uploads for both the JD and resume. CSV/XLSX files are flattened with row and column labels so ATS exports and candidate trackers remain auditable.

Optional Gemini 3 Pro reviewer secrets:

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3-pro-preview"
```

The optional reviewer is only used from the Export tab. The main assessment flow works without these values. The app also supports OpenRouter or a custom OpenAI-compatible endpoint from the same reviewer panel.

The live Skill Conversation can also use the same `GEMINI_API_KEY` to generate more varied role-specific questions. If the secret is not configured, it automatically falls back to deterministic rubric questions.

## Local Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## CLI Smoke Test

```bash
python cli.py --sample
```

Or run with custom files:

```bash
python cli.py --jd-file path/to/jd.docx --resume-file path/to/resume.xlsx
```

## Unit Tests

```bash
python -m unittest discover -s tests
```
