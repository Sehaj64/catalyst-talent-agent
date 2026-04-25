from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .agent import TalentScoutingAgent
from .agent.schemas import AnalyzeRequest


SAMPLE_JD = """Role: Senior AI Engineer - Agentic Talent Scouting

We are building an AI-powered talent scouting and engagement agent for recruiters. The agent should parse job descriptions, discover matching candidates, score them with explainable match logic, simulate conversational outreach, and return a ranked shortlist that a recruiter can act on immediately.

Responsibilities:
- Build production-quality Python services and clean recruiter-facing workflows.
- Design AI agents with tool calling, RAG, candidate matching, ranking, and evaluation loops.
- Create transparent scoring for Match Score and Interest Score.
- Work with candidate data responsibly, including privacy and human-in-the-loop review.

Requirements:
- 3+ years of experience building AI or ML products.
- Strong Python and FastAPI.
- Experience with LLMs, RAG, embeddings, vector databases, and prompt engineering.
- Bonus: recruiting, talent sourcing, ATS integrations, LangGraph, observability, and privacy.

Location: Remote or Bengaluru hybrid.
"""

SAMPLE_RESUMES = """Name: Ishaan Kapoor
Current Title: AI Product Engineer
Location: Bengaluru
Experience: 4.5 years
Summary: Builds agentic AI products with strong Python, FastAPI, LangGraph, RAG, embeddings, vector databases, and recruiter-facing UX.
Skills: Python, FastAPI, AI agents, LangGraph, RAG, embeddings, vector databases, prompt engineering, evaluations, PostgreSQL, Docker
Projects:
- Built a resume-to-shortlist agent that parsed JDs, normalized skills, ranked candidates, and generated recruiter notes.
- Shipped a LangGraph support agent with tool calling, trace logs, and human approval before actions.
Achievements:
- Reduced screening time by 35% in a pilot workflow.
- Created evaluation tests for extraction quality, ranking quality, and hallucination risk.
Preferences: open to remote or Bengaluru hybrid, likes ownership and agentic AI.
Notice: 30 days
Salary: 36 LPA

---

Name: Kavya Menon
Current Title: Talent Intelligence Analyst
Location: Pune
Experience: 5 years
Summary: Recruiting-tech specialist with sourcing, ATS workflows, scoring models, analytics, and candidate engagement experience.
Skills: Python, recruiting, talent sourcing, ATS, scoring models, ranking, analytics, PostgreSQL, privacy
Projects:
- Built a talent market map that segmented candidates by skills, seniority, availability, and reply likelihood.
- Designed outreach templates and measured candidate interest signals across hiring funnels.
Achievements:
- Improved recruiter reply rates by 18% using personalized hooks.
- Built a transparent candidate scorecard used by hiring managers.
Preferences: remote work, recruiting domain, candidate engagement.
Notice: 20 days
Salary: 28 LPA

---

Name: Dev Sharma
Current Title: ML Engineer
Location: Hyderabad
Experience: 3.5 years
Summary: ML engineer focused on semantic search, RAG, vector databases, ranking, and evaluation loops.
Skills: Python, RAG, embeddings, semantic search, vector databases, ranking, PyTorch, transformers, FastAPI, AWS
Projects:
- Built hybrid retrieval for noisy technical profiles using vector search and cross-encoder reranking.
- Created an evaluation dashboard for precision, recall, latency, and failure examples.
Achievements:
- Improved top-5 retrieval precision from 70% to 86%.
Preferences: remote work, hard ranking problems, applied AI.
Notice: 45 days
Salary: 32 LPA
"""


app = FastAPI(
    title="TalentSignal Agent",
    description="AI-powered talent scouting and engagement prototype for Deccan AI Catalyst.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
agent = TalentScoutingAgent()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/sample-jd")
async def sample_jd() -> dict[str, str]:
    return {"job_description": SAMPLE_JD}


@app.get("/api/sample-resumes")
async def sample_resumes() -> dict[str, str]:
    return {"candidate_resumes": SAMPLE_RESUMES}


@app.post("/api/analyze")
async def analyze(payload: AnalyzeRequest) -> JSONResponse:
    run = agent.run(
        job_description=payload.job_description,
        top_k=payload.top_k,
        simulate=payload.simulate_outreach,
        candidate_resumes=payload.candidate_resumes,
        include_sample_market=payload.include_sample_market,
    )
    return JSONResponse(content=jsonable_encoder(run))


def run() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
