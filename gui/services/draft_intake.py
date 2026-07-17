"""Scholar fragment intake and research-organ building for GUI v0.2.

This service handles scholar-authored rumination only. Captured material is
always labelled ``scholar_input_not_evidence`` and is never written to evidence,
ontology, corpus, queue, disposition, boundary, or research-state tables.
"""
from __future__ import annotations

from .rumination import (
    CONFIDENCE_LEVELS,
    FRAGMENT_LABEL,
    INPUT_TYPES,
    RESEARCH_ORGANS,
    RUMINATION_DIR,
    SOURCE_NOTES,
    ResearchFragment,
    build_organ_map,
    classify_fragment,
    classify_text,
    draft_organ_text,
    empty_organ_map,
    fragments_as_rows,
    generate_synopsis_skeleton,
    new_fragment,
    organ_confidence,
    organ_rows,
    write_markdown,
    write_organ_map_csv,
    write_rumination_log,
)


__all__ = [
    "CONFIDENCE_LEVELS",
    "FRAGMENT_LABEL",
    "INPUT_TYPES",
    "RESEARCH_ORGANS",
    "RUMINATION_DIR",
    "SOURCE_NOTES",
    "ResearchFragment",
    "build_organ_map",
    "classify_fragment",
    "classify_text",
    "draft_organ_text",
    "empty_organ_map",
    "fragments_as_rows",
    "generate_synopsis_skeleton",
    "new_fragment",
    "organ_confidence",
    "organ_rows",
    "write_markdown",
    "write_organ_map_csv",
    "write_rumination_log",
]
