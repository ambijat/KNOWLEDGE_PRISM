"""Scholar-input schema v0.2 helpers for the Tkinter GUI.

This module is UI/report preparation only. It does not create database tables,
write research-state rows, run retrieval, or promote any input to evidence.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .db_access import ROOT


SCHEMA_VERSION = "0.2"
RECORD_TYPE = "scholar_input_not_evidence"
BANNER = "SCHOLAR INPUT — NOT EVIDENCE"
FLOW_WARNING = (
    "This record may seed a research question or retrieval lens, but it is not "
    "a source and cannot directly enter verification_queue."
)
REPORT_DIR = ROOT / "outputs" / "gui_reports" / "scholar_inputs"

SOURCES = {"android_app", "desktop_manual", "desktop_import"}
STATUSES = {
    "raw_captured",
    "imported_not_evidence",
    "under_review",
    "approved_to_question",
    "rejected_archived",
}
STATUS_FILTER_VALUES = [
    "All",
    "raw_captured",
    "imported_not_evidence",
    "under_review",
    "approved_to_question",
    "rejected_archived",
    "invalid",
    "warning",
]
SOURCE_FILTER_VALUES = [
    "All",
    "android_app",
    "desktop_manual",
    "desktop_import",
    "invalid",
    "missing",
]
FROZEN_ORGANS = {
    "Title",
    "Background",
    "Statement_of_Problem",
    "Research_Gap",
    "Research_Questions",
    "Objectives",
    "Scope",
    "Methodology",
    "Conceptual_Framework",
    "Literature_Clusters",
    "Evidence_Needs",
    "Case_Region_Time_Period",
    "Chapterisation",
    "Supervisor_Questions",
    "Revision_Tasks",
    "Unassigned",
}
ORGAN_FILTER_VALUES = [
    "All",
    "Title",
    "Background",
    "Statement_of_Problem",
    "Research_Gap",
    "Research_Questions",
    "Objectives",
    "Scope",
    "Methodology",
    "Conceptual_Framework",
    "Literature_Clusters",
    "Evidence_Needs",
    "Case_Region_Time_Period",
    "Chapterisation",
    "Supervisor_Questions",
    "Revision_Tasks",
    "Unassigned",
    "invalid",
    "missing",
]
OPTIONAL_FIELDS = [
    "scholar_id",
    "imported_ts",
    "draft_organ",
    "draft_diagnosis",
    "draft_search_plan",
    "supervisor_brief",
    "raw_notes",
    "voice_transcript",
    "tags",
    "confidence",
    "project_title",
    "course_or_context",
    "became_question",
    "became_queue_id",
    "decided_by",
    "decided_ts",
    "rejection_reason",
    "block_no",
]
DISPLAY_FIELDS = [
    "scholar_id",
    "schema_version",
    "source",
    "captured_ts",
    "imported_ts",
    "idea",
    "draft_organ",
    "draft_diagnosis",
    "draft_search_plan",
    "supervisor_brief",
    "tags",
    "confidence",
    "project_title",
    "course_or_context",
    "status",
    "content_sha256",
    "became_question",
    "became_queue_id",
    "block_no",
]


@dataclass(frozen=True)
class ValidationItem:
    level: str
    field: str
    message: str


@dataclass(frozen=True)
class InboxRecord:
    path: Path
    filename: str
    record: dict[str, Any] | None
    validation_items: list[ValidationItem]
    validation_status: str
    load_error: str = ""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_inbox_records(directory: Path = REPORT_DIR) -> list[InboxRecord]:
    """List local scholar-input JSON records from the report directory.

    Generated report-bundle JSON files include ``report_type`` and are skipped so
    the inbox stays focused on scholar-input records and test fixtures.
    """
    directory.mkdir(parents=True, exist_ok=True)
    records: list[InboxRecord] = []
    for path in sorted(directory.glob("*.json")):
        try:
            record = load_json(path)
        except Exception as exc:
            records.append(
                InboxRecord(
                    path=path,
                    filename=path.name,
                    record=None,
                    validation_items=[ValidationItem("invalid", "json", f"Could not parse JSON: {exc}")],
                    validation_status="invalid",
                    load_error=str(exc),
                )
            )
            continue
        if isinstance(record, dict) and "report_type" in record:
            continue
        if not isinstance(record, dict):
            records.append(
                InboxRecord(
                    path=path,
                    filename=path.name,
                    record=None,
                    validation_items=[ValidationItem("invalid", "json", "Top-level JSON value is not an object.")],
                    validation_status="invalid",
                    load_error="Top-level JSON value is not an object.",
                )
            )
            continue
        items = validate_record(record)
        records.append(
            InboxRecord(
                path=path,
                filename=path.name,
                record=record,
                validation_items=items,
                validation_status=validation_status(items),
            )
        )
    return records


def validate_record(record: dict[str, Any]) -> list[ValidationItem]:
    items: list[ValidationItem] = []
    _check_equal(items, record, "schema_version", SCHEMA_VERSION)
    _check_equal(items, record, "record_type", RECORD_TYPE)
    _check_non_empty(items, record, "idea")
    _check_choice(items, record, "source", SOURCES)
    _check_choice(items, record, "status", STATUSES)
    _check_iso8601(items, record, "captured_ts", required=True)
    _check_iso8601(items, record, "imported_ts", required=False)
    _check_organ(items, record)
    _check_hash(items, record)
    for field in OPTIONAL_FIELDS:
        if field not in record:
            items.append(ValidationItem("missing optional field", field, "Optional field not present."))
    if not any(item.level == "invalid" for item in items):
        items.insert(0, ValidationItem("valid", "record", "Required v0.2 checks passed."))
    return items


def is_valid(items: list[ValidationItem]) -> bool:
    return not any(item.level == "invalid" for item in items)


def validation_status(items: list[ValidationItem]) -> str:
    if any(item.level == "invalid" for item in items):
        return "invalid"
    if any(item.level == "warning" for item in items):
        return "warning"
    return "valid"


def inbox_rows(records: list[InboxRecord]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in records:
        record = item.record or {}
        rows.append(
            {
                "filename": item.filename,
                "scholar_id": _cell(record.get("scholar_id")),
                "schema_version": _cell(record.get("schema_version")),
                "source": _cell(record.get("source")),
                "captured_ts": _cell(record.get("captured_ts")),
                "status": _cell(record.get("status")),
                "draft_organ": _cell(record.get("draft_organ")),
                "idea_preview": _short(record.get("idea")),
                "validation_status": item.validation_status,
            }
        )
    return rows


def filter_inbox_records(
    records: list[InboxRecord],
    status_filter: str = "All",
    source_filter: str = "All",
    organ_filter: str = "All",
    search_query: str = "",
) -> list[InboxRecord]:
    return [
        item for item in records
        if _matches_status(item, status_filter)
        and _matches_source(item, source_filter)
        and _matches_organ(item, organ_filter)
        and _matches_search(item, search_query)
    ]


def canonical_content(record: dict[str, Any]) -> str:
    """Canonical content for lightweight UI hash checks.

    The frozen schema describes this as idea + notes. For UI validation we use
    the required idea plus raw notes and voice transcript, preserving order.
    """
    return "\n".join(
        str(record.get(field) or "")
        for field in ["idea", "raw_notes", "voice_transcript"]
    )


def compute_content_sha256(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_content(record).encode("utf-8")).hexdigest()


def question_seed_preview(record: dict[str, Any]) -> dict[str, Any]:
    idea = str(record.get("idea") or "").strip()
    draft_search = str(record.get("draft_search_plan") or "")
    tags = str(record.get("tags") or "")
    supervisor = str(record.get("supervisor_brief") or "")
    organ = str(record.get("draft_organ") or "Unassigned")
    terms = _terms(" ".join([idea, draft_search, tags]))[:12]
    question = _question_from_idea(idea)
    return {
        "banner": BANNER,
        "status": "draft_seed_not_evidence",
        "possible_research_question": question,
        "possible_query_lens_terms": terms,
        "possible_research_organ": organ,
        "possible_supervisor_question": supervisor or "What should this idea become: question, scope note, or search clue?",
        "warning": "This is a draft seed, not evidence.",
        "flow_warning": FLOW_WARNING,
    }


def display_card(record: dict[str, Any]) -> str:
    lines = [
        BANNER,
        FLOW_WARNING,
        "",
        "Not evidence",
        "Not in verification queue",
        "Not a claim",
        "Not ontology",
        "",
    ]
    labels = {
        "draft_organ": "DRAFT — unverified organ assignment",
        "draft_diagnosis": "DRAFT — unverified diagnosis",
        "draft_search_plan": "Suggested keywords — not Recoll lens",
    }
    for field in DISPLAY_FIELDS:
        value = record.get(field)
        if value is None:
            value = ""
        if field in labels:
            lines.append(f"{field}: {value}  [{labels[field]}]")
        else:
            lines.append(f"{field}: {value}")
    return "\n".join(lines)


def validation_rows(items: list[ValidationItem]) -> list[dict[str, str]]:
    return [
        {"level": item.level, "field": item.field, "message": item.message}
        for item in items
    ]


def write_example_fixture() -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "record_type": RECORD_TYPE,
        "_note": "This record is scholar input, not evidence.",
        "schema_version": SCHEMA_VERSION,
        "scholar_id": "KP-SI-EXAMPLE",
        "source": "desktop_manual",
        "captured_ts": "2026-07-09T09:14:00+05:30",
        "imported_ts": "2026-07-09T09:14:00+05:30",
        "idea": "Chapter 3 may need a counter-case that tests whether balance-of-power language still explains Central Asian alignment.",
        "draft_organ": "Evidence_Needs",
        "draft_diagnosis": "Possible foil for a chapter argument.",
        "draft_search_plan": "balance of power, central asia, alignment, hedging",
        "supervisor_brief": "Ask whether this should become a retrieval lens for opposing accounts.",
        "raw_notes": "Keep it as a fair strongest-opponent search, not a claim.",
        "voice_transcript": "",
        "tags": "counter-case,foil",
        "confidence": "hunch",
        "project_title": "Eurasian security imaginaries",
        "course_or_context": "PhD chapter 3",
        "status": "imported_not_evidence",
        "content_sha256": "",
        "became_question": None,
        "became_queue_id": None,
        "decided_by": None,
        "decided_ts": None,
        "rejection_reason": None,
        "block_no": None,
    }
    record["content_sha256"] = compute_content_sha256(record)
    path = REPORT_DIR / "example_scholar_input_v0.2.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _check_equal(items: list[ValidationItem], record: dict[str, Any], field: str, expected: str) -> None:
    actual = record.get(field)
    if actual == expected:
        items.append(ValidationItem("valid", field, f"Value is {expected}."))
    else:
        items.append(ValidationItem("invalid", field, f"Expected {expected!r}; found {actual!r}."))


def _check_non_empty(items: list[ValidationItem], record: dict[str, Any], field: str) -> None:
    if isinstance(record.get(field), str) and record[field].strip():
        items.append(ValidationItem("valid", field, "Non-empty text present."))
    else:
        items.append(ValidationItem("invalid", field, "Required non-empty idea text missing."))


def _check_choice(items: list[ValidationItem], record: dict[str, Any], field: str, allowed: set[str]) -> None:
    actual = record.get(field)
    if actual in allowed:
        items.append(ValidationItem("valid", field, f"Value is allowed: {actual}."))
    else:
        items.append(ValidationItem("invalid", field, f"Expected one of {sorted(allowed)}; found {actual!r}."))


def _check_iso8601(items: list[ValidationItem], record: dict[str, Any], field: str, required: bool) -> None:
    value = record.get(field)
    if value in (None, "") and not required:
        items.append(ValidationItem("warning", field, "Optional timestamp not present yet."))
        return
    if not isinstance(value, str) or not value.strip():
        items.append(ValidationItem("invalid", field, "Required ISO-8601 timestamp missing."))
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        items.append(ValidationItem("invalid", field, f"Timestamp is not valid ISO-8601: {value!r}."))
    else:
        items.append(ValidationItem("valid", field, "Timestamp parses as ISO-8601."))


def _check_organ(items: list[ValidationItem], record: dict[str, Any]) -> None:
    organ = record.get("draft_organ")
    if organ in (None, ""):
        items.append(ValidationItem("valid", "draft_organ", "Empty draft organ is allowed."))
    elif organ in FROZEN_ORGANS:
        items.append(ValidationItem("valid", "draft_organ", f"Frozen organ value: {organ}."))
    else:
        items.append(ValidationItem("invalid", "draft_organ", f"Not in frozen organ vocabulary: {organ!r}."))


def _check_hash(items: list[ValidationItem], record: dict[str, Any]) -> None:
    supplied = record.get("content_sha256")
    if not supplied:
        items.append(ValidationItem("invalid", "content_sha256", "Required content hash missing."))
        return
    if not isinstance(supplied, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", supplied):
        items.append(ValidationItem("warning", "content_sha256", "Hash present but not recomputable hex; hash check pending."))
        return
    recomputed = compute_content_sha256(record)
    if supplied.lower() == recomputed:
        items.append(ValidationItem("valid", "content_sha256", "Hash matches UI canonical content."))
    else:
        items.append(ValidationItem("invalid", "content_sha256", "Hash mismatch against UI canonical content."))


def _terms(text: str) -> list[str]:
    stopwords = {
        "the", "and", "or", "of", "in", "to", "for", "a", "an", "with", "that",
        "this", "whether", "still", "may", "need", "needs", "should", "become",
    }
    result: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower()):
        cleaned = word.strip("-'")
        if len(cleaned) < 3 or cleaned in stopwords:
            continue
        if cleaned not in result:
            result.append(cleaned)
    return result


def _question_from_idea(idea: str) -> str:
    cleaned = " ".join(idea.split())
    if not cleaned:
        return "What research question should this scholar input seed?"
    if cleaned.endswith("?"):
        return cleaned
    return f"How should the project investigate this idea: {cleaned[:180]}?"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _short(value: Any, limit: int = 90) -> str:
    text = _cell(value).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _matches_status(item: InboxRecord, selected: str) -> bool:
    if selected == "All":
        return True
    if selected in {"invalid", "warning"}:
        return item.validation_status == selected
    if item.record is None:
        return False
    return item.record.get("status") == selected


def _matches_source(item: InboxRecord, selected: str) -> bool:
    if selected == "All":
        return True
    if item.record is None:
        return selected == "invalid"
    value = item.record.get("source")
    if value in (None, ""):
        return selected == "missing"
    if value not in SOURCES:
        return selected == "invalid"
    return value == selected


def _matches_organ(item: InboxRecord, selected: str) -> bool:
    if selected == "All":
        return True
    if item.record is None:
        return selected == "invalid"
    value = item.record.get("draft_organ")
    if value in (None, ""):
        return selected == "missing"
    if value not in FROZEN_ORGANS:
        return selected == "invalid"
    return value == selected


def _matches_search(item: InboxRecord, query: str) -> bool:
    needle = " ".join(query.lower().split())
    if not needle:
        return True
    record = item.record or {}
    haystack_values = [
        item.filename,
        record.get("scholar_id"),
        record.get("idea"),
        record.get("tags"),
        record.get("draft_organ"),
        record.get("source"),
        record.get("status"),
        record.get("project_title"),
        record.get("course_or_context"),
    ]
    haystack = " ".join(_cell(value).lower() for value in haystack_values)
    return needle in haystack
