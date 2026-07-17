"""Concept and ontology-fit service for GUI v0.2.

This service maps scholar concepts against already-readable project state using
non-promotional labels. A design-map match remains not verified.
"""
from __future__ import annotations

from typing import Any

from .rumination import ResearchFragment, concept_fit as _concept_fit, extract_concepts


def match_concepts(
    concepts_text: str,
    fragments: list[ResearchFragment],
    design_nodes: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Match concepts without creating evidence, queue, or ontology changes."""
    return _concept_fit(concepts_text, fragments, design_nodes, evidence_rows, queue_rows)


__all__ = ["extract_concepts", "match_concepts"]
