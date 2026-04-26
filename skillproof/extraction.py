from __future__ import annotations

import re
from collections import defaultdict

from skillproof.models import SkillCandidate
from skillproof.taxonomy import CRITICALITY_CUES, SKILLS


WORD_RE = re.compile(r"[A-Za-z0-9+#./-]+")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def contains_alias(text: str, alias: str) -> bool:
    alias_norm = normalize(alias)
    if len(alias_norm) <= 3:
        return re.search(rf"(?<![a-z0-9]){re.escape(alias_norm)}(?![a-z0-9])", text) is not None
    return alias_norm in text


def find_skill_mentions(text: str) -> dict[str, list[str]]:
    text_norm = normalize(text)
    sentences = split_sentences(text)
    mentions: dict[str, list[str]] = defaultdict(list)
    for skill_name, config in SKILLS.items():
        aliases = [skill_name, *config["aliases"]]
        if not any(contains_alias(text_norm, alias) for alias in aliases):
            continue
        for sentence in sentences:
            sentence_norm = normalize(sentence)
            if any(contains_alias(sentence_norm, alias) for alias in aliases):
                mentions[skill_name].append(sentence[:280])
    return dict(mentions)


def infer_criticality(skill_mentions: list[str]) -> str:
    combined = normalize(" ".join(skill_mentions))
    for level, cues in CRITICALITY_CUES.items():
        if any(cue in combined for cue in cues):
            return level
    return "Medium"


def evidence_quality(snippets: list[str]) -> int:
    if not snippets:
        return 0
    action_words = (
        "built",
        "created",
        "designed",
        "implemented",
        "deployed",
        "optimized",
        "improved",
        "automated",
        "analyzed",
        "led",
    )
    metric_re = re.compile(r"(\d+%|\d+\s*(users|hours|mins|minutes|seconds|x|projects|models|apis))", re.I)
    score = min(12, len(snippets) * 4)
    joined = normalize(" ".join(snippets))
    score += min(8, sum(2 for word in action_words if word in joined))
    score += min(5, len(metric_re.findall(" ".join(snippets))) * 2)
    return min(25, score)


def extract_candidates(jd_text: str, resume_text: str) -> list[SkillCandidate]:
    jd_mentions = find_skill_mentions(jd_text)
    resume_mentions = find_skill_mentions(resume_text)
    all_names = set(jd_mentions) | set(resume_mentions)

    candidates: list[SkillCandidate] = []
    for name in sorted(all_names):
        config = SKILLS[name]
        criticality = infer_criticality(jd_mentions.get(name, []))
        if name not in jd_mentions:
            criticality = "Resume-only"
        candidates.append(
            SkillCandidate(
                name=name,
                category=config["category"],
                criticality=criticality,
                jd_mentions=jd_mentions.get(name, []),
                resume_evidence=resume_mentions.get(name, []),
                questions=list(config["questions"]),
                adjacent_skills=list(config["adjacent"]),
                resources=list(config["resources"]),
            )
        )

    priority = {"High": 0, "Medium": 1, "Resume-only": 2}
    candidates.sort(
        key=lambda skill: (
            priority.get(skill.criticality, 3),
            -evidence_quality(skill.resume_evidence),
            skill.name,
        )
    )
    return candidates[:8]

