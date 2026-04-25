# TalentSignal Agent

AI-powered talent scouting and engagement agent for the Deccan AI Catalyst challenge.

The app takes a job description plus optional pasted resumes/profiles, parses hiring requirements, discovers matching candidates from user-provided resumes and/or a simulated talent market, runs explainable match scoring, simulates conversational outreach, and returns a ranked shortlist with `Match Score`, `Interest Score`, `Confidence Score`, ROI estimates, decision labels, transcript snippets, evidence paths, risk mitigations, interview questions, and recruiter next steps.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000`.

## What It Covers From The Brief

- JD parsing: role, seniority, years, location, remote policy, must-have skills, nice-to-have skills, domains, responsibilities.
- Resume/profile parsing: recruiters can paste multiple resumes or import a `.txt`/`.md` file.
- Candidate discovery: user-provided resumes plus simulated public profile, GitHub, portfolio, ATS, and CRM sourcing layer.
- Matching: explainable scoring with exact skills, adjacent skills, seniority fit, domain fit, evidence depth, logistics, and differentiators.
- Conversational outreach: simulated personalized opener, candidate response, follow-up, constraints, reservations, and next action.
- Ranked recruiter output: combined ranking based on match and interest, with confidence, evidence paths, risks, counterfactuals, interview questions, and a recruiter brief.
- Business outcomes: estimated recruiter hours saved, screening cost saved, throughput lift, quality proxy, and KPIs to validate after deployment.
- Documentation: architecture diagram, scoring logic, sample inputs and outputs, and one-page write-up.

## Architecture

```mermaid
flowchart LR
    A["Recruiter JD"] --> B["JD Parser"]
    R["Resumes / Profiles"] --> RP["Resume Parser"]
    B --> C["Search Strategy Builder"]
    RP --> D["Candidate Discovery Layer"]
    C --> D
    D --> E["Match Scorer"]
    E --> F["Outreach Simulator"]
    F --> G["Ranker"]
    G --> H["Decision Intelligence"]
    H --> ROI["Business Impact Model"]
    ROI --> I["Recruiter Console"]
    ROI --> J["JSON Export"]

    B --> B1["Skills, seniority, domains, constraints"]
    E --> E1["Explainable score breakdown"]
    F --> F1["Interest signal and transcript"]
```

## Scoring Logic

`Match Score` is weighted out of 100:

- Skill alignment: 55 points
- Seniority fit: 15 points
- Domain fit: 10 points
- Evidence depth: 12 points
- Logistics fit: 8 points
- Differentiation: 10 points, capped into the final 100

`Interest Score` is simulated from candidate drivers, responsiveness, remote/location fit, perceived role fit, availability, and reservations.

`Combined Score = Match Score * 0.65 + Interest Score * 0.35`

`Confidence Score` is not used to inflate ranking. It tells the recruiter how much evidence supports the ranking by looking at source depth, evidence paths, score agreement, responsiveness, and missing skill penalties.

## Business Outcome Model

The prototype is framed around measurable recruiting ROI:

- Cost reduction: estimates recruiter screening hours saved and equivalent effort cost.
- Throughput: compares manual first-pass review against agent-assisted review.
- Quality lift: uses an evidence-weighted fit proxy from `Match Score` and `Confidence Score`.
- Waste reduction: flags risky candidates before recruiter screens.
- KPIs: time-to-shortlist, recruiter minutes per qualified candidate, top-3 hiring manager acceptance rate, reply rate, and false positive screen rate.

## Why This Is Different

Most hackathon submissions stop at "paste JD, get candidates." TalentSignal adds a decision layer a recruiter can defend:

- Evidence paths connect each claim to a source-style artifact.
- Risk signals explain what could make a candidate fail later and how to mitigate it.
- Interview questions are generated from the candidate's actual gaps and strengths.
- Compliance audit states what signals are and are not used.
- The discovery layer is swappable, but the ranking logic remains auditable.

## API

- `GET /` - recruiter console
- `GET /api/sample-jd` - sample job description
- `GET /api/sample-resumes` - sample resume/profile input
- `POST /api/analyze` - run the agent
- `GET /api/health` - service health

Example request:

```json
{
  "job_description": "Role: Senior AI Engineer...",
  "candidate_resumes": "Name: Candidate One...",
  "include_sample_market": true,
  "top_k": 8,
  "simulate_outreach": true
}
```

## APIs And Tools Used

This prototype uses only local/free tooling:

- Python
- FastAPI
- Pydantic
- Jinja2
- Uvicorn
- Vanilla HTML/CSS/JS

No paid LLM API keys are required. Production connectors can be added behind the discovery and outreach interfaces.

## Submission Checklist

- Working prototype: run with `python run.py`
- Source code: this repository
- Architecture: see `docs/architecture.md`
- One-page write-up: see `docs/one_page_writeup.md`
- Sample input: see `samples/sample_jd.txt`
- Sample resumes: see `samples/sample_resumes.txt`
- Sample output: generate with the app's Export JSON button or inspect `samples/sample_output.json`
- Demo video script: included in `docs/one_page_writeup.md`

Before final submission, push this repo publicly and share repository access with `hackathon@deccan.ai`.
