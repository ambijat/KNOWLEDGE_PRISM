"""Research rumination helpers for the scholar-facing GUI.

This module stores and organises scholar-authored fragments only. It does not
write to evidence, ontology, corpus, queue, disposition, boundary, or research
state tables.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .db_access import ROOT
from .query_lens import SYNONYMS, build_query_string
from .report_writer import timestamp


RUMINATION_DIR = ROOT / "outputs" / "gui_reports" / "rumination"
FRAGMENT_LABEL = "scholar_input_not_evidence"
BRIEF_PROVENANCE_NOTE = (
    "This brief is generated from scholar input and Knowledge Prism diagnostic logic. "
    "It is not evidence verification and does not promote any claim into the ontology."
)

INPUT_TYPES = [
    "idea",
    "voice/dictated note",
    "rough title",
    "problem fragment",
    "research question",
    "objective",
    "concept",
    "case/region",
    "time period",
    "theory hunch",
    "methodology hunch",
    "literature clue",
    "evidence need",
    "supervisor comment",
    "paragraph",
    "partial synopsis",
    "full synopsis",
    "full draft",
]

SOURCE_NOTES = [
    "self-thought",
    "supervisor",
    "class discussion",
    "reading",
    "field observation",
    "lecture",
    "other",
]

CONFIDENCE_LEVELS = ["weak", "medium", "strong"]

RESEARCH_ORGANS = [
    "Title",
    "Background",
    "Statement of Problem",
    "Research Gap",
    "Research Questions",
    "Objectives",
    "Scope",
    "Methodology",
    "Conceptual Framework",
    "Literature Clusters",
    "Evidence Needs",
    "Case / Region / Time Period",
    "Chapterisation / Structure",
    "Supervisor Questions",
    "Revision Tasks",
]

INPUT_TYPE_TO_ORGANS = {
    "rough title": ["Title"],
    "problem fragment": ["Statement of Problem"],
    "research question": ["Research Questions"],
    "objective": ["Objectives"],
    "concept": ["Conceptual Framework"],
    "case/region": ["Case / Region / Time Period", "Scope"],
    "time period": ["Case / Region / Time Period", "Scope"],
    "theory hunch": ["Conceptual Framework", "Methodology"],
    "methodology hunch": ["Methodology"],
    "literature clue": ["Literature Clusters"],
    "evidence need": ["Evidence Needs"],
    "supervisor comment": ["Supervisor Questions", "Revision Tasks"],
    "paragraph": ["Background"],
    "partial synopsis": ["Background", "Statement of Problem", "Research Questions"],
    "full synopsis": ["Title", "Background", "Statement of Problem", "Research Gap", "Research Questions", "Objectives"],
    "full draft": ["Background", "Statement of Problem", "Research Questions"],
}

ORGAN_KEYWORDS = {
    "Title": ["title", "called", "working title"],
    "Background": ["background", "context", "history", "debate"],
    "Statement of Problem": ["problem", "puzzle", "tension", "contradiction"],
    "Research Gap": ["gap", "understudied", "missing", "neglect"],
    "Research Questions": ["question", "why", "how", "whether", "?"],
    "Objectives": ["objective", "aim", "purpose", "will examine"],
    "Scope": ["scope", "limit", "exclude", "focus"],
    "Methodology": ["method", "methodology", "discourse", "sample", "compare", "analysis"],
    "Conceptual Framework": ["concept", "theory", "framework", "lens", "geopolitic"],
    "Literature Clusters": ["literature", "author", "book", "article", "reading"],
    "Evidence Needs": ["evidence", "source", "document", "archive", "data"],
    "Case / Region / Time Period": ["case", "region", "eurasia", "afghanistan", "central asia", "period"],
    "Chapterisation / Structure": ["chapter", "structure", "outline", "section"],
    "Supervisor Questions": ["supervisor", "ask", "clarify", "feedback"],
    "Revision Tasks": ["revise", "rewrite", "task", "fix", "todo"],
}

DIAGNOSIS_PATTERNS = {
    "Title": [r"\btitle\b", r"^#\s+"],
    "Background": [r"\bbackground\b", r"\bcontext\b"],
    "Statement of Problem": [r"\bproblem\b", r"\bpuzzle\b"],
    "Research Gap": [r"\bgap\b", r"\bunderstudied\b", r"\bmissing\b"],
    "Research Questions": [r"\bresearch question", r"\?", r"\bhow\b", r"\bwhy\b"],
    "Objectives": [r"\bobjective", r"\baim"],
    "Scope": [r"\bscope\b", r"\bcase\b", r"\bperiod\b"],
    "Methodology": [r"\bmethod", r"\bmethodology\b", r"\banalysis\b"],
    "Conceptual Framework": [r"\bconcept", r"\bframework\b", r"\btheory\b"],
    "Literature Clusters": [r"\bliterature\b", r"\bscholar", r"\bauthor"],
    "Evidence Needs": [r"\bevidence\b", r"\bsource\b", r"\bcorpus\b"],
    "Chapterisation / Structure": [r"\bchapter\b", r"\bstructure\b"],
}


@dataclass
class ResearchFragment:
    fragment_id: str
    created_at: str
    input_type: str
    text: str
    source_note: str
    confidence: str
    tags: list[str]
    label: str
    assigned_organs: list[str]
    classification_reason: str


def new_fragment(
    input_type: str,
    text: str,
    source_note: str,
    confidence: str,
    tags: str,
) -> ResearchFragment:
    assigned = classify_text(input_type, text)
    return ResearchFragment(
        fragment_id=f"frag-{uuid.uuid4().hex[:10]}",
        created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        input_type=input_type,
        text=text.strip(),
        source_note=source_note,
        confidence=confidence,
        tags=_tag_list(tags),
        label=FRAGMENT_LABEL,
        assigned_organs=assigned,
        classification_reason=classification_reason(input_type, text, assigned),
    )


def classify_fragment(fragment: ResearchFragment) -> ResearchFragment:
    assigned = classify_text(fragment.input_type, fragment.text)
    fragment.assigned_organs = assigned
    fragment.classification_reason = classification_reason(fragment.input_type, fragment.text, assigned)
    return fragment


def classify_text(input_type: str, text: str) -> list[str]:
    organs: list[str] = []
    for organ in INPUT_TYPE_TO_ORGANS.get(input_type, []):
        _append_unique(organs, organ)
    lowered = text.lower()
    for organ, terms in ORGAN_KEYWORDS.items():
        if any(term in lowered for term in terms):
            _append_unique(organs, organ)
    if not organs:
        organs.append("Background")
    return organs[:4]


def classification_reason(input_type: str, text: str, assigned: list[str]) -> str:
    reason = [f"input_type={input_type}"]
    lowered = text.lower()
    hits = [
        f"{organ}:{term}"
        for organ, terms in ORGAN_KEYWORDS.items()
        for term in terms
        if term in lowered
    ]
    if hits:
        reason.append("keyword_hits=" + ", ".join(hits[:8]))
    reason.append("label=" + FRAGMENT_LABEL)
    reason.append("assigned_organs=" + ", ".join(assigned))
    return "; ".join(reason)


def empty_organ_map() -> dict[str, dict[str, Any]]:
    return {
        organ: {
            "organ": organ,
            "fragments": [],
            "status": "missing",
            "confidence": "weak",
            "suggested_next_action": suggested_next_action(organ, []),
        }
        for organ in RESEARCH_ORGANS
    }


def build_organ_map(fragments: list[ResearchFragment]) -> dict[str, dict[str, Any]]:
    organ_map = empty_organ_map()
    for fragment in fragments:
        for organ in fragment.assigned_organs:
            if organ not in organ_map:
                continue
            organ_map[organ]["fragments"].append(fragment)
    for organ, entry in organ_map.items():
        assigned = entry["fragments"]
        entry["status"] = "present" if assigned else "missing"
        entry["confidence"] = organ_confidence(assigned)
        entry["suggested_next_action"] = suggested_next_action(organ, assigned)
    return organ_map


def organ_confidence(fragments: list[ResearchFragment]) -> str:
    if not fragments:
        return "weak"
    scores = {"weak": 1, "medium": 2, "strong": 3}
    average = sum(scores.get(fragment.confidence, 1) for fragment in fragments) / len(fragments)
    if average >= 2.6:
        return "strong"
    if average >= 1.7:
        return "medium"
    return "weak"


def suggested_next_action(organ: str, fragments: list[ResearchFragment]) -> str:
    if not fragments:
        return f"Add a scholar fragment for {organ}; keep it labelled {FRAGMENT_LABEL}."
    if organ_confidence(fragments) == "weak":
        return "Clarify the fragment, add source context, or ask the supervisor before drafting."
    if len(fragments) == 1:
        return "Add one corroborating or contrasting scholar fragment before drafting polished text."
    return "Ready for draft support; still not evidence and still outside ontology."


def draft_organ_text(organ: str, organ_map: dict[str, dict[str, Any]]) -> str:
    fragments = organ_map.get(organ, {}).get("fragments", [])
    if not fragments:
        return f"## {organ}\n\nNo scholar fragments assigned yet. Add rumination before drafting this organ.\n"
    lines = [
        f"## {organ}",
        "",
        "Draft support only. This text is not evidence and must not enter evidence tables.",
        "",
    ]
    for index, fragment in enumerate(fragments, start=1):
        lines.append(f"{index}. {fragment.text}")
    lines.extend(["", f"Status: {organ_confidence(fragments)}"])
    return "\n".join(lines)


def generate_synopsis_skeleton(organ_map: dict[str, dict[str, Any]]) -> str:
    lines = [
        "# Synopsis Skeleton",
        "",
        "Draft support only. Scholar input remains labelled scholar_input_not_evidence.",
        "",
    ]
    for organ in RESEARCH_ORGANS:
        lines.append(f"## {organ}")
        lines.append(draft_organ_text(organ, organ_map).split("\n\n", 2)[-1])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def diagnose_draft(text: str) -> dict[str, Any]:
    lowered = text.lower()
    present: list[str] = []
    for organ, patterns in DIAGNOSIS_PATTERNS.items():
        if any(re.search(pattern, lowered, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns):
            present.append(organ)
    missing = [organ for organ in RESEARCH_ORGANS if organ not in present]
    weak = [
        organ for organ in present
        if len(re.findall("|".join(DIAGNOSIS_PATTERNS.get(organ, [])), lowered, flags=re.IGNORECASE)) <= 1
    ]
    duplicate_candidates = _duplicate_lines(text)
    unsupported_claims = [
        line.strip()
        for line in text.splitlines()
        if _looks_like_claim(line) and not _has_evidence_marker(line)
    ][:12]
    return {
        "status": "diagnostic_only_not_evidence",
        "present_organs": present,
        "missing_organs": missing,
        "weak_organs": weak,
        "duplicated_organs_or_lines": duplicate_candidates,
        "unclear_research_question": "Research Questions" not in present,
        "unsupported_claims": unsupported_claims,
        "methodology_gaps": "Methodology" not in present,
        "literature_gaps": "Literature Clusters" not in present,
        "missing_scope": "Scope" not in present,
        "weak_chapterisation": "Chapterisation / Structure" not in present,
        "safety_note": (
            "Draft diagnosis organises scholar writing only. It does not verify claims "
            "or promote any material into ontology."
        ),
    }


def concept_fit(
    concepts_text: str,
    fragments: list[ResearchFragment],
    design_nodes: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    concepts = extract_concepts(concepts_text, fragments)
    results: list[dict[str, str]] = []
    design_labels = [str(row.get("label", "")).lower() for row in design_nodes]
    evidence_titles = [str(row.get("title", "")).lower() for row in evidence_rows]
    queue_titles = [str(row.get("title", "")).lower() for row in queue_rows]
    fragment_text = " ".join(fragment.text for fragment in fragments).lower()
    for concept in concepts:
        concept_l = concept.lower()
        if any(concept_l in label or label in concept_l for label in design_labels if label):
            status = "design_map_match_not_verified"
        elif any(concept_l in title for title in evidence_titles):
            status = "sample_supported_related"
        elif any(concept_l in title for title in queue_titles):
            status = "queue_related"
        else:
            status = "absent_from_project"
        if status == "absent_from_project":
            next_step = "needs_literature_search"
        elif status == "design_map_match_not_verified":
            next_step = "Compare against sampled corpus before any evidence claim."
        elif status == "queue_related":
            next_step = "Review queue status before sampling."
        else:
            next_step = "Inspect sampled verdict before using in argument."
        results.append(
            {
                "concept": concept,
                "appears_in_scholar_fragments": "yes" if concept_l in fragment_text else "no",
                "fit_label": status,
                "next_step": next_step,
            }
        )
    return results


def extract_concepts(concepts_text: str, fragments: list[ResearchFragment]) -> list[str]:
    raw = concepts_text
    if not raw.strip():
        raw = " ".join(
            fragment.text
            for fragment in fragments
            if fragment.input_type in {"concept", "theory hunch", "problem fragment", "research question"}
        )
    parts = re.split(r"[,;\n]+", raw)
    concepts: list[str] = []
    for part in parts:
        cleaned = part.strip(" .:-")
        if not cleaned:
            continue
        words = re.findall(r"[A-Za-z][A-Za-z\-']+", cleaned)
        if len(words) > 6:
            words = words[:6]
        concept = " ".join(words).strip()
        if len(concept) >= 3:
            _append_unique(concepts, concept)
    if not concepts:
        for fragment in fragments[:8]:
            terms = re.findall(r"[A-Za-z][A-Za-z\-']+", fragment.text)
            if terms:
                _append_unique(concepts, " ".join(terms[:3]))
    return concepts[:20]


def literature_search_plan(
    fragments: list[ResearchFragment],
    organ_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    text = " ".join(fragment.text for fragment in fragments)
    terms = _terms(text)
    region_terms = _organ_terms(organ_map, "Case / Region / Time Period")
    concept_terms = _organ_terms(organ_map, "Conceptual Framework")
    method_terms = _organ_terms(organ_map, "Methodology")
    gap_terms = _organ_terms(organ_map, "Research Gap")
    chosen_synonyms = {
        key: values for key, values in SYNONYMS.items()
        if key in text.lower() or any(part in terms for part in key.split())
    }
    exclusion_terms = ["op-ed", "news summary", "blog"] if len(terms) >= 3 else []
    recoll_query = build_query_string(
        terms[:10],
        chosen_synonyms,
        region_terms[:6],
        concept_terms[:6] + method_terms[:4],
        exclusion_terms,
    )
    return {
        "status": "search_strategy_only_not_retrieval",
        "search_terms": terms[:20],
        "anchor_candidate_categories": [
            "classic geopolitical work",
            "regional-order work",
            "theoretical or methodological work",
            "cartographic or spatial-imagination work",
            "corpus-specific discovery",
        ],
        "theory_source_needs": concept_terms or ["Identify theory/lens terms in Conceptual Framework."],
        "empirical_source_needs": region_terms or ["Specify case, region, and time period."],
        "methodology_source_needs": method_terms or ["Specify method and sampling protocol."],
        "gap_source_needs": gap_terms or ["Add literature gap fragments."],
        "exclusion_terms": exclusion_terms,
        "recoll_query_suggestion": recoll_query,
        "zotero_openalex_suggestion": _zotero_openalex_suggestion(terms, concept_terms, region_terms),
        "safety_note": "This plan does not run Recoll and does not create evidence.",
    }


def supervisor_brief(
    organ_map: dict[str, dict[str, Any]],
    plan: dict[str, Any] | None = None,
) -> str:
    def organ_text(organ: str) -> str:
        fragments = organ_map.get(organ, {}).get("fragments", [])
        if not fragments:
            return "_Missing or not yet clear._"
        return " ".join(fragment.text for fragment in fragments[:3])

    weak_missing = [
        organ for organ, entry in organ_map.items()
        if entry["status"] == "missing" or entry["confidence"] == "weak"
    ]
    if plan is None:
        plan = literature_search_plan([], organ_map)
    lines = [
        "# Supervisor Brief",
        "",
        BRIEF_PROVENANCE_NOTE,
        "",
        "## Working Title",
        organ_text("Title"),
        "",
        "## Current Research Problem",
        organ_text("Statement of Problem"),
        "",
        "## Research Question",
        organ_text("Research Questions"),
        "",
        "## Objectives",
        organ_text("Objectives"),
        "",
        "## Methodology Hunch",
        organ_text("Methodology"),
        "",
        "## Concepts",
        organ_text("Conceptual Framework"),
        "",
        "## Case / Region / Time Period",
        organ_text("Case / Region / Time Period"),
        "",
        "## Literature Clusters",
        organ_text("Literature Clusters"),
        "",
        "## Evidence Gaps",
        organ_text("Evidence Needs"),
        "",
        "## Weak / Missing Organs",
        "\n".join(f"- {organ}" for organ in weak_missing) or "- None flagged.",
        "",
        "## Questions for Supervisor",
        organ_text("Supervisor Questions"),
        "",
        "## Next Revision Tasks",
        organ_text("Revision Tasks"),
        "",
        "## Search Plan Snapshot",
        json.dumps(plan, indent=2, ensure_ascii=False),
        "",
    ]
    return "\n".join(lines)


def write_rumination_log(fragments: list[ResearchFragment]) -> Path:
    RUMINATION_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "rumination_log",
        "status": FRAGMENT_LABEL,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "safety_note": "Scholar thoughts are seed material, not evidence.",
        "fragments": [asdict(fragment) for fragment in fragments],
    }
    path = RUMINATION_DIR / f"{timestamp()}-rumination-log.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_organ_map_csv(organ_map: dict[str, dict[str, Any]]) -> Path:
    RUMINATION_DIR.mkdir(parents=True, exist_ok=True)
    path = RUMINATION_DIR / f"{timestamp()}-organ-map.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["organ", "status", "confidence", "fragment_ids", "suggested_next_action"])
        for organ in RESEARCH_ORGANS:
            entry = organ_map[organ]
            writer.writerow(
                [
                    organ,
                    entry["status"],
                    entry["confidence"],
                    ";".join(fragment.fragment_id for fragment in entry["fragments"]),
                    entry["suggested_next_action"],
                ]
            )
    return path


def write_supervisor_brief(markdown: str) -> Path:
    RUMINATION_DIR.mkdir(parents=True, exist_ok=True)
    path = RUMINATION_DIR / f"{timestamp()}-supervisor-brief.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def write_markdown(name: str, markdown: str) -> Path:
    RUMINATION_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    path = RUMINATION_DIR / f"{timestamp()}-{safe}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def fragments_as_rows(fragments: list[ResearchFragment]) -> list[dict[str, str]]:
    return [
        {
            "fragment_id": fragment.fragment_id,
            "input_type": fragment.input_type,
            "confidence": fragment.confidence,
            "source_note": fragment.source_note,
            "label": fragment.label,
            "assigned_organs": ", ".join(fragment.assigned_organs),
            "text": fragment.text,
        }
        for fragment in fragments
    ]


def organ_rows(organ_map: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "organ": organ,
            "status": entry["status"],
            "confidence": entry["confidence"],
            "fragment_count": str(len(entry["fragments"])),
            "suggested_next_action": entry["suggested_next_action"],
        }
        for organ, entry in organ_map.items()
    ]


def _tag_list(tags: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;]+", tags) if part.strip()]


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _duplicate_lines(text: str) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for line in text.splitlines():
        cleaned = re.sub(r"\s+", " ", line.strip().lower())
        if len(cleaned) < 30:
            continue
        if cleaned in seen and cleaned not in dupes:
            dupes.append(line.strip())
        seen.add(cleaned)
    return dupes[:12]


def _looks_like_claim(line: str) -> bool:
    lowered = line.lower()
    return any(term in lowered for term in ["shows", "proves", "demonstrates", "reveals", "is clearly"])


def _has_evidence_marker(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in ["citation", "source", "evidence", "according to", "("])


def _terms(text: str) -> list[str]:
    stopwords = {
        "the", "and", "or", "of", "in", "to", "for", "a", "an", "with", "from",
        "this", "that", "into", "about", "through", "will", "should", "not",
    }
    result: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower()):
        cleaned = word.strip("-'")
        if len(cleaned) < 3 or cleaned in stopwords:
            continue
        _append_unique(result, cleaned)
    return result


def _organ_terms(organ_map: dict[str, dict[str, Any]], organ: str) -> list[str]:
    text = " ".join(fragment.text for fragment in organ_map.get(organ, {}).get("fragments", []))
    return _terms(text)[:10]


def _zotero_openalex_suggestion(terms: list[str], concept_terms: list[str], region_terms: list[str]) -> str:
    candidates = concept_terms[:4] + region_terms[:4] + terms[:6]
    if not candidates:
        return "Add concepts, case, and method fragments before querying Zotero or OpenAlex."
    return " ".join(candidates[:10])
