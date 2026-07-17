"""Draft query-lens generation for scholar-authored research inputs."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict


STOPWORDS = {
    "the", "and", "or", "of", "in", "to", "for", "a", "an", "how", "does",
    "do", "is", "are", "with", "into", "about", "through", "by", "on",
}

SYNONYMS = {
    "afghanistan": ["Af-Pak", "Hindu Kush", "Taliban"],
    "central asia": ["Turkestan", "the stans", "post-Soviet Central Asia"],
    "eurasia": ["Eurasian", "Heartland", "post-Soviet space"],
    "security": ["regional security", "security imaginary", "securitization"],
    "geopolitics": ["geopolitical imagination", "critical geopolitics", "Heartland"],
    "russia": ["Russian", "near abroad", "post-Soviet order"],
    "cartography": ["mapping", "map semiotics", "representational space"],
}

THEORY_TERMS = [
    "regional security complex",
    "critical geopolitics",
    "classical geopolitics",
    "discourse analysis",
    "semiotics",
]


@dataclass
class ResearchInput:
    research_question: str
    topic_domain: str
    region: str
    time_period: str
    key_concepts: str
    required_corpus_scope: str
    exclusion_terms: str
    scholar_notes: str
    output_type: str


@dataclass
class QueryLens:
    main_query_terms: list[str]
    synonyms: dict[str, list[str]]
    region_terms: list[str]
    theoretical_terms: list[str]
    exclusion_terms: list[str]
    layer_hypothesis: str
    recoll_query_preview: str
    safety_note: str


def build_lens(data: ResearchInput) -> QueryLens:
    source = " ".join([
        data.research_question,
        data.topic_domain,
        data.region,
        data.key_concepts,
    ])
    terms = _terms(source)
    region_terms = _terms(data.region)
    exclusion_terms = _terms(data.exclusion_terms)
    chosen_synonyms = {
        key: values for key, values in SYNONYMS.items()
        if key in source.lower() or any(part in terms for part in key.split())
    }
    layer = infer_layer(data)
    theoretical_terms = [term for term in THEORY_TERMS if _matches(term, source)]
    if layer in {"B", "AB"}:
        theoretical_terms = sorted(set(theoretical_terms + THEORY_TERMS[:3]))
    preview = build_query_string(terms, chosen_synonyms, region_terms, theoretical_terms, exclusion_terms)
    return QueryLens(
        main_query_terms=terms,
        synonyms=chosen_synonyms,
        region_terms=region_terms,
        theoretical_terms=theoretical_terms,
        exclusion_terms=exclusion_terms,
        layer_hypothesis=layer,
        recoll_query_preview=preview,
        safety_note=(
            "Planning stage only. This lens does not run Recoll, create evidence, "
            "modify the queue, or promote ontology."
        ),
    )


def infer_layer(data: ResearchInput) -> str:
    text = " ".join([data.research_question, data.topic_domain, data.region, data.key_concepts]).lower()
    empirical = any(term in text for term in ["afghanistan", "central asia", "eurasia", "russia", "china", "taliban"])
    theory = any(term in text for term in ["theory", "method", "geopolit", "semiotic", "cartograph", "discourse", "rsct"])
    if empirical and theory:
        return "AB"
    if empirical:
        return "A"
    if theory:
        return "B"
    return "Ambiguous"


def build_query_string(
    terms: list[str],
    synonyms: dict[str, list[str]],
    region_terms: list[str],
    theoretical_terms: list[str],
    exclusion_terms: list[str],
) -> str:
    groups: list[str] = []
    if terms:
        groups.append(_or_group(terms[:10]))
    for key, values in synonyms.items():
        groups.append(_or_group([key] + values))
    if region_terms:
        groups.append(_or_group(region_terms[:8]))
    if theoretical_terms:
        groups.append(_or_group(theoretical_terms[:8]))
    query = " AND ".join(groups) if groups else ""
    if exclusion_terms:
        query += " " + " ".join(f"-{term}" for term in exclusion_terms)
    return query or "(enter scholar question to preview lens)"


def to_dict(lens: QueryLens) -> dict:
    return asdict(lens)


def _terms(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    terms = []
    for word in raw:
        cleaned = word.strip("-'")
        if len(cleaned) < 3 or cleaned in STOPWORDS:
            continue
        if cleaned not in terms:
            terms.append(cleaned)
    return terms


def _matches(term: str, text: str) -> bool:
    return any(part in text.lower() for part in term.lower().split())


def _or_group(values: list[str]) -> str:
    quoted = [f'"{value}"' if " " in value else value for value in values]
    return "(" + " OR ".join(quoted) + ")"
