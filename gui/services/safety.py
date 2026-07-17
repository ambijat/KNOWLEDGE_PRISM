"""Safety controls for Knowledge Prism operational GUI v0.3."""
from __future__ import annotations

READ_ONLY_WARNING = (
    "Read-only mode is active. Inspection and local report export are allowed. "
    "Queue status, evidence grades, ontology, corpus, and boundary state are not modified."
)

WRITE_MODE_WARNING = (
    "Governed write mode can modify queue status, sampling records, evidence verdicts, "
    "reports, and logs. It cannot silently promote ontology or alter evidence without confirmation."
)

DISABLED_ACTIONS = {
    "Run Governed Retrieval": "Disabled in v0.3. Recoll runs require explicit approval after query preview.",
    "Add Selected Retrieval Hits to Queue": "Disabled in v0.3. Queue mutation must be confirmed and logged.",
    "Approve for Sampling": "Disabled in v0.3. Approval is a governed queue-status change.",
    "Run Sampling": "Disabled in v0.3. Sampling requires approved_for_sampling status and rubric selection.",
    "Create Evidence Verdict": "Disabled in v0.3. Evidence grades require visible reviewer decisions.",
    "Promote to Ontology Core": "Disabled in v0.3. Ontology promotion requires full provenance and approval.",
}


def can_write(governed_write_mode: bool) -> bool:
    return bool(governed_write_mode)


def disabled_reason(action: str) -> str:
    return DISABLED_ACTIONS.get(action, "Disabled in v0.3 pending governed implementation.")
