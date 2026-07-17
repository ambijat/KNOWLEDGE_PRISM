"""Literature-plan and supervisor-brief service for GUI v0.2.

Outputs from this service are local writing and supervision aids only. They do
not run Recoll and do not create evidence.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .rumination import (
    BRIEF_PROVENANCE_NOTE,
    ResearchFragment,
    literature_search_plan as _literature_search_plan,
    supervisor_brief as _supervisor_brief,
    write_markdown,
    write_supervisor_brief,
)


def literature_search_plan(
    fragments: list[ResearchFragment],
    organ_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a search strategy suggestion without running retrieval."""
    return _literature_search_plan(fragments, organ_map)


def supervisor_brief(
    organ_map: dict[str, dict[str, Any]],
    plan: dict[str, Any] | None = None,
) -> str:
    """Build a supervisor-facing Markdown brief with the required provenance note."""
    return _supervisor_brief(organ_map, plan)


def export_supervisor_brief(markdown: str) -> Path:
    return write_supervisor_brief(markdown)


__all__ = [
    "BRIEF_PROVENANCE_NOTE",
    "export_supervisor_brief",
    "literature_search_plan",
    "supervisor_brief",
    "write_markdown",
]
