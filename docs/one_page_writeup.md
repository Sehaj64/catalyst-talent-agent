# One-Page Write-Up

## Approach

TalentSignal Agent treats recruiting as a multi-step agent workflow, not a single prompt. The recruiter inputs a job description and can also paste resumes or candidate profiles. The system parses the role, converts resumes into structured candidate profiles, builds a sourcing strategy, discovers candidates from the provided resumes and/or a simulated market, computes explainable `Match Score`, simulates conversational outreach to estimate genuine interest, and returns a ranked shortlist with confidence, evidence paths, risks, interview questions, and next actions.

## Architecture

The app is a Python FastAPI service with a browser-based recruiter console. The core agent modules are separated into JD parser, resume parser, discovery, scorer, outreach simulator, decision intelligence, and orchestrator. Each module returns structured Pydantic objects, so the UI and JSON export use the same auditable output.

## Scoring

`Match Score` measures role fit:

- Skills: exact and adjacent skill coverage
- Seniority: years and role level fit
- Domain: HRTech, SaaS, enterprise, recruiting, or other domain overlap
- Evidence: public projects, achievements, and artifacts
- Logistics: remote/location, notice period, compensation hint
- Differentiation: agent, evaluation, privacy, ranking, and recruiting-specific signals

`Interest Score` estimates candidate willingness from simulated outreach. It considers motivation, responsiveness, remote/location fit, perceived role fit, reservations, and availability.

The final ranking uses:

`Combined Score = Match Score * 0.65 + Interest Score * 0.35`

`Confidence Score` is shown separately. It measures how much evidence supports the ranking and penalizes missing skills, weak source depth, and disagreement between match and interest.

## Trade-Offs

The main trade-off is deterministic reliability versus live internet sourcing. For a hackathon submission, pasted resumes and a local simulated candidate market avoid API costs, scraping risk, rate limits, and demo instability. The discovery layer is still designed as a connector interface, so real sources can be added later without rewriting the scoring or UI.

The outreach is simulated rather than sent to real candidates. This keeps the demo ethical and repeatable while still showing how the agent would assess interest.

## What Makes It Strong

- Works end to end from JD to ranked shortlist.
- Produces recruiter-ready explanations, not just opaque scores.
- Separates match quality from candidate interest.
- Shows the conversation transcript and reservations behind the interest score.
- Adds evidence paths, risk mitigations, and interview questions for each candidate.
- Includes a compliance audit that avoids protected attributes and keeps the human recruiter accountable.
- Includes counterfactuals that tell the recruiter what would change the ranking.
- Runs locally with no paid API keys.

## Demo Video Script

1. Open the app and show the sample JD.
2. Show the sample resumes and explain that recruiters can paste their own profiles.
3. Click `Run Agent`.
4. Walk through parsed role signals: skills, seniority, location, domain.
5. Show the discovery strategy and audit trace.
6. Review the top candidate's match score, interest score, confidence, transcript, evidence paths, risks, and next steps.
7. Export JSON and explain how it can be handed to a recruiter or ATS.
