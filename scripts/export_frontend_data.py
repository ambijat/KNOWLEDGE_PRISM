#!/usr/bin/env python3
"""Export static, public-safe data for the Knowledge Prism front end."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "knowledge_prism.db"
OUT_DIR = ROOT / "public" / "data"

PILOT_CSV = ROOT / "outputs" / "reports" / "BRIDGE_PILOT_VERDICTS.csv"
PILOT_JSON = ROOT / "outputs" / "reports" / "BRIDGE_PILOT_VERDICTS.json"
REVIEW_JSON = ROOT / "db" / "_staging" / "pilot_review_table.json"
LEDGER_DIR = ROOT / "ledger" / "blocks"
COUNTS_JSON = ROOT / "outputs" / "reports" / "project_status_counts.json"

ALLOWED_LAYERS = {
    "Layer_A_empirical_core",
    "Layer_B_method_theory_core",
    "Layer_AB_bridge_core",
    "Ambiguous_review_required",
    "Peripheral_context",
    "Out_of_domain_noise",
    "Misfile_or_metadata_error",
    "Unreadable_or_unassessable",
}

LAYER_ALIASES = {
    "A": "Layer_A_empirical_core",
    "B": "Layer_B_method_theory_core",
    "AB": "Layer_AB_bridge_core",
    "AMB": "Ambiguous_review_required",
    "Layer_B_geopolitics": "Layer_B_method_theory_core",
}

DISPOSITION_ORDER = [
    "core_candidate",
    "Peripheral_context",
    "claim_supported_but_project_irrelevant",
    "excluded_misfile_noise",
    "excluded_unreadable",
    "review_required",
]

PIPELINE = [
    {
        "stage": "Reconnaissance",
        "status": "done_metadata_level",
        "evidence_grade": "metadata_only",
        "note": "Archive terrain mapped; not treated as read scholarship.",
    },
    {
        "stage": "Master Register",
        "status": "built_partly_heuristic",
        "evidence_grade": "metadata_only / metadata_manifest",
        "note": "Unified register exists; duplicate and class labels still need verification.",
    },
    {
        "stage": "Evidence Ledger",
        "status": "operational",
        "evidence_grade": "infrastructure",
        "note": "Hash-chained blocks and claim lifecycle are active.",
    },
    {
        "stage": "Verification Queue",
        "status": "active",
        "evidence_grade": "hypothesis_only_not_scholarly_evidence",
        "note": "Bridge concepts are queued for sampled text checks.",
    },
    {
        "stage": "Rubric",
        "status": "active",
        "evidence_grade": "rubric_v2",
        "note": "Two independent axes: thesis support and project relevance.",
    },
    {
        "stage": "Pilot Verification",
        "status": "run",
        "evidence_grade": "sampled_text",
        "note": "18 rows tested; 11 rows sample-level promoted only.",
    },
    {
        "stage": "Core Corpus",
        "status": "not_final",
        "evidence_grade": "sampled_text_supported_core_candidate",
        "note": "No final ontology-core promotion has happened.",
    },
    {
        "stage": "Verified Ontology",
        "status": "not_started",
        "evidence_grade": "concept_verified / ontology_core",
        "note": "Both final ontology grades remain at zero.",
    },
    {
        "stage": "OpenAlex Enrichment",
        "status": "partial",
        "evidence_grade": "external_bibliographic_enrichment",
        "note": "Enrichment work is partial and not a substitute for text verification.",
    },
    {
        "stage": "Codex Handover",
        "status": "in_progress",
        "evidence_grade": "handover",
        "note": "Static front end now reads exported project-state JSON.",
    },
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(name: str, payload: Any) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def db_rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in con.execute(sql, params)]
    finally:
        con.close()


def db_scalar(sql: str, default: int = 0) -> int:
    con = sqlite3.connect(DB_PATH)
    try:
        row = con.execute(sql).fetchone()
        return int(row[0]) if row and row[0] is not None else default
    finally:
        con.close()


def normalize_key(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def find_review_match(row: dict[str, Any], review_rows: list[dict[str, Any]]) -> dict[str, Any]:
    title_key = normalize_key(row.get("title"))
    file_key = normalize_key(row.get("file"))
    for review in review_rows:
        review_title = normalize_key(review.get("title"))
        review_file = normalize_key(review.get("file"))
        if review_title and (title_key.startswith(review_title) or review_title.startswith(title_key[:35])):
            return review
        if review_file and (file_key.startswith(review_file) or review_file.startswith(file_key[:35])):
            return review
    return {}


def normalize_layer(row: dict[str, Any], review: dict[str, Any]) -> str:
    current = row.get("layer_tag")
    if current in LAYER_ALIASES:
        return LAYER_ALIASES[str(current)]
    if current in ALLOWED_LAYERS:
        return str(current)

    disposition = row.get("disposition")
    if disposition == "Peripheral_context":
        return "Peripheral_context"
    if disposition == "claim_supported_but_project_irrelevant":
        return "Out_of_domain_noise"
    if disposition == "excluded_misfile_noise":
        return "Misfile_or_metadata_error"
    if disposition == "excluded_unreadable":
        return "Unreadable_or_unassessable"

    track = review.get("relevance_track")
    if track in LAYER_ALIASES:
        return LAYER_ALIASES[str(track)]

    title = row.get("title") or ""
    if title in {"Why Islamism Is Winning", "To Lead the Free World: American Nationalism and the Cultural Roots of the Cold War"}:
        return "Layer_AB_bridge_core"
    if row.get("provisional_axis") == "empirical":
        return "Layer_A_empirical_core"
    if row.get("provisional_axis") in {"theory", "method"}:
        return "Layer_B_method_theory_core"
    return "Layer_AB_bridge_core"


def functional_caution(role: dict[str, Any]) -> str:
    grade = role.get("evidence_grade") or ""
    function_text = (role.get("ir_function") or "").upper()
    if grade == "sampled_text_supported_core_candidate":
        return "Functional reading is sample-supported, but still not concept_verified or ontology_core."
    if grade == "review_required":
        return "Functional promise is visible, but the evidence remains review-required; deeper sampling is needed before ontology use."
    if grade == "excluded_unreadable" or "UNDETERMINED" in function_text:
        return "Functional role is only a candidate because the text is unreadable; OCR or manual inspection is required."
    return "Functional reading must remain tied to its evidence grade and cannot be used as final ontology-core."


def build_functional_roles() -> list[dict[str, Any]]:
    role_rows = db_rows(
        """
        SELECT file, title, ir_function, contribution, interaction, layer_substantive,
               explanatory_contribution, evidence_grade, decided_by, ts, block_no
        FROM functional_role
        ORDER BY title COLLATE NOCASE
        """
    )
    pilot_csv = {row["file"]: row for row in load_csv(PILOT_CSV)}
    roles: list[dict[str, Any]] = []
    for index, role in enumerate(role_rows, start=1):
        csv_row = pilot_csv.get(role.get("file") or "", {})
        pilot_index = int(csv_row.get("idx") or index)
        payload = {
            "id": f"pilot_{pilot_index:02d}",
            "pilot_index": pilot_index,
            "file": role.get("file"),
            "title": role.get("title"),
            "functional_ir_role": role.get("ir_function") or "",
            "contribution_type": role.get("contribution") or "",
            "concept_family": role.get("contribution") or "",
            "interaction_illuminated": role.get("interaction") or "",
            "substantive_layer_explanation": role.get("layer_substantive") or "",
            "ontology_use": role.get("explanatory_contribution") or "",
            "limitation_or_caution": functional_caution(role),
            "functional_evidence_grade": role.get("evidence_grade"),
            "functional_decided_by": role.get("decided_by"),
            "functional_block_no": role.get("block_no"),
            "functional_updated_ts": role.get("ts"),
        }
        roles.append(payload)
    return sorted(roles, key=lambda item: item["pilot_index"])


def merge_functional_roles(
    pilot_rows: list[dict[str, Any]], functional_roles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_id = {role["id"]: role for role in functional_roles}
    by_file = {role.get("file"): role for role in functional_roles if role.get("file")}
    empty_functional = {
        "functional_ir_role": "",
        "contribution_type": "",
        "concept_family": "",
        "interaction_illuminated": "",
        "substantive_layer_explanation": "",
        "ontology_use": "",
        "limitation_or_caution": "No functional IR reading is recorded for this row yet.",
        "functional_evidence_grade": "",
        "functional_decided_by": "",
        "functional_block_no": None,
        "functional_updated_ts": "",
    }
    merged: list[dict[str, Any]] = []
    for row in pilot_rows:
        role = by_id.get(row["id"]) or by_file.get(row.get("file")) or {}
        merged.append({**row, **empty_functional, **role})
    return merged


def evidence_grade(row: dict[str, Any]) -> str:
    if row.get("evidence_grade"):
        return str(row["evidence_grade"])
    disposition = row.get("disposition")
    if disposition in {"excluded_misfile_noise", "excluded_unreadable"}:
        return "metadata_only"
    return "hypothesis_only_not_scholarly_evidence"


def quote_status(row: dict[str, Any]) -> str:
    value = row.get("quote_verified")
    if value == 1:
        return "verified"
    if value == 0:
        return "not_validated"
    return "not_applicable"


def next_action(row: dict[str, Any]) -> str:
    title = row.get("title") or ""
    disposition = row.get("disposition")
    grade = evidence_grade(row)
    if disposition == "core_candidate" and grade == "sampled_text_supported_core_candidate":
        return "Eligible for future concept verification; not ontology-core."
    if title == "Ratzel and Demography":
        return "Deeper re-sample needed; validated argument quote required."
    if title.startswith("Russia and the Mongols"):
        return "Deeper re-sample needed; decide core vs peripheral vs historical background."
    if disposition == "excluded_unreadable":
        return "OCR or manual inspection required before any relevance judgement."
    if disposition == "Peripheral_context":
        return "Keep as empirical context; do not promote to ontology-core."
    if disposition == "claim_supported_but_project_irrelevant":
        return "Keep excluded from core; claim support does not imply project relevance."
    if disposition == "excluded_misfile_noise":
        return "Keep excluded as administrative misfile/noise."
    return "Human review required before promotion."


def promotion_eligibility(row: dict[str, Any]) -> str:
    if row.get("evidence_grade") == "sampled_text_supported_core_candidate":
        return "sample_level_only_not_ontology_core"
    if row.get("disposition") == "review_required":
        return "blocked_pending_review"
    return "not_eligible"


def build_pilot_rows() -> list[dict[str, Any]]:
    disposition_rows = db_rows(
        """
        SELECT file, title, folder, provisional_axis, thesis_verdict, thesis_confidence,
               corpus_membership, disposition, reason, argument_quote, quote_verified,
               decided_by, ts, block_no, layer_tag, evidence_grade
        FROM verdict_disposition
        ORDER BY title COLLATE NOCASE
        """
    )
    pilot_csv = {row["file"]: row for row in load_csv(PILOT_CSV)}
    pilot_json = {row.get("file"): row for row in load_json(PILOT_JSON, [])}
    review_rows = load_json(REVIEW_JSON, [])

    pilot_rows: list[dict[str, Any]] = []
    for index, row in enumerate(disposition_rows, start=1):
        csv_row = pilot_csv.get(row["file"], {})
        json_row = pilot_json.get(row["file"], {})
        review = find_review_match(row, review_rows)
        layer = normalize_layer(row, review)
        grade = evidence_grade(row)
        concepts = json_row.get("concept_list") or []
        verdict = json_row.get("verdict") or {}
        pilot_index = int(csv_row.get("idx") or index)
        pilot_rows.append(
            {
                "id": f"pilot_{pilot_index:02d}",
                "pilot_index": pilot_index,
                "file": row.get("file"),
                "title": row.get("title"),
                "folder": row.get("folder"),
                "axis": row.get("provisional_axis") or csv_row.get("axis"),
                "total_pages": int(csv_row.get("total_pages") or csv_row.get("pages") or 0),
                "thesis_verdict": row.get("thesis_verdict"),
                "thesis_confidence": row.get("thesis_confidence"),
                "verdict_status": csv_row.get("verdict_status"),
                "quote_validation_status": quote_status(row),
                "argument_quote": row.get("argument_quote") or csv_row.get("argument_quote") or "",
                "concepts_seen": int(csv_row.get("concepts_seen") or 0),
                "concepts_total": int(csv_row.get("concepts_total") or len(concepts) or 0),
                "concepts": concepts,
                "ai_thesis": json_row.get("ai_thesis", ""),
                "thesis_reasoning": verdict.get("thesis_reasoning", ""),
                "disposition": row.get("disposition"),
                "corpus_membership": row.get("corpus_membership"),
                "evidence_grade": grade,
                "layer_tag": layer,
                "promotion_eligibility": promotion_eligibility(row),
                "next_action": next_action(row),
                "reason": row.get("reason") or review.get("reason") or "",
                "decided_by": row.get("decided_by"),
                "block_no": row.get("block_no"),
                "updated_ts": row.get("ts"),
            }
        )
    return sorted(pilot_rows, key=lambda item: item["pilot_index"])


def review_queue(pilot_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": row["title"],
            "file": row["file"],
            "thesis_verdict": row["thesis_verdict"],
            "confidence": row["thesis_confidence"],
            "quote_validation_status": row["quote_validation_status"],
            "disposition": row["disposition"],
            "evidence_grade": row["evidence_grade"],
            "layer_tag": row["layer_tag"],
            "functional_ir_role": row.get("functional_ir_role", ""),
            "interaction_illuminated": row.get("interaction_illuminated", ""),
            "ontology_use": row.get("ontology_use", ""),
            "limitation_or_caution": row.get("limitation_or_caution", ""),
            "next_action": row["next_action"],
            "reason": row["reason"],
        }
        for row in pilot_rows
        if row["disposition"] == "review_required" or row["disposition"] == "excluded_unreadable"
    ]


def disposition_census(pilot_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row["disposition"] for row in pilot_rows)
    return {key: counts.get(key, 0) for key in DISPOSITION_ORDER}


def evidence_dashboard(pilot_rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "provisional_unverified_rows": db_scalar(
            "SELECT COUNT(*) FROM bridge_concepts WHERE bridge_claim_status='provisional_unverified'"
        ),
        "sampled_text_supported_rows": sum(
            1 for row in pilot_rows if row["evidence_grade"] == "sampled_text_supported_core_candidate"
        ),
        "review_required_rows": sum(1 for row in pilot_rows if row["disposition"] == "review_required"),
        "out_of_domain_rows": sum(
            1 for row in pilot_rows if row["disposition"] == "claim_supported_but_project_irrelevant"
        ),
        "unreadable_rows": sum(1 for row in pilot_rows if row["disposition"] == "excluded_unreadable"),
        "ontology_core_rows": 0,
    }


def parse_jsonish(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if stripped[0] not in "[{":
        return value
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return value


def redact(value: Any) -> Any:
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if not isinstance(value, str):
        return value
    lowered = value.lower()
    if "secret" in lowered or "api_key" in lowered or "apikey" in lowered or ".env" in lowered:
        return "[sensitive reference redacted]"
    redacted = re.sub(r"/(?:home|media)/[^,\]\s)]+", "[local_path_redacted]", value)
    return redacted


def ledger_blocks() -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for path in sorted(LEDGER_DIR.glob("*.json")):
        data = load_json(path, {})
        if not data:
            continue
        blocks.append(
            {
                "block_no": data.get("block_no"),
                "block_id": data.get("block_id"),
                "title": data.get("title"),
                "ts": data.get("ts"),
                "actor": data.get("actor"),
                "action_type": "ledger_block",
                "inputs": redact(parse_jsonish(data.get("inputs", []))),
                "operations": redact(parse_jsonish(data.get("operations", []))),
                "artifacts_produced": redact(parse_jsonish(data.get("outputs", []))),
                "prev_hash": data.get("prev_hash"),
                "block_hash": data.get("block_hash"),
                "source_file": path.name,
            }
        )

    blocks.sort(key=lambda item: int(item.get("block_no") or 0))
    previous_hash = None
    for block in blocks:
        if block["block_no"] == 0:
            block["chain_link_ok"] = True
        else:
            block["chain_link_ok"] = bool(previous_hash and block.get("prev_hash") == previous_hash)
        previous_hash = block.get("block_hash")
    return blocks


def project_status(pilot_rows: list[dict[str, Any]], blocks: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = load_json(COUNTS_JSON, {})
    chain_ok = all(block.get("chain_link_ok") for block in blocks)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_identity": "Knowledge Prism Graph Lab",
        "summary": "Proof-of-provenance graph lab for converting a scholarly corpus into an evidence-graded research ontology.",
        "master_corpus_rows": db_scalar("SELECT COUNT(*) FROM master_corpus"),
        "bridge_concept_rows": db_scalar("SELECT COUNT(*) FROM bridge_concepts"),
        "pilot_rows": len(pilot_rows),
        "promoted_sample_level_rows": sum(
            1 for row in pilot_rows if row["evidence_grade"] == "sampled_text_supported_core_candidate"
        ),
        "ontology_core_rows": 0,
        "concept_verified_rows": 0,
        "ledger_blocks": len(blocks),
        "ledger_chain_verifies": chain_ok,
        "functional_role_rows": db_scalar("SELECT COUNT(*) FROM functional_role"),
        "source_counts": status_counts,
        "data_sources": [
            "db/knowledge_prism.db: verdict_disposition, functional_role, bridge_concepts, master_corpus",
            "outputs/reports/BRIDGE_PILOT_VERDICTS.csv",
            "outputs/reports/BRIDGE_PILOT_VERDICTS.json",
            "ledger/blocks/*.json",
            "outputs/reports/project_status_counts.json",
        ],
        "public_safety": "Secrets, API keys, and absolute local paths are not exported.",
    }


def graph_data(pilot_rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    def add_node(node_id: str, label: str, node_type: str, group: str) -> None:
        nodes.setdefault(node_id, {"id": node_id, "label": label, "type": node_type, "group": group})

    for row in pilot_rows:
        work_id = f"work:{normalize_key(row['title'])[:50]}"
        grade_id = f"grade:{row['evidence_grade']}"
        disposition_id = f"disposition:{row['disposition']}"
        layer_id = f"layer:{row['layer_tag']}"
        action_id = f"action:{normalize_key(row['next_action'])[:50]}"
        function_id = f"function:{normalize_key(row.get('functional_ir_role'))[:50]}"
        interaction_id = f"interaction:{normalize_key(row.get('interaction_illuminated'))[:50]}"
        concept_family_id = f"concept_family:{normalize_key(row.get('concept_family'))[:50]}"
        ontology_id = f"ontology_use:{normalize_key(row.get('ontology_use'))[:50]}"

        add_node(work_id, row["title"], "work", "work")
        add_node(grade_id, row["evidence_grade"], "evidence_grade", "evidence")
        add_node(disposition_id, row["disposition"], "disposition", "disposition")
        add_node(layer_id, row["layer_tag"], "layer", "layer")
        add_node(action_id, row["next_action"], "required_action", "action")
        if row.get("functional_ir_role"):
            add_node(function_id, row["functional_ir_role"], "ir_function", "function")
            add_node(interaction_id, row.get("interaction_illuminated", ""), "interaction", "interaction")
            add_node(concept_family_id, row.get("concept_family", ""), "concept_family", "concept")
            add_node(ontology_id, row.get("ontology_use", ""), "ontology_use", "ontology")

        edges.extend(
            [
                {"source": work_id, "target": grade_id, "relation": "work_to_evidence_grade"},
                {"source": work_id, "target": disposition_id, "relation": "work_to_disposition"},
                {"source": work_id, "target": layer_id, "relation": "work_to_layer"},
                {"source": work_id, "target": action_id, "relation": "work_to_next_action"},
            ]
        )
        if row.get("functional_ir_role"):
            edges.extend(
                [
                    {"source": work_id, "target": function_id, "relation": "work_to_functional_role"},
                    {"source": work_id, "target": interaction_id, "relation": "work_to_interaction"},
                    {"source": work_id, "target": concept_family_id, "relation": "work_to_concept_family"},
                    {"source": work_id, "target": ontology_id, "relation": "work_to_ontology_use"},
                ]
            )

        for concept in row.get("concepts", [])[:4]:
            concept_id = f"concept:{normalize_key(concept)[:50]}"
            add_node(concept_id, concept, "concept", "concept")
            edges.append({"source": work_id, "target": concept_id, "relation": "work_to_concept"})

    return {"nodes": list(nodes.values()), "edges": edges}


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Missing database: {DB_PATH}")

    functional_roles = build_functional_roles()
    pilot_rows = merge_functional_roles(build_pilot_rows(), functional_roles)
    promoted_rows = [
        row for row in pilot_rows if row["evidence_grade"] == "sampled_text_supported_core_candidate"
    ]
    queue = review_queue(pilot_rows)
    census = disposition_census(pilot_rows)
    blocks = ledger_blocks()
    status = project_status(pilot_rows, blocks)

    write_json("pilot_rows.json", pilot_rows)
    write_json("functional_roles.json", functional_roles)
    write_json("promoted_rows.json", promoted_rows)
    write_json("review_queue.json", queue)
    write_json("disposition_census.json", census)
    write_json("ledger_blocks.json", blocks)
    write_json("project_status.json", status)
    write_json("evidence_dashboard.json", evidence_dashboard(pilot_rows))
    write_json("pipeline.json", PIPELINE)
    write_json("graph.json", graph_data(pilot_rows))

    print(
        f"Exported {len(pilot_rows)} pilot rows, {len(functional_roles)} functional roles, "
        f"{len(promoted_rows)} promoted rows, {len(blocks)} ledger blocks."
    )
    print(f"Wrote static data to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
