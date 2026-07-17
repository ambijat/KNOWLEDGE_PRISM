"""Read-only scholar-input access and safe invocation of the sealed importer."""
from __future__ import annotations

import re
import os
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import db_access


IMPORTER = db_access.ROOT / "scripts" / "06_import_scholar_input.py"
CONSISTENCY_VALIDATOR = db_access.ROOT / "scripts" / "00b_validate_db_consistency.py"
TRANSITION = db_access.ROOT / "scripts" / "07_transition_scholar_input.py"


def active_db_path() -> Path:
    """Return the configured DB, allowing explicit disposable GUI acceptance runs."""
    return Path(os.environ.get("KNOWLEDGE_PRISM_DB_PATH", str(db_access.DB_PATH))).resolve()


def active_validator_path() -> Path:
    return Path(os.environ.get("KNOWLEDGE_PRISM_CONSISTENCY_VALIDATOR", str(CONSISTENCY_VALIDATOR))).resolve()


@dataclass(frozen=True)
class ImportReport:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    counts: dict[str, int] = field(default_factory=dict)
    assigned_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    duplicates: tuple[str, ...] = ()
    transaction_outcome: str = "not reported"

    @property
    def can_commit(self) -> bool:
        return (
            self.exit_code == 0
            and self.counts.get("records eligible", 0) > 0
            and self.counts.get("records invalid", 0) == 0
        )


@dataclass(frozen=True)
class TransitionResult:
    command: tuple[str, ...]
    exit_code: int
    data: dict[str, Any]
    stdout: str
    stderr: str

    @property
    def accepted(self) -> bool:
        return self.exit_code == 0 and self.data.get("status") in {"ok", "already_approved"}

    @property
    def refused(self) -> bool:
        return self.exit_code == 2


def taxonomy_statuses(db_path: Path | None = None) -> list[str]:
    db_path = db_path or active_db_path()
    with _readonly_connection(db_path) as con:
        return [row[0] for row in con.execute(
            "SELECT status FROM scholar_input_status_taxonomy ORDER BY status"
        )]


def persistent_rows(db_path: Path | None = None) -> list[dict[str, Any]]:
    db_path = db_path or active_db_path()
    with _readonly_connection(db_path) as con:
        rows = con.execute(
            """SELECT scholar_id, captured_ts, imported_ts, source, draft_organ,
                      status, idea, raw_notes, tags, confidence, project_title,
                      course_or_context, content_sha256, became_question,
                      decided_by, decided_ts, rejection_reason
               FROM scholar_input ORDER BY imported_ts DESC, scholar_id DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def research_question(question_id: str, db_path: Path | None = None) -> dict[str, Any] | None:
    db_path = db_path or active_db_path()
    with _readonly_connection(db_path) as con:
        row = con.execute(
            """SELECT question_id, lens_type, question_text, status,
                      origin_scholar_id, created_ts, created_by
               FROM research_question WHERE question_id=?""", (question_id,),
        ).fetchone()
    return dict(row) if row else None


def filter_persistent_rows(
    rows: list[dict[str, Any]], status: str = "All", source: str = "All",
    organ: str = "All", search: str = "",
) -> list[dict[str, Any]]:
    needle = " ".join(search.lower().split())
    result = []
    for row in rows:
        if status != "All" and row.get("status") != status:
            continue
        if source != "All" and row.get("source") != source:
            continue
        if organ != "All" and (row.get("draft_organ") or "") != organ:
            continue
        if needle and needle not in " ".join(str(value or "") for value in row.values()).lower():
            continue
        result.append(row)
    return result


def run_importer(input_path: Path, db_path: Path | None = None, commit: bool = False) -> ImportReport:
    db_path = db_path or active_db_path()
    command = [sys.executable, str(IMPORTER), "--input", str(input_path), "--db", str(db_path)]
    if commit:
        command.append("--commit")
    completed = subprocess.run(command, cwd=db_access.ROOT, text=True, capture_output=True, shell=False)
    return parse_import_report(tuple(command), completed.returncode, completed.stdout, completed.stderr)


def run_transition(
    scholar_id: str, action: str, decided_by: str, db_path: Path | None = None,
    question_text: str = "", lens_type: str = "research_question",
    rejection_reason: str = "", commit: bool = False,
) -> TransitionResult:
    db_path = db_path or active_db_path()
    command = [
        sys.executable, str(TRANSITION), "--db", str(db_path),
        "--scholar-id", scholar_id, "--action", action, "--decided-by", decided_by,
    ]
    if action == "approve-to-question":
        command.extend(["--question-text", question_text, "--lens-type", lens_type])
    elif action == "reject":
        command.extend(["--rejection-reason", rejection_reason])
    if commit:
        command.append("--commit")
    completed = subprocess.run(command, cwd=db_access.ROOT, text=True, capture_output=True, shell=False)
    data: dict[str, Any]
    try:
        parsed = json.loads(completed.stdout)
        data = parsed if isinstance(parsed, dict) else {"validation_error": "backend JSON was not an object"}
    except json.JSONDecodeError:
        data = {
            "status": "refused" if completed.returncode == 2 else "error",
            "refusal_reason" if completed.returncode == 2 else "validation_error": completed.stdout.strip(),
        }
    return TransitionResult(tuple(command), completed.returncode, data, completed.stdout, completed.stderr)


def readable_transition_result(result: TransitionResult) -> str:
    data = result.data
    lines = [
        f"operation: {data.get('action', 'transition')}",
        f"prior status: {data.get('from', 'not reported')}",
        f"proposed/final status: {data.get('to', data.get('status', 'not reported'))}",
        f"committed: {data.get('committed', False)}",
        f"question ID: {data.get('question_id', '')}",
        f"refusal reason: {data.get('refusal_reason', '')}",
        f"validation error: {data.get('validation_error', '')}",
        f"transaction result: {'COMMITTED' if data.get('committed') else 'NO WRITE'}",
    ]
    if result.stderr.strip():
        lines.append("backend error: " + result.stderr.strip())
    return "\n".join(lines)


def run_consistency_validator(db_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    db_path = db_path or active_db_path()
    validator = active_validator_path()
    if db_path.resolve() != db_access.DB_PATH.resolve() and validator == CONSISTENCY_VALIDATOR.resolve():
        raise ValueError("disposable DB requires KNOWLEDGE_PRISM_CONSISTENCY_VALIDATOR in an isolated layout")
    return subprocess.run(
        [sys.executable, str(validator)], cwd=validator.parent.parent,
        text=True, capture_output=True, shell=False,
    )


def parse_import_report(command: tuple[str, ...], exit_code: int, stdout: str, stderr: str) -> ImportReport:
    labels = {
        "files discovered": "files discovered",
        "records discovered": "records discovered",
        "records valid": "records valid",
        "records invalid": "records invalid",
        "records duplicate": "records duplicate",
        "records eligible for insertion": "records eligible",
        "records inserted": "records inserted",
        "records skipped as duplicates": "records duplicate",
    }
    counts: dict[str, int] = {}
    for line in stdout.splitlines():
        match = re.match(r"^([^:]+):\s*(\d+)\s*$", line.strip())
        if match and match.group(1).lower() in labels:
            counts[labels[match.group(1).lower()]] = int(match.group(2))
    ids = tuple(dict.fromkeys(re.findall(r"\bKP-SI-\d{6}\b", stdout)))
    errors = tuple(line.strip() for line in _section(stdout, "validation errors:", ()))
    duplicates = tuple(
        f"duplicate_skipped: {line.strip()}"
        for line in _section(stdout, "duplicates (skipped):", ("validation errors:",))
    )
    if "transaction result: COMMITTED" in stdout:
        outcome = "COMMITTED"
    elif "rolled back" in stdout.lower():
        outcome = "ROLLED BACK"
    elif "no database changes" in stdout or "no rows written" in stdout:
        outcome = "NO WRITE"
    else:
        outcome = "not reported"
    return ImportReport(command, exit_code, stdout, stderr, counts, ids, errors, duplicates, outcome)


def readable_report(report: ImportReport) -> str:
    lines = ["Backend importer report"]
    for label in (
        "files discovered", "records discovered", "records valid", "records invalid",
        "records duplicate", "records eligible", "records inserted",
    ):
        lines.append(f"{label}: {report.counts.get(label, 0)}")
    lines.append(f"transaction outcome: {report.transaction_outcome}")
    if report.assigned_ids:
        lines.append("assigned scholar IDs: " + ", ".join(report.assigned_ids))
    if report.duplicates:
        lines.extend(report.duplicates)
    if report.errors:
        lines.append("validation errors:")
        lines.extend(f"  {error}" for error in report.errors)
    if report.stderr.strip():
        lines.append("backend error: " + report.stderr.strip())
    return "\n".join(lines)


def _readonly_connection(path: Path):
    import sqlite3
    con = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _section(text: str, heading: str, end_headings: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip().lower() == heading) + 1
    except StopIteration:
        return []
    result = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped or stripped.lower() in end_headings or not line.startswith(" "):
            break
        result.append(stripped)
    return result
