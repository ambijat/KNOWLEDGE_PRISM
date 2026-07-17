"""Local report writing for the Knowledge Prism operational GUI."""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from .db_access import ROOT


REPORT_DIR = ROOT / "outputs" / "gui_reports"
DRAFT_DIR = REPORT_DIR / "drafts"


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_research_input(data: dict[str, Any], fmt: str = "markdown") -> Path:
    payload = {
        "record_type": "draft_research_input",
        "status": "draft_only_not_evidence",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "non_promotion_statement": (
            "This draft does not create evidence claims, queue rows, dispositions, "
            "functional roles, or ontology changes."
        ),
        "research_input": data,
    }
    return _write_payload("research_input", payload, fmt, DRAFT_DIR)


def write_query_lens(data: dict[str, Any], fmt: str = "markdown") -> Path:
    payload = {
        "record_type": "draft_query_lens",
        "status": "planning_only_not_retrieval",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "non_promotion_statement": (
            "This query lens does not run Recoll, create evidence, modify the queue, "
            "or promote ontology."
        ),
        "query_lens": data,
    }
    return _write_payload("query_lens", payload, fmt, REPORT_DIR)


def write_project_state(data: dict[str, Any], fmt: str = "markdown") -> Path:
    payload = {
        "record_type": "project_state_summary",
        "status": "read_only_snapshot",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_state": data,
    }
    return _write_payload("project_state", payload, fmt, REPORT_DIR)


def _write_payload(name: str, payload: dict[str, Any], fmt: str, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = _slug(name)
    fmt = fmt.lower()
    if fmt == "json":
        path = directory / f"{timestamp()}-{safe_name}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path
    if fmt == "csv":
        path = directory / f"{timestamp()}-{safe_name}.csv"
        _write_csv(path, payload)
        return path
    path = directory / f"{timestamp()}-{safe_name}.md"
    path.write_text(_markdown(payload), encoding="utf-8")
    return path


def _write_csv(path: Path, payload: dict[str, Any]) -> None:
    flat = _flatten(payload)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        writer.writerows(flat.items())


def _markdown(payload: dict[str, Any]) -> str:
    lines = [f"# {payload.get('record_type', 'Knowledge Prism report').replace('_', ' ').title()}", ""]
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


def _flatten(data: Any, prefix: str = "") -> dict[str, str]:
    result: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(value, child))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            result.update(_flatten(value, f"{prefix}.{index}"))
    else:
        result[prefix] = "" if data is None else str(data)
    return result


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
