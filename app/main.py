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


@app.post("/api/analyze")
async def analyze(payload: AnalyzeRequest) -> JSONResponse:
    run = agent.run(
        job_description=payload.job_description,
        top_k=payload.top_k,
        simulate=payload.simulate_outreach,
    )
    return JSONResponse(content=jsonable_encoder(run))


def run() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
