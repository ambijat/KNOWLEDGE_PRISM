"""Project-state readers for the local operational GUI.

These helpers are intentionally read-only. They do not mutate evidence,
ontology, queue, corpus, claim, or boundary state.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any

from . import db_access


@dataclass(frozen=True)
class ProjectState:
    ledger_blocks: int
    latest_block_no: int | None
    latest_block_title: str
    master_corpus_rows: int
    pilot_rows: int
    sample_supported_rows: int
    verification_queue_rows: int
    boundary_proposal_rows: int
    concept_verified_rows: int
    ontology_core_rows: int
    design_nodes: int
    design_edges: int
    functional_role_rows: int
    chain_ok: bool
    action_log_ok: bool
    current_stage: str


def load_project_state() -> ProjectState:
    latest = db_access.rows(
        "SELECT block_no,title FROM block ORDER BY block_no DESC LIMIT 1"
    )
    latest_block_no = latest[0]["block_no"] if latest else None
    latest_block_title = latest[0]["title"] if latest else ""
    sample_supported = db_access.scalar(
        "SELECT COUNT(*) FROM verdict_disposition "
        "WHERE evidence_grade='sampled_text_supported_core_candidate'"
    )
    return ProjectState(
        ledger_blocks=db_access.table_count("block"),
        latest_block_no=latest_block_no,
        latest_block_title=latest_block_title,
        master_corpus_rows=db_access.table_count("master_corpus"),
        pilot_rows=db_access.table_count("verdict_disposition"),
        sample_supported_rows=int(sample_supported),
        verification_queue_rows=db_access.table_count("verification_queue"),
        boundary_proposal_rows=db_access.table_count("boundary_proposal"),
        concept_verified_rows=int(
            db_access.scalar("SELECT COUNT(*) FROM claim WHERE evidence_grade='concept_verified'")
        ),
        ontology_core_rows=0,
        design_nodes=int(
            db_access.scalar(
                "SELECT COUNT(*) FROM ontology_node "
                "WHERE COALESCE(provenance_status,'design_hypothesis')='design_hypothesis'"
            )
        ),
        design_edges=db_access.table_count("ontology_edge"),
        functional_role_rows=db_access.table_count("functional_role"),
        chain_ok=verify_chain(),
        action_log_ok=verify_action_log(),
        current_stage="Stage 4 of 8 - Verification Queue",
    )


def verification_queue() -> list[dict[str, Any]]:
    return db_access.rows(
        "SELECT queue_id,title,candidate_type,status,source_stage,layer_prior,"
        "rationale,recommended_action,duplicate_group_id,canonical_candidate_id,"
        "approved_by,approved_ts,sampling_block_no,rubric_version "
        "FROM verification_queue ORDER BY queue_id"
    )


def ontology_status() -> dict[str, Any]:
    return {
        "design_nodes": db_access.rows(
            "SELECT node_id,node_type,label,layer,provenance_status "
            "FROM ontology_node ORDER BY node_type,label"
        ),
        "design_edges": db_access.rows(
            "SELECT src,dst,rel,weight FROM ontology_edge ORDER BY weight DESC LIMIT 50"
        ),
        "verified_ontology_core_rows": [],
    }


def boundary_proposals() -> list[dict[str, Any]]:
    return db_access.rows(
        "SELECT proposal_id,scope,observation,proposed_change,status,triggered_by,"
        "decided_by,ts,block_no FROM boundary_proposal ORDER BY proposal_id"
    )


def evidence_rows(limit: int = 50) -> list[dict[str, Any]]:
    return db_access.rows(
        "SELECT title,thesis_verdict,thesis_confidence,disposition,evidence_grade,"
        "layer_norm,reason FROM verdict_disposition ORDER BY title LIMIT ?",
        (limit,),
    )


def functional_roles(limit: int = 50) -> list[dict[str, Any]]:
    return db_access.rows(
        "SELECT title,ir_function,interaction,layer_norm,explanatory_contribution,"
        "evidence_grade FROM functional_role ORDER BY title LIMIT ?",
        (limit,),
    )


def verify_chain() -> bool:
    return _run_ok(["python3", "db/prism.py", "verify"])


def verify_action_log() -> bool:
    return _run_ok(["python3", "scripts/04_log_agent_action.py", "verify"])


def _run_ok(cmd: list[str]) -> bool:
    result = subprocess.run(
        cmd,
        cwd=db_access.ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0
