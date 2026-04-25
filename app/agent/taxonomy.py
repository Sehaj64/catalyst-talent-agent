from __future__ import annotations

import re


SKILL_ALIASES: dict[str, list[str]] = {
    "python": ["python", "py"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "react": ["react", "reactjs", "react.js"],
    "typescript": ["typescript", "ts"],
    "ai agents": ["ai agent", "ai agents", "agentic ai", "agentic workflows", "autonomous agents"],
    "llms": ["llm", "llms", "large language model", "large language models", "gpt", "openai", "claude", "gemini"],
    "langchain": ["langchain"],
    "langgraph": ["langgraph"],
    "llamaindex": ["llamaindex", "llama index"],
    "rag": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "embeddings": ["embedding", "embeddings", "sentence transformers", "sentence-transformers"],
    "vector databases": ["vector db", "vector database", "vector databases", "qdrant", "pinecone", "weaviate", "faiss", "chroma"],
    "semantic search": ["semantic search", "hybrid search"],
    "prompt engineering": ["prompt engineering", "prompting", "prompt design"],
    "tool calling": ["tool calling", "function calling", "tools", "tool use"],
    "evaluations": ["eval", "evals", "evaluation", "evaluations", "llm evaluation", "quality metrics"],
    "observability": ["observability", "tracing", "monitoring", "telemetry"],
    "mlops": ["mlops", "model serving", "model deployment"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "postgresql": ["postgres", "postgresql", "sql"],
    "redis": ["redis"],
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud"],
    "azure": ["azure"],
    "api integration": ["api", "apis", "api integration", "rest api", "webhooks"],
    "ranking": ["ranking", "ranker", "re-ranking", "reranking"],
    "scoring models": ["scoring", "scoring model", "scoring models", "matching score", "propensity score"],
    "nlp": ["nlp", "natural language processing"],
    "transformers": ["transformer", "transformers", "hugging face", "huggingface"],
    "pytorch": ["pytorch", "torch"],
    "web scraping": ["web scraping", "scraping", "crawler", "crawling"],
    "knowledge graphs": ["knowledge graph", "knowledge graphs", "graph db", "neo4j"],
    "recruiting": ["recruiting", "recruitment", "talent acquisition", "hiring"],
    "talent sourcing": ["talent sourcing", "sourcing", "candidate discovery", "candidate search"],
    "ats": ["ats", "applicant tracking system", "greenhouse", "lever"],
    "human-in-the-loop": ["human in the loop", "human-in-the-loop", "review workflow"],
    "privacy": ["privacy", "pii", "data protection", "compliance"],
    "red teaming": ["red teaming", "safety testing", "adversarial testing"],
    "analytics": ["analytics", "dashboard", "dashboards", "business intelligence"],
}


RELATED_GROUPS: list[set[str]] = [
    {"ai agents", "llms", "langchain", "langgraph", "llamaindex", "tool calling", "human-in-the-loop"},
    {"rag", "embeddings", "vector databases", "semantic search", "ranking"},
    {"python", "fastapi", "django", "flask", "api integration"},
    {"mlops", "docker", "kubernetes", "observability", "aws", "gcp", "azure"},
    {"recruiting", "talent sourcing", "ats", "scoring models", "analytics"},
    {"nlp", "transformers", "pytorch", "prompt engineering", "evaluations"},
    {"privacy", "red teaming", "observability", "human-in-the-loop"},
]


DOMAIN_ALIASES: dict[str, list[str]] = {
    "hrtech": ["hrtech", "hr tech", "recruiting", "recruitment", "talent", "hiring", "candidate"],
    "saas": ["saas", "b2b", "subscription"],
    "fintech": ["fintech", "banking", "payments", "lending"],
    "healthcare": ["healthcare", "health tech", "clinical"],
    "legaltech": ["legal", "legaltech", "contracts"],
    "developer tools": ["developer tools", "devtools", "api platform"],
    "enterprise": ["enterprise", "b2b", "internal tooling"],
    "sales": ["sales", "gtm", "crm", "revops"],
    "security": ["security", "compliance", "privacy"],
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("/", " ")).strip()


def normalize_skill(skill: str) -> str:
    lowered = _clean(skill)
    for canonical, aliases in SKILL_ALIASES.items():
        if lowered == canonical or lowered in aliases:
            return canonical
    return lowered


def extract_skills(text: str) -> list[str]:
    haystack = f" {_clean(text)} "
    found: list[str] = []
    alias_pairs = sorted(
        ((alias, canonical) for canonical, aliases in SKILL_ALIASES.items() for alias in aliases + [canonical]),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    for alias, canonical in alias_pairs:
        pattern = r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, haystack) and canonical not in found:
            found.append(canonical)
    return found


def extract_domains(text: str) -> list[str]:
    haystack = _clean(text)
    domains: list[str] = []
    for domain, aliases in DOMAIN_ALIASES.items():
        if any(alias in haystack for alias in aliases) and domain not in domains:
            domains.append(domain)
    return domains


def related_for(skill: str, candidate_skills: set[str]) -> list[str]:
    canonical = normalize_skill(skill)
    related: set[str] = set()
    for group in RELATED_GROUPS:
        if canonical in group:
            related |= group & candidate_skills
    related.discard(canonical)
    return sorted(related)
