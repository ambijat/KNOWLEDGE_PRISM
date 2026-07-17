"""Local reports for Scholar Input Inbox v0.3."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from . import scholar_input_schema as schema


def export_report_bundle(
    record: dict[str, Any],
    validation_items: list[schema.ValidationItem],
    seed_preview: dict[str, Any],
) -> list[Path]:
    schema.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = _safe_id(record)
    payloads = {
        "validation-report": {
            "report_type": "scholar_input_validation_report",
            "banner": schema.BANNER,
            "flow_warning": schema.FLOW_WARNING,
            "record": record,
            "validation": schema.validation_rows(validation_items),
        },
        "question-seed-preview": {
            "report_type": "research_question_seed_preview",
            "banner": schema.BANNER,
            "flow_warning": schema.FLOW_WARNING,
            "seed_preview": seed_preview,
        },
        "supervisor-note-summary": {
            "report_type": "supervisor_note_summary",
            "banner": schema.BANNER,
            "flow_warning": schema.FLOW_WARNING,
            "scholar_id": record.get("scholar_id"),
            "supervisor_brief": record.get("supervisor_brief") or "",
            "idea": record.get("idea") or "",
            "status": record.get("status"),
        },
    }
    paths: list[Path] = []
    for name, payload in payloads.items():
        json_path = schema.REPORT_DIR / f"{stamp}-{base}-{name}.json"
        md_path = schema.REPORT_DIR / f"{stamp}-{base}-{name}.md"
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(_markdown(payload), encoding="utf-8")
        paths.extend([json_path, md_path])
    return paths


def supervisor_note(record: dict[str, Any], seed_preview: dict[str, Any] | None = None) -> str:
    lines = [
        schema.BANNER,
        schema.FLOW_WARNING,
        "",
        f"Scholar ID: {record.get('scholar_id') or ''}",
        f"Status: {record.get('status') or ''}",
        f"Draft organ: {record.get('draft_organ') or ''} [DRAFT — unverified organ assignment]",
        "",
        "Idea:",
        str(record.get("idea") or ""),
        "",
        "Supervisor brief:",
        str(record.get("supervisor_brief") or ""),
    ]
    if seed_preview:
        lines.extend([
            "",
            "Possible research question seed:",
            str(seed_preview.get("possible_research_question") or ""),
        ])
    return "\n".join(lines)


def _markdown(payload: dict[str, Any]) -> str:
    title = str(payload.get("report_type", "scholar_input_report")).replace("_", " ").title()
    lines = [
        f"# {title}",
        "",
        schema.BANNER,
        "",
        schema.FLOW_WARNING,
        "",
    ]
    for key, value in payload.items():
        lines.append(f"## {key.replace('_', ' ').title()}")
        if isinstance(value, (dict, list)):
            lines.append("```json")
            lines.append(json.dumps(value, indent=2, ensure_ascii=False))
            lines.append("```")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)


def _safe_id(record: dict[str, Any]) -> str:
    value = str(record.get("scholar_id") or "scholar-input")
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower() or "scholar-input"
