#!/usr/bin/env python3
"""Prepare bridge-concept verification batches.

This replaces the old "first 50 checklist" helper with a batch-oriented
preparation step. It joins the 392 bridge-concept hypotheses to the master
corpus, checks whether the source files are currently accessible, writes a
machine-readable manifest, and emits Markdown review reports.

No text is sampled here and no claim is promoted. This is still access-level
work only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "data/verification/BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv"
MASTER = ROOT / "data/processed/MASTER_CORPUS_REGISTER_PRELIMINARY.csv"

MANIFEST = ROOT / "data/verification/BRIDGE_BATCH_MANIFEST.csv"
ACCESS_REPORT = ROOT / "outputs/reports/BRIDGE_QUEUE_ACCESS_REPORT.md"
PILOT_REPORT = ROOT / "outputs/reports/BRIDGE_VERIFICATION_PILOT_20.md"
COMPAT_SAMPLE_50 = ROOT / "outputs/reports/BRIDGE_VERIFICATION_SAMPLE_50.md"

DEFAULT_BATCH_ID = "pilot_balanced_20"
DEFAULT_PILOT_SIZE = 20
PILOT_STRATA = [
    ("International Relations Theory", "theory", 6),
    ("International Relations Theory", "mixed", 2),
    ("International Relations Theory", "method", 1),
    ("Social Science Theories and Geography", "theory", 3),
    ("semiotics", "", 3),
    ("Statistical Analysis and Research Methods", "method", 2),
    ("Statistical Analysis and Research Methods", "empirical", 2),
    ("cognitive_philiosophy", "method", 1),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y"}


def int_or_zero(value: str | None) -> int:
    try:
        return int(float((value or "").strip()))
    except ValueError:
        return 0


def build_master_index(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_filename: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        filename = (row.get("filename") or "").strip()
        if filename:
            by_filename[filename].append(row)
    return by_filename


def choose_master_match(matches: list[dict[str, str]]) -> dict[str, str] | None:
    if not matches:
        return None

    def score(row: dict[str, str]) -> tuple[int, int, int, str]:
        path = row.get("path_norm") or ""
        exists = 1 if path and Path(path).exists() else 0
        source_both = 1 if truthy(row.get("source_solemon_crawl")) and truthy(row.get("source_recoll_manifest")) else 0
        size = int_or_zero(row.get("size_bytes"))
        return (exists, source_both, size, path)

    return sorted(matches, key=score, reverse=True)[0]


def access_status(path_value: str, ext: str) -> str:
    if not path_value:
        return "unmapped"
    path = Path(path_value)
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "not_file"
    if path.stat().st_size == 0:
        return "empty_file"
    if ext.lower() != ".pdf":
        return "present_non_pdf"
    return "present_pdf"


def make_manifest(bridge_rows: list[dict[str, str]], master_rows: list[dict[str, str]], batch_id: str) -> list[dict[str, str]]:
    master_index = build_master_index(master_rows)
    manifest: list[dict[str, str]] = []

    for idx, bridge in enumerate(bridge_rows, start=1):
        matches = master_index.get((bridge.get("file") or "").strip(), [])
        match = choose_master_match(matches)
        ext = (match or {}).get("ext", "")
        path_norm = (match or {}).get("path_norm", "")
        status = access_status(path_norm, ext)
        duplicate_group_size = (match or {}).get("duplicate_group_size", "")
        duplicate_risk = "yes" if int_or_zero(duplicate_group_size) > 1 or len(matches) > 1 else "no"

        manifest.append({
            "bridge_row_id": f"BRIDGE-{idx:04d}",
            "batch_id": "backlog",
            "pilot_selected": "False",
            "folder": bridge.get("folder", ""),
            "file": bridge.get("file", ""),
            "title": bridge.get("title", ""),
            "axis": bridge.get("axis", ""),
            "thesis": bridge.get("thesis", ""),
            "concepts": bridge.get("concepts", ""),
            "bridge_claim_status": bridge.get("bridge_claim_status", ""),
            "required_next_evidence": bridge.get("required_next_evidence", ""),
            "claim_use_allowed": bridge.get("claim_use_allowed", ""),
            "corpus_item_id": (match or {}).get("corpus_item_id", ""),
            "path_norm": path_norm,
            "ext": ext,
            "size_bytes": (match or {}).get("size_bytes", ""),
            "dedupe_key": (match or {}).get("dedupe_key", ""),
            "duplicate_group_size": duplicate_group_size,
            "filename_match_count": str(len(matches)),
            "duplicate_risk": duplicate_risk,
            "corpus_class_preliminary": (match or {}).get("corpus_class_preliminary", ""),
            "current_evidence_grade": (match or {}).get("evidence_grade", ""),
            "current_verification_status": (match or {}).get("verification_status", ""),
            "access_status": status,
            "sample_status": "not_sampled",
            "verdict_status": "not_started",
            "review_status": "not_started",
            "ledger_block_id": "",
        })

    selected_ids = select_pilot_ids(manifest, batch_id)
    for row in manifest:
        if row["bridge_row_id"] in selected_ids:
            row["batch_id"] = batch_id
            row["pilot_selected"] = "True"

    return manifest


def select_pilot_ids(manifest: list[dict[str, str]], batch_id: str) -> set[str]:
    """Deterministically select a pilot from load-bearing folders.

    The pilot is not a random sample. It intentionally exercises the project's
    main methodological pressure points: IR theory, general social theory,
    semiotics, research methods, and a small empirical slice.
    """
    selected: list[str] = []
    selected_set: set[str] = set()

    for folder, axis, quota in PILOT_STRATA:
        candidates = [
            row for row in manifest
            if row["bridge_row_id"] not in selected_set
            and row.get("folder") == folder
            and (not axis or row.get("axis") == axis)
        ]
        candidates = sorted(candidates, key=lambda r: r["bridge_row_id"])
        for row in candidates[:quota]:
            selected.append(row["bridge_row_id"])
            selected_set.add(row["bridge_row_id"])

    if len(selected) < DEFAULT_PILOT_SIZE:
        remaining = [
            row for row in sorted(manifest, key=lambda r: (r["folder"], r["axis"], r["bridge_row_id"]))
            if row["bridge_row_id"] not in selected_set
        ]
        selected.extend(row["bridge_row_id"] for row in remaining[: DEFAULT_PILOT_SIZE - len(selected)])

    return set(selected[:DEFAULT_PILOT_SIZE])


def write_manifest(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def md_escape(value: str) -> str:
    return (value or "").replace("\n", " ").strip()


def write_access_report(rows: list[dict[str, str]], path: Path, batch_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    access_counts = Counter(row["access_status"] for row in rows)
    axis_counts = Counter(row["axis"] for row in rows)
    pilot_rows = [row for row in rows if row["pilot_selected"] == "True"]
    pilot_axis_counts = Counter(row["axis"] for row in pilot_rows)
    duplicate_risk_count = sum(1 for row in rows if row["duplicate_risk"] == "yes")
    unmapped_count = sum(1 for row in rows if not row["corpus_item_id"])
    today = dt.date.today().isoformat()

    lines = [
        "# Bridge Queue Access Report",
        "",
        f"Generated: {today}",
        "",
        "This report is access-level only. It maps provisional bridge-concept",
        "claims to corpus files and checks whether the files are currently",
        "reachable. It does not sample text or promote any claim.",
        "",
        "## Summary",
        "",
        f"- Bridge rows: {len(rows)}",
        f"- Mapped to master corpus: {len(rows) - unmapped_count}",
        f"- Unmapped rows: {unmapped_count}",
        f"- Duplicate-risk rows: {duplicate_risk_count}",
        f"- Pilot batch: `{batch_id}`",
        f"- Pilot rows selected: {len(pilot_rows)}",
        "",
        "## Access Status",
        "",
    ]
    for status, count in sorted(access_counts.items()):
        lines.append(f"- {status}: {count}")

    lines += ["", "## Axis Counts", ""]
    for axis, count in sorted(axis_counts.items()):
        lines.append(f"- {axis}: {count}")

    lines += ["", "## Pilot Axis Counts", ""]
    for axis, count in sorted(pilot_axis_counts.items()):
        lines.append(f"- {axis}: {count}")

    lines += [
        "",
        "## Pilot Items",
        "",
        "| ID | Axis | Access | Title | File |",
        "|---|---|---|---|---|",
    ]
    for row in pilot_rows:
        lines.append(
            f"| {row['bridge_row_id']} | {row['axis']} | {row['access_status']} | "
            f"{md_escape(row['title'])} | `{md_escape(row['file'])}` |"
        )

    lines += [
        "",
        "## Next Step",
        "",
        "Run PDF sample extraction only for rows where `pilot_selected=True` and",
        "`access_status=present_pdf`. Keep any unreadable result as a blocked",
        "verification state, not as absent evidence.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def checklist_lines(rows: list[dict[str, str]], title: str) -> list[str]:
    lines = [
        f"# {title}",
        "",
        "Each item below is provisional. Mark the evidence actually seen before",
        "using it in scholarly argument.",
        "",
    ]
    for i, row in enumerate(rows, 1):
        lines += [
            f"## {i}. {md_escape(row.get('title') or row.get('file') or row['bridge_row_id'])}",
            "",
            f"- Bridge row: `{row['bridge_row_id']}`",
            f"- Batch: `{row['batch_id']}`",
            f"- Folder: `{md_escape(row.get('folder', ''))}`",
            f"- File: `{md_escape(row.get('file', ''))}`",
            f"- Corpus item: `{row.get('corpus_item_id', '')}`",
            f"- Access status: `{row.get('access_status', '')}`",
            f"- Duplicate risk: `{row.get('duplicate_risk', '')}`",
            f"- Provisional axis: `{row.get('axis', '')}`",
            f"- Provisional thesis: {md_escape(row.get('thesis', ''))}",
            f"- Provisional concepts: {md_escape(row.get('concepts', ''))}",
            "",
            "**Verification checklist**",
            "",
            "- [ ] File located",
            "- [ ] Text extraction works",
            "- [ ] Front matter / abstract / TOC checked",
            "- [ ] Introduction or chapter sample checked",
            "- [ ] Concept probes checked",
            "- [ ] Thesis verdict assigned: SUPPORTED / PARTIAL / CONTRADICTED / ABSENT / UNREADABLE",
            "- [ ] Key concepts tagged: seen_in_text / variant_seen / not_found",
            "- [ ] Evidence locator recorded",
            "- [ ] Claim event or review route recorded",
            "",
        ]
    return lines


def write_checklists(rows: list[dict[str, str]]) -> None:
    PILOT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    pilot_rows = [row for row in rows if row["pilot_selected"] == "True"]
    pilot_rows = sorted(pilot_rows, key=lambda r: (r["axis"], r["folder"], r["file"], r["bridge_row_id"]))
    PILOT_REPORT.write_text(
        "\n".join(checklist_lines(pilot_rows, "Bridge Verification Pilot 20")),
        encoding="utf-8",
    )

    first_50 = rows[:50]
    COMPAT_SAMPLE_50.write_text(
        "\n".join(checklist_lines(first_50, "Bridge Concepts Verification Sample 50")),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare bridge verification batch manifests and reports.")
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID, help="Batch id assigned to selected pilot rows.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bridge_rows = read_csv(BRIDGE)
    master_rows = read_csv(MASTER)
    rows = make_manifest(bridge_rows, master_rows, args.batch_id)
    write_manifest(rows, MANIFEST)
    write_access_report(rows, ACCESS_REPORT, args.batch_id)
    write_checklists(rows)

    access_counts = Counter(row["access_status"] for row in rows)
    pilot_count = sum(1 for row in rows if row["pilot_selected"] == "True")
    print(f"Wrote {len(rows)} rows to {MANIFEST}")
    print(f"Wrote access report to {ACCESS_REPORT}")
    print(f"Wrote pilot checklist to {PILOT_REPORT}")
    print(f"Wrote compatibility checklist to {COMPAT_SAMPLE_50}")
    print(f"Pilot rows selected: {pilot_count}")
    print("Access status:", dict(sorted(access_counts.items())))


if __name__ == "__main__":
    main()
