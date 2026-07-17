"""Draft diagnosis service for GUI v0.2.

Diagnosis is a writing-support check over scholar text. It does not verify
claims and does not promote material into the research ontology.
"""
from __future__ import annotations

from typing import Any

from .rumination import diagnose_draft as _diagnose_draft


def diagnose_draft(text: str) -> dict[str, Any]:
    """Return a non-evidentiary organ diagnosis for pasted or generated drafts."""
    return _diagnose_draft(text)
