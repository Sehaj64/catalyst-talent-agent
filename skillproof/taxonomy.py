from __future__ import annotations

from skillproof.models import Question


SKILLS = {
    "Python": {
        "category": "Programming",
        "aliases": ["python", "pandas", "numpy", "fastapi", "flask", "django"],
        "adjacent": ["Testing", "APIs", "Data Analysis"],
        "resources": [
            "Python official tutorial: https://docs.python.org/3/tutorial/",
            "FastAPI docs: https://fastapi.tiangolo.com/",
            "Pandas getting started: https://pandas.pydata.org/docs/getting_started/",
        ],
        "questions": [
            Question(
                "Describe a Python project where you converted messy input into reliable output. What failed first, and how did you fix it?",
                "practical",
                ("project", "debug", "input", "output", "test", "exception"),
            ),
            Question(
                "How would you structure a Python service that must parse resumes, score candidates, and return a report?",
                "system",
                ("module", "api", "validation", "logging", "test", "queue"),
            ),
        ],
    },
    "SQL": {
        "category": "Data",
        "aliases": ["sql", "postgres", "mysql", "joins", "window functions", "query"],
        "adjacent": ["Data Modeling", "Analytics", "Dashboards"],
        "resources": [
            "Mode SQL tutorial: https://mode.com/sql-tutorial/",
            "PostgreSQL SELECT docs: https://www.postgresql.org/docs/current/sql-select.html",
        ],
        "questions": [
            Question(
                "Walk through the most complex SQL query you have written. Which joins or aggregations made it difficult?",
                "practical",
                ("join", "group", "window", "index", "cte", "performance"),
            ),
            Question(
                "An analytics dashboard double-counts users after joining events and accounts. How would you debug it?",
                "scenario",
                ("duplicate", "join", "grain", "count", "primary", "group"),
            ),
        ],
    },
    "React": {
        "category": "Frontend",
        "aliases": ["react", "next.js", "nextjs", "jsx", "hooks", "components"],
        "adjacent": ["TypeScript", "Testing", "Accessibility"],
        "resources": [
            "React docs: https://react.dev/learn",
            "Next.js docs: https://nextjs.org/docs",
        ],
        "questions": [
            Question(
                "Explain how you decide where state should live in a React app with forms, filters, and server data.",
                "system",
                ("state", "props", "effect", "server", "cache", "component"),
            ),
            Question(
                "A React page becomes slow after adding a candidate table. What would you profile and optimize?",
                "scenario",
                ("render", "memo", "virtual", "pagination", "profile", "state"),
            ),
        ],
    },
    "TypeScript": {
        "category": "Frontend",
        "aliases": ["typescript", "ts", "types", "interface", "generics"],
        "adjacent": ["React", "APIs", "Testing"],
        "resources": [
            "TypeScript handbook: https://www.typescriptlang.org/docs/handbook/intro.html",
            "TypeScript for React: https://react.dev/learn/typescript",
        ],
        "questions": [
            Question(
                "When would you use an interface, union type, or generic in TypeScript? Give an example from an app.",
                "foundation",
                ("interface", "union", "generic", "type", "compile", "example"),
            ),
            Question(
                "How would you model an API response that can return success data or validation errors?",
                "practical",
                ("union", "discriminated", "error", "schema", "narrow", "response"),
            ),
        ],
    },
    "Machine Learning": {
        "category": "AI/ML",
        "aliases": ["machine learning", "ml", "classification", "regression", "model", "scikit-learn"],
        "adjacent": ["Data Analysis", "Model Evaluation", "MLOps"],
        "resources": [
            "Google Machine Learning Crash Course: https://developers.google.com/machine-learning/crash-course",
            "Scikit-learn user guide: https://scikit-learn.org/stable/user_guide.html",
        ],
        "questions": [
            Question(
                "How do you choose an evaluation metric when false positives and false negatives have different business costs?",
                "scenario",
                ("precision", "recall", "cost", "threshold", "confusion", "metric"),
            ),
            Question(
                "Tell me about a model that looked good offline but failed in practice. What changed?",
                "practical",
                ("drift", "validation", "leakage", "baseline", "feature", "monitor"),
            ),
        ],
    },
    "LLM / Generative AI": {
        "category": "AI/ML",
        "aliases": ["llm", "generative ai", "genai", "openai", "rag", "prompt", "langchain"],
        "adjacent": ["Evaluation", "Prompt Engineering", "Vector Search"],
        "resources": [
            "OpenAI docs: https://platform.openai.com/docs",
            "LangChain docs: https://python.langchain.com/docs/",
            "RAG evaluation guide: https://docs.ragas.io/",
        ],
        "questions": [
            Question(
                "How would you evaluate an LLM assessment agent so it is not just fluent but actually correct?",
                "scenario",
                ("rubric", "ground truth", "eval", "hallucination", "judge", "dataset"),
            ),
            Question(
                "Explain a RAG pipeline and where retrieval errors can enter the answer.",
                "foundation",
                ("embedding", "retrieval", "chunk", "rerank", "context", "citation"),
            ),
        ],
    },
    "Data Analysis": {
        "category": "Data",
        "aliases": ["data analysis", "analytics", "eda", "excel", "power bi", "tableau", "dashboard"],
        "adjacent": ["SQL", "Statistics", "Business Communication"],
        "resources": [
            "Kaggle data cleaning: https://www.kaggle.com/learn/data-cleaning",
            "Storytelling with Data blog: https://www.storytellingwithdata.com/blog",
        ],
        "questions": [
            Question(
                "Describe an analysis where the first result was misleading. How did you validate the final answer?",
                "practical",
                ("validate", "segment", "outlier", "metric", "stakeholder", "assumption"),
            ),
            Question(
                "A business metric drops 20% overnight. What checks do you run before escalating?",
                "scenario",
                ("pipeline", "seasonality", "segment", "data quality", "baseline", "incident"),
            ),
        ],
    },
    "APIs": {
        "category": "Backend",
        "aliases": ["api", "rest", "graphql", "endpoint", "http", "json"],
        "adjacent": ["Python", "Authentication", "Testing"],
        "resources": [
            "REST API tutorial: https://restfulapi.net/",
            "FastAPI docs: https://fastapi.tiangolo.com/",
        ],
        "questions": [
            Question(
                "Design an API endpoint for submitting a candidate assessment. What should the request, response, and errors look like?",
                "system",
                ("status", "schema", "validation", "error", "auth", "idempotent"),
            ),
            Question(
                "How do you handle retries when an external scoring service times out?",
                "scenario",
                ("timeout", "retry", "backoff", "idempotency", "queue", "fallback"),
            ),
        ],
    },
    "Testing": {
        "category": "Engineering",
        "aliases": ["testing", "unit test", "pytest", "integration test", "test cases", "qa"],
        "adjacent": ["CI/CD", "Python", "TypeScript"],
        "resources": [
            "Pytest docs: https://docs.pytest.org/",
            "Testing Library docs: https://testing-library.com/docs/",
        ],
        "questions": [
            Question(
                "What tests would you write for a skill scoring engine before trusting it in hiring?",
                "scenario",
                ("unit", "edge", "fixture", "regression", "calibration", "integration"),
            ),
            Question(
                "How do you test code that calls an external LLM or API?",
                "practical",
                ("mock", "fixture", "contract", "timeout", "snapshot", "deterministic"),
            ),
        ],
    },
    "Communication": {
        "category": "Soft Skill",
        "aliases": ["communication", "stakeholder", "presentation", "documentation", "collaboration"],
        "adjacent": ["Product Thinking", "Data Analysis", "Leadership"],
        "resources": [
            "Write the Docs guide: https://www.writethedocs.org/guide/",
            "Google technical writing: https://developers.google.com/tech-writing",
        ],
        "questions": [
            Question(
                "Tell me about a time you explained a technical tradeoff to a non-technical stakeholder.",
                "behavioral",
                ("stakeholder", "tradeoff", "impact", "decision", "clarify", "outcome"),
            ),
            Question(
                "How would you summarize this assessment report for a busy hiring manager in 5 bullet points?",
                "practical",
                ("summary", "priority", "risk", "evidence", "decision", "next step"),
            ),
        ],
    },
}


CRITICALITY_CUES = {
    "High": (
        "required",
        "must have",
        "must-have",
        "mandatory",
        "strong experience",
        "need",
        "responsible for",
    ),
    "Medium": (
        "preferred",
        "good to have",
        "nice to have",
        "familiarity",
        "plus",
        "bonus",
    ),
}
