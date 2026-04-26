from __future__ import annotations

from skillproof.taxonomy import SKILLS


SAMPLE_JD = """
Senior AI Systems Engineer (Generative AI & MLOps)

We are seeking an elite engineer to architect our next-generation talent assessment engine. 
The ideal candidate has deep expertise in building production-grade LLM applications, 
orchestrating RAG pipelines, and implementing robust MLOps workflows.

Key Responsibilities:
- Design and scale distributed REST APIs in Python (FastAPI/Flask) for high-concurrency AI workloads.
- Implement advanced RAG architectures using Vector Databases (Pinecone/Milvus) and semantic search.
- Develop custom evaluation frameworks for LLM outputs (faithfulness, relevancy, toxicity).
- Build interactive data visualization dashboards in React/TypeScript to surface talent insights.
- Ensure 99.9% reliability through rigorous unit testing, integration testing, and CI/CD.

Required: Python (Expert), React, TypeScript, SQL, LLM Orchestration (LangChain/LlamaIndex), 
Cloud Infrastructure (AWS/GCP), and a proven track record of solving 'impossible' technical bottlenecks.
"""


SAMPLE_RESUME = """
Arjun S. | Senior AI Engineer

- Built a multi-agent RAG system for legal discovery, processing 10M+ documents with 94% retrieval accuracy.
- Architected a high-throughput Python API using FastAPI and Celery, handling 2,000+ requests/sec with sub-100ms latency.
- Developed a React/TypeScript analytics suite for MLOps monitoring, featuring real-time drift detection and SHAP/LIME visualizations.
- Implemented automated LLM evaluation pipelines that reduced manual 'vibes-based' testing by 80%.
- Migrated legacy monolithic data pipelines to a modern Snowflake/dbt stack, improving query performance by 4x.
- Reduced cloud compute costs by $150k/year through strategic model quantization and aggressive caching strategies.
- Published internal 'Clean Code for ML' standards and mentored a team of 12 engineers on CI/CD and testing best practices.
"""


def _sample_answers() -> dict[str, str]:
    answer_bank = {
        "Python": [
            (
                "I architected a high-concurrency data ingestion engine using Python's asyncio and multiprocessing modules. "
                "The primary challenge was the Global Interpreter Lock (GIL) during heavy CPU-bound parsing. I solved this by "
                "offloading parsing to a ProcessPoolExecutor while maintaining the I/O loop in asyncio. This setup handled "
                "2k requests/sec. I implemented strict pydantic validation to ensure 100% type safety across the service."
            ),
            (
                "When scaling a Python service, I prioritize memory profile over raw speed. I use memory-profiler to catch leaks "
                "in long-running worker processes. For I/O bottlenecks, I implement custom middleware for circuit breaking and "
                "exponential backoff to prevent cascading failures when external AI model endpoints go down."
            ),
        ],
        "React": [
            (
                "I built a real-time MLOps dashboard using React and Tailwind CSS. To handle high-frequency metric streams, "
                "I implemented a custom hook with requestAnimationFrame to throttle state updates, preventing UI jank. "
                "I used React.memo and useMemo aggressively for complex SVG data visualizations, maintaining a smooth 60fps "
                "even with 5,000+ data points being updated via WebSockets."
            ),
            (
                "For global state, I prefer a 'State-at-the-Edge' approach—keeping state as local as possible. I use TanStack Query "
                "for server state and Zustand for lightweight global UI state. This prevents the 'Context Hell' common in large "
                "React apps and makes individual components easier to test in isolation."
            ),
        ],
        "LLM / Generative AI": [
            (
                "In my last project, I built a 'Self-RAG' system. It doesn't just retrieve context; it uses a secondary LLM "
                "to evaluate if the retrieved context is relevant before generating an answer. If relevant context is missing, "
                "it triggers a multi-step search. This reduced hallucinations in our talent agent from 12% down to <1%."
            ),
            (
                "To evaluate LLM quality, I moved beyond 'vibe checks'. I implemented the 'RAGAS' framework to measure "
                "faithfulness, answer relevance, and context precision. We used a 'Golden Dataset' of 500 human-verified "
                "question-answer pairs to run regression tests before every deployment of the prompt templates."
            ),
        ],
        "Testing": [
            (
                "My testing strategy follows the 'Testing Trophy': static analysis with Pyright, heavy unit testing for business logic, "
                "and strategic E2E tests for critical user paths. I use Playwright for browser testing and VCR.py to mock "
                "external AI API responses, ensuring our CI pipeline is fast, deterministic, and doesn't burn API credits."
            ),
            (
                "For ML systems, I implement 'Property-Based Testing' using Hypothesis to generate edge-case inputs for my "
                "data normalization utilities. This caught several silent bugs in how we handled non-ASCII characters in "
                "candidate resumes that traditional unit tests missed."
            ),
        ],
        "Communication": [
            (
                "I once had to convince a Product Manager to delay a feature release because our LLM evaluation showed a 15% drop "
                "in answer accuracy for edge cases. I presented the 'Cost of a Wrong Answer' in terms of user trust and support load. "
                "We delayed by one week, improved the retrieval strategy, and the feature launched with record-high CSAT scores."
            ),
            (
                "When communicating technical debt to non-technical stakeholders, I use the 'Interest Rate' metaphor. "
                "I explain that skipping unit tests now is like taking a high-interest loan; we'll eventually spend 10x more time "
                "fixing bugs than it would take to build it right. This framing consistently gets me the 'Buy-In' for quality."
            ),
        ],
    }
    answers: dict[str, str] = {}
    for skill_name, config in SKILLS.items():
        skill_answers = answer_bank.get(skill_name, [])
        for index, question in enumerate(config["questions"]):
            key = f"{skill_name}::{question.prompt}"
            if index < len(skill_answers):
                answers[key] = skill_answers[index]
            else:
                answers[key] = (
                    f"I would demonstrate {skill_name} with a role-specific artifact, measurable outcome, "
                    "failure case, and short README explaining the tradeoffs."
                )
    return answers


SAMPLE_ANSWERS = _sample_answers()
