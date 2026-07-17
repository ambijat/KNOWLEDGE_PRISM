#!/usr/bin/env python3
"""Generate the contract-v1.0 Knowledge Prism Obsidian vertical slice.

This tool consumes a projection package. It never reads or writes the project
database. Generated regions may be refreshed; researcher regions are preserved
byte-for-byte. Marker conflicts produce reports and leave notes untouched.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


GEN_START = "<!-- KP:GENERATED:START -->"
GEN_END = "<!-- KP:GENERATED:END -->"
RES_START = "<!-- RESEARCHER:NOTES:START -->"
RES_END = "<!-- RESEARCHER:NOTES:END -->"
NOTICE = (
    "This page is a generated Knowledge Prism projection of non-canonical "
    "research material. It is intended for navigation, inspection and "
    "synthesis and does not constitute accepted evidence or canonical knowledge."
)
DIRS = {
    "concept": "01_concepts",
    "entity": "02_entities",
    "source": "03_sources",
    "claim": "06_arguments",
}
VAULT_DIRS = [
    "00_dashboard", "01_concepts", "02_entities", "03_sources", "04_topics",
    "05_projects", "06_arguments", "07_questions", "08_canvases",
    "09_synthesis", "10_teaching", "proposals/inbox", "proposals/accepted",
    "proposals/revised", "proposals/rejected", "proposals/receipts", "templates",
    "99_sync_conflicts", "records",
]
PREDICATES = {
    "supports", "contradicts", "defines", "mentions", "causes", "enables",
    "constrains", "located_in", "part_of", "instrument_of", "associated_with",
    "precedes", "responds_to", "fuses_with",
}
ID_RE = re.compile(r"^(SRC|PAS|CON|ENT|CLM|REL|PROP)-[0-9]{6}$")


@dataclass
class PlannedNote:
    record: dict[str, Any]
    destination: Path
    content: str
    action: str
    conflict: str | None = None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:72] or "untitled"


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def note_filename(record: dict[str, Any]) -> str:
    return f"{record['record_id']} {slug(record['title'])}.md"


def note_relative_path(record: dict[str, Any]) -> Path:
    return Path(DIRS[record["record_type"]]) / note_filename(record)


def index_by_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["record_id"]: record for record in records}


def generated_body(record: dict[str, Any], records: dict[str, dict[str, Any]]) -> str:
    status = record["status"]
    origin = record["provenance"]["origin_table"]
    lines = [
        "---",
        f"record_id: {record['record_id']}",
        f"record_type: {record['record_type']}",
        f"status: {status}",
        "canonical: false" if status != "canonical" else "canonical: true",
        f"title: {yaml_string(record['title'])}",
        f"projection_version: {record['projection_version']}",
        f"last_synchronisation: {yaml_string(record['sync']['projection_built_ts'])}",
        "---",
        "",
        f"# {record['title']}",
        "",
        f"> [!warning] {status.replace('_', ' ').title()} — projection status",
        f"> {NOTICE}",
        "",
        f"- **Knowledge Prism stable ID:** `{record['record_id']}`",
        f"- **Record type:** `{record['record_type']}`",
        f"- **Projected status:** `{status}`",
        f"- **Canonical:** `{'yes' if status == 'canonical' else 'no'}`",
        f"- **Backend origin:** `{origin}`",
        f"- **Reviewed:** `{'yes' if record['provenance']['reviewed'] else 'no'}`",
        f"- **Review date:** `{record['provenance']['review_date'] or 'not reviewed'}`",
        f"- **Ledger block:** `{record['provenance']['block_no'] if record['provenance']['block_no'] is not None else 'none'}`",
        f"- **Projection built:** `{record['sync']['projection_built_ts']}`",
        "",
        "## Backend-projected material",
        "",
    ]
    for label, key in (("Definition", "definition"), ("Summary", "summary"), ("Detail", "detail")):
        if record.get(key):
            lines.extend([f"**{label}.** {record[key]}", ""])
    if record.get("layer") is not None:
        lines.extend([f"**Layer.** `{record['layer']}`", ""])
    if record.get("evidence_grade") is not None:
        lines.extend([f"**Evidence grade.** `{record['evidence_grade']}`", ""])
    lines.extend(["## Source references", ""])
    if record["source_ids"]:
        for source_id in record["source_ids"]:
            target = records.get(source_id)
            link = Path("..") / note_relative_path(target) if target else Path(source_id)
            lines.append(f"- [[{link.as_posix()[:-3]}|{source_id}]]")
    else:
        lines.append("- None supplied by the projection package.")
    lines.extend(["", "## Typed relationships", ""])
    if record["relationships"]:
        for relationship in record["relationships"]:
            target = records.get(relationship["target_id"])
            link = Path("..") / note_relative_path(target) if target else Path(relationship["target_id"])
            lines.append(
                f"- `{relationship['predicate']}` → "
                f"[[{link.as_posix()[:-3]}|{relationship['target_title']}]] "
                f"(`{relationship['relationship_id']}`, status `{relationship['status']}`)"
            )
    else:
        lines.append("- None supplied by the projection package.")
    return "\n".join(lines).rstrip()


def researcher_block(text: str) -> str | None:
    span = marker_span(text, RES_START, RES_END)
    return None if isinstance(span, str) else text[span[0]:span[1]]


def fresh_note(body: str, preserved: str | None = None) -> str:
    block = preserved or (
        f"{RES_START}\n## Researcher Notes\n\n"
        "Write interpretation here. This region is preserved verbatim across synchronisations.\n"
        f"{RES_END}"
    )
    return f"{GEN_START}\n{body}\n{GEN_END}\n\n{block}\n"


def marker_span(text: str, start: str, end: str) -> tuple[int, int] | str:
    starts = [m.start() for m in re.finditer(re.escape(start), text)]
    ends = [m.start() for m in re.finditer(re.escape(end), text)]
    if len(starts) == 0 or len(ends) == 0:
        return f"missing marker pair ({start} / {end})"
    if len(starts) > 1 or len(ends) > 1:
        return f"duplicated marker pair ({start} / {end})"
    if ends[0] < starts[0]:
        return f"END before START ({start} / {end})"
    return starts[0], ends[0] + len(end)


def merge_note(existing: str, body: str) -> tuple[str | None, str | None]:
    generated = marker_span(existing, GEN_START, GEN_END)
    researcher = marker_span(existing, RES_START, RES_END)
    if isinstance(generated, str):
        return None, generated
    if isinstance(researcher, str):
        return None, researcher
    if not generated[1] <= researcher[0]:
        return None, "generated and researcher regions interleave or are out of order"
    preserved = existing[researcher[0]:researcher[1]]
    return f"{GEN_START}\n{body}\n{GEN_END}\n\n{preserved}\n", None


def read_package(package: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = load_json(package / "export_manifest.json")
    records = [load_json(package / item["file"]) for item in manifest["records"]]
    return manifest, records


def plan_notes(package: Path, vault: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[PlannedNote]]:
    manifest, records = read_package(package)
    lookup = index_by_id(records)
    plan: list[PlannedNote] = []
    for record in records:
        destination = vault / note_relative_path(record)
        body = generated_body(record, lookup)
        if not destination.exists():
            fixture_notes = sorted((package / "notes").glob(f"{record['record_id']} *.md"))
            preserved = None
            if fixture_notes:
                preserved = researcher_block(fixture_notes[0].read_text(encoding="utf-8"))
            plan.append(PlannedNote(record, destination, fresh_note(body, preserved), "create"))
            continue
        merged, conflict = merge_note(destination.read_text(encoding="utf-8"), body)
        plan.append(PlannedNote(record, destination, merged or "", "conflict" if conflict else "update", conflict))
    return manifest, records, plan


def render_index(title: str, records: list[dict[str, Any]], vault: Path) -> str:
    lines = [f"# {title}", "", f"> {NOTICE}", ""]
    for record in records:
        rel = note_relative_path(record)
        lines.append(f"- [[../{rel.as_posix()[:-3]}|{record['title']}]] — `{record['record_id']}` · **{record['status']}**")
    if not records:
        lines.append("- No records in the export manifest.")
    return "\n".join(lines) + "\n"


def render_dashboard(manifest: dict[str, Any], records: list[dict[str, Any]], proposal_count: int, receipt_count: int) -> str:
    counts = manifest["counts"]
    return f"""# Knowledge Prism Obsidian Dashboard

> [!warning] Projection, not canonical knowledge
> {NOTICE}

## Synchronisation

- **Last export time:** `{manifest['generated_ts']}`
- **Projection version:** `{manifest['projection_version']}`
- **Manifest version:** `{manifest['manifest_version']}`
- **Source chain reported valid:** `{str(manifest['source_db']['chain_ok']).lower()}`
- **Pending proposals in this vault:** `{proposal_count}`
- **Decision receipts in this vault:** `{receipt_count}`

## Manifest counts

- Concepts: **{counts['concept']}**
- Entities: **{counts['entity']}**
- Sources: **{counts['source']}**
- Claims: **{counts['claim']}**
- Canonical relationships: **0** (fixture relationships retain their projected statuses)
- Exported relationships: **{counts['relationship']}**

## Navigate

- [[Concept Index]]
- [[Entity Index]]
- [[Source Index]]
- [[Argument Index]]
- [[Recent Updates]]
- [[Relationship Summary]]
- [[Pending Proposals]]
- [[Synchronisation Conflicts]]
- [[../08_canvases/Knowledge Prism Vertical Slice.canvas|Knowledge Prism Vertical Slice Canvas]]
- [[../proposals/Proposal Authoring|Proposal Authoring]]
"""


def render_relationships(records: list[dict[str, Any]], lookup: dict[str, dict[str, Any]]) -> str:
    lines = ["# Relationship Summary", "", f"> {NOTICE}", ""]
    for record in records:
        for relationship in record["relationships"]:
            target = lookup.get(relationship["target_id"])
            lines.append(
                f"- [[../{note_relative_path(record).as_posix()[:-3]}|{record['title']}]] "
                f"`{relationship['predicate']}` "
                f"[[../{note_relative_path(target).as_posix()[:-3]}|{relationship['target_title']}]] "
                f"— **{relationship['status']}**"
            )
    return "\n".join(lines) + "\n"


def render_canvas(records: list[dict[str, Any]]) -> dict[str, Any]:
    lookup = index_by_id(records)
    node_ids = {record["record_id"]: f"n{index + 1}" for index, record in enumerate(records)}
    nodes = []
    for index, record in enumerate(records):
        nodes.append({
            "id": node_ids[record["record_id"]], "type": "file",
            # Obsidian Canvas file-node paths are vault-root-relative, not
            # relative to the directory containing the .canvas file.
            "file": note_relative_path(record).as_posix(),
            "x": (index % 4) * 430, "y": (index // 4) * 260,
            "width": 390, "height": 220,
        })
    edges = []
    edge_no = 1
    for record in records:
        for relationship in record["relationships"]:
            if relationship["target_id"] not in lookup:
                continue
            edges.append({
                "id": f"e{edge_no}", "fromNode": node_ids[record["record_id"]],
                "toNode": node_ids[relationship["target_id"]],
                "label": relationship["predicate"],
            })
            edge_no += 1
    return {"nodes": nodes, "edges": edges}


def proposal_markdown(proposal: dict[str, Any], receipt: dict[str, Any] | None) -> str:
    decision = receipt["decision"] if receipt else "pending backend review"
    lines = [
        f"# {proposal.get('title') or proposal['record_id']}", "",
        "> [!warning] Pending proposal — not canonical", "> Submission creates a proposal for review. It does not alter the canonical Knowledge Prism corpus.", "",
        f"- **Proposal ID:** `{proposal['record_id']}`", f"- **Type:** `{proposal['proposal_type']}`",
        f"- **Submitted status:** `{proposal['status']}`", f"- **Displayed review status:** `{decision}`",
        f"- **Created by:** `{proposal['created_by']}`", "", "## Rationale", "", proposal["rationale"], "",
    ]
    if proposal.get("source_id"):
        lines.extend(["## Proposed connection", "", f"`{proposal['source_id']}` **{proposal['predicate']}** `{proposal['target_id']}`", ""])
    if receipt:
        lines.extend([
            "## Backend decision receipt", "", f"- **Decision:** `{receipt['decision']}`",
            f"- **Decided by:** `{receipt['decided_by']}`", f"- **Decided at:** `{receipt['decided_ts']}`",
            f"- **Resulting canonical record:** `{receipt.get('resulting_record_id') or 'none'}`", "",
            receipt["review_message"], "",
            "> Acceptance is review of a proposal only. It does not canonicalise knowledge.",
        ])
    return "\n".join(lines) + "\n"


def copy_contract_package(package: Path, vault: Path) -> None:
    shutil.copy2(package / "export_manifest.json", vault / "export_manifest.json")
    for source in sorted((package / "records").glob("*.json")):
        shutil.copy2(source, vault / "records" / source.name)
    for lifecycle in ("inbox", "accepted", "revised", "rejected", "receipts"):
        target = vault / "proposals" / lifecycle
        target.mkdir(parents=True, exist_ok=True)
        source_dir = package / "proposals" / lifecycle
        if source_dir.exists():
            for source in sorted(source_dir.glob("*.json")):
                shutil.copy2(source, target / source.name)


def demo_receipt() -> dict[str, Any]:
    return {
        "receipt_version": "1.0", "proposal_id": "PROP-000001", "decision": "accepted",
        "decided_by": "synthetic_fixture_reviewer", "decided_ts": "2026-07-16T12:30:00+00:00",
        "review_message": "[SYNTHETIC] Accepted for further backend consideration; no canonical promotion occurred.",
        "resulting_record_id": None,
    }


def write_supporting_files(vault: Path, manifest: dict[str, Any], records: list[dict[str, Any]], demo: bool) -> None:
    lookup = index_by_id(records)
    proposals = [load_json(path) for path in sorted((vault / "proposals/inbox").glob("*.json"))]
    receipts = [load_json(path) for path in sorted((vault / "proposals/receipts").glob("*.json"))]
    if demo and proposals and not receipts:
        receipt = demo_receipt()
        dump_json(vault / "proposals/receipts/PROP-000001.receipt.json", receipt)
        receipts = [receipt]
    receipt_by_proposal = {item["proposal_id"]: item for item in receipts}
    dashboard = vault / "00_dashboard"
    (dashboard / "Knowledge Prism Dashboard.md").write_text(render_dashboard(manifest, records, len(proposals), len(receipts)), encoding="utf-8")
    labels = {"concept": "Concept Index", "entity": "Entity Index", "source": "Source Index", "claim": "Argument Index"}
    for record_type, title in labels.items():
        selected = [record for record in records if record["record_type"] == record_type]
        (dashboard / f"{title}.md").write_text(render_index(title, selected, vault), encoding="utf-8")
    (dashboard / "Recent Updates.md").write_text(render_index("Recent Updates", records, vault), encoding="utf-8")
    (dashboard / "Relationship Summary.md").write_text(render_relationships(records, lookup), encoding="utf-8")
    pending = [f"- [[../proposals/{p['record_id']}|{p.get('title', p['record_id'])}]] — **proposed**" for p in proposals]
    (dashboard / "Pending Proposals.md").write_text("# Pending Proposals\n\n" + ("\n".join(pending) if pending else "- None.") + "\n", encoding="utf-8")
    (dashboard / "Synchronisation Conflicts.md").write_text("# Synchronisation Conflicts\n\nSee `99_sync_conflicts/`. Conflict reports never overwrite the affected note.\n", encoding="utf-8")
    dump_json(vault / "08_canvases/Knowledge Prism Vertical Slice.canvas", render_canvas(records))
    for proposal in proposals:
        (vault / "proposals" / f"{proposal['record_id']}.md").write_text(proposal_markdown(proposal, receipt_by_proposal.get(proposal["record_id"])), encoding="utf-8")
    (vault / "templates/Researcher Synthesis.md").write_text(
        "---\nnote_type: researcher_synthesis\nstatus: researcher_synthesis\ncanonical: false\nrelated_record_ids:\n  - CON-000001\ncreated_by: researcher\n---\n\n# Research question\n\n# Relevant canonical records\n\n# Argument\n\n# Counterargument\n\n# Evidence needed\n\n# Proposed connections\n\n# Unresolved issues\n",
        encoding="utf-8",
    )
    (vault / "templates/Proposal.md").write_text(
        "# Proposal Authoring Template\n\n> Submission creates a proposal for review. It does not alter the canonical Knowledge Prism corpus.\n\n- Proposal type: relationship_proposal\n- Status: proposed\n- Source ID:\n- Target ID:\n- Predicate:\n- Rationale:\n",
        encoding="utf-8",
    )
    (vault / "proposals/Proposal Authoring.md").write_text(
        "# Proposal Authoring\n\n> [!warning] Proposal only\n> Submission creates a proposal for review. It does not alter the canonical Knowledge Prism corpus.\n\nUse `scripts/09_generate_obsidian_workspace.py proposal` to create schema-bounded JSON in `proposals/inbox/`. Only status `proposed` is emitted.\n",
        encoding="utf-8",
    )


def write_sync_preview(vault: Path, plan: list[PlannedNote]) -> None:
    lines = ["# Synchronisation Preview", "", "No files are silently overwritten when protected markers are malformed.", ""]
    for item in plan:
        detail = f" — {item.conflict}" if item.conflict else ""
        lines.append(f"- **{item.action.upper()}** `{item.destination.relative_to(vault)}`{detail}")
    (vault / "00_dashboard/Sync Preview.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def apply_sync(package: Path, vault: Path, demo: bool) -> tuple[int, int]:
    manifest, records, plan = plan_notes(package, vault)
    for directory in VAULT_DIRS:
        (vault / directory).mkdir(parents=True, exist_ok=True)
    copy_contract_package(package, vault)
    conflicts = 0
    for item in plan:
        if item.conflict:
            conflicts += 1
            report = vault / "99_sync_conflicts" / f"{item.destination.stem}.conflict.md"
            report.write_text(
                f"# Synchronisation conflict\n\n- File: `{item.destination.relative_to(vault)}`\n- Reason: {item.conflict}\n- Action: original file left untouched; manual review required.\n",
                encoding="utf-8",
            )
            continue
        item.destination.parent.mkdir(parents=True, exist_ok=True)
        item.destination.write_text(item.content, encoding="utf-8")
    write_supporting_files(vault, manifest, records, demo)
    write_sync_preview(vault, plan)
    (vault / "README.md").write_text(
        "# Knowledge Prism Obsidian Vertical Slice\n\nOpen this directory as an Obsidian vault. Start at `00_dashboard/Knowledge Prism Dashboard.md`. This fixture projection is synthetic and does not alter Knowledge Prism research state.\n",
        encoding="utf-8",
    )
    return len(plan), conflicts


def validate_proposal(payload: dict[str, Any]) -> list[str]:
    errors = []
    if payload.get("proposal_version") != "1.0": errors.append("proposal_version must be 1.0")
    if not ID_RE.fullmatch(str(payload.get("record_id", ""))) or not str(payload.get("record_id", "")).startswith("PROP-"): errors.append("record_id must match PROP-######")
    if payload.get("status") != "proposed": errors.append("status must be proposed")
    if not str(payload.get("rationale", "")).strip(): errors.append("rationale must be non-empty")
    if payload.get("proposal_type") == "relationship_proposal":
        if not ID_RE.fullmatch(str(payload.get("source_id", ""))): errors.append("source_id is invalid")
        if not ID_RE.fullmatch(str(payload.get("target_id", ""))): errors.append("target_id is invalid")
        if payload.get("predicate") not in PREDICATES: errors.append("predicate is outside the closed vocabulary")
    return errors


def cmd_sync(args: argparse.Namespace) -> int:
    package, vault = Path(args.package).resolve(), Path(args.vault).resolve()
    _manifest, _records, plan = plan_notes(package, vault)
    print("Synchronisation preview:")
    for item in plan:
        print(f"  {item.action.upper():8} {item.destination.relative_to(vault)}" + (f" — {item.conflict}" if item.conflict else ""))
    if not args.apply:
        print("Preview only; use --apply to write the vault.")
        return 0
    count, conflicts = apply_sync(package, vault, args.synthetic_demo_receipt)
    print(f"Applied synchronisation for {count} notes; {conflicts} conflict(s).")
    return 0 if conflicts == 0 else 2


def cmd_proposal(args: argparse.Namespace) -> int:
    payload = {
        "proposal_version": "1.0", "record_id": args.record_id,
        "proposal_type": "relationship_proposal", "status": "proposed",
        "title": args.title, "rationale": args.rationale, "created_by": args.created_by,
        "created_ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_id": args.source_id, "target_id": args.target_id, "predicate": args.predicate,
    }
    errors = validate_proposal(payload)
    if errors:
        for error in errors: print(f"ERROR: {error}")
        return 1
    destination = Path(args.vault).resolve() / "proposals/inbox" / f"{args.record_id}.json"
    dump_json(destination, payload)
    print(f"Wrote proposed-only review submission: {destination}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser("sync", help="preview or apply a projection-package synchronisation")
    sync.add_argument("package")
    sync.add_argument("vault")
    sync.add_argument("--apply", action="store_true")
    sync.add_argument("--synthetic-demo-receipt", action="store_true", help="fixture-only receipt display demonstration")
    sync.set_defaults(func=cmd_sync)
    proposal = sub.add_parser("proposal", help="write a controlled relationship proposal to the file inbox")
    proposal.add_argument("vault")
    proposal.add_argument("--record-id", required=True)
    proposal.add_argument("--title", required=True)
    proposal.add_argument("--rationale", required=True)
    proposal.add_argument("--created-by", default="researcher")
    proposal.add_argument("--source-id", required=True)
    proposal.add_argument("--target-id", required=True)
    proposal.add_argument("--predicate", required=True)
    proposal.set_defaults(func=cmd_proposal)
    return args.func(args) if (args := parser.parse_args()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
