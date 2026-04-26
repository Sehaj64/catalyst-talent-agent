# Deployment Guide

## Streamlit Community Cloud

1. Push the repo to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from the repo.
4. Set the main file path to:

```text
app.py
```

5. Deploy.

No API key is required for the default demo because the core scoring engine is deterministic and offline.

The app accepts pasted text, TXT/MD, PDF, DOCX, CSV, and XLSX uploads for both the JD and resume. CSV/XLSX files are flattened with row and column labels so ATS exports and candidate trackers remain auditable.

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
