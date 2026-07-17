# Audit Remediation Log — 2026-07-08

Closes findings from **PROJECT_AUDIT_2026-07-08.md**. All remediation was metadata/schema only,
sealed as **block 25** (`block_0025_audit_remediation_layer_ontology_provenance`); chain verifies OK,
action log 26 records. No evidence grade, disposition, claim, ontology membership, or boundary status changed.

## Findings → disposition

| # | Audit finding | Severity | Action | Status |
|---|---|---|---|---|
| §4 | Ontology `ontology_node` conflates Stage-1 design map with text-verified ontology (no provenance column) | Material | Added `provenance_status`; 43 nodes = `design_hypothesis`, 0 `text_verified` (matches 0 at `ontology_core`) | ✅ FIXED (block 25) |
| §2/consistency | Layer vocabulary drift: `layer_prior` (queue) vs `layer_tag` (disposition, 2 ad-hoc + 16 null) vs `layer_substantive` (14 free-text prose) | Material | Added controlled `layer_norm` (A\|B\|AB\|Peripheral\|Out_of_domain\|Ambiguous) to `verdict_disposition` + `functional_role`, derived from prose by leading-token rule; prose kept verbatim as rationale | ✅ FIXED (block 25) |
| audit follow-up | Trenin duplicate group recorded as 2 copies; `master_corpus` holds 4 | Minor | `recommended_action` note corrected to 4 physical copies; canonical still NULL (sha256 compare deferred, PDFs not opened) | ✅ FIXED (block 25) |
| process | No automated evidence-integrity check; audit ran ad-hoc SQL | Enhancement | Added `scripts/00b_validate_db_consistency.py` (read-only, 5 checks); passes green before and after rebuild | ✅ ADDED (block 25) |
| §1 | Block 23 label typo (`block_0022_codex_index_development_update` at block_no 23) | Cosmetic | Left sealed (rewriting breaks chain); Codex to fix label convention forward | ⏳ OPEN (Codex track) |
| §6 | Redundant top-level status docs (ACTION_PLAN/PROJECT_STATUS/ROADMAP/PREAMBLE/README/SHIFT_HANDOVER) | Low | Consolidation proposed; not yet done | ⏳ OPEN |

## Verified-unchanged invariants (before and after block 25)
- 11 items at `sampled_text_supported_core_candidate`; **0** at `concept_verified`/`ontology_core`.
- 32 claims (27 accepted, 5 provisional).
- Trenin `KP-VQ-000001` status = `queued` (not sampled); boundary `KP-BP-000001` = `proposed_boundary_refinement` (not adopted).
- Ledger chain contiguous 0–25, no gaps, no duplicate block numbers.

## `layer_norm` derivation rule (auditable)
From `functional_role.layer_substantive` prose: contains "undecided"/"unconfirmed" → `Ambiguous`; else leading token `AB`→AB, `A`→A, `B`→B; else `Ambiguous`.
For `verdict_disposition` rows without a functional reading: `excluded_misfile_noise`/`claim_supported_but_project_irrelevant`→`Out_of_domain`; `Peripheral_context`→`Peripheral`; `excluded_unreadable`→`Ambiguous`.
Result — verdict_disposition: 10 B, 2 AB, 3 Out_of_domain, 1 Peripheral, 2 Ambiguous.

## Still queued (need user ruling)
1. sha256 canonicalisation of the 4 Trenin copies — belongs to the approved-for-sampling step (needs file access).
2. Standing evidence queue: re-sample #7 Ratzel (validated quote), #13 Russia/Mongols; reOCR #18 Advaita.
3. Codex block-label convention fix; status-doc consolidation.

## Artifacts
- `db/build_prism_db.py` v6 — schema persistence for `layer_norm` + `provenance_status`.
- `scripts/00b_validate_db_consistency.py` v1 — automated consistency validator.
- `docs/audit/PROJECT_AUDIT_2026-07-08.md` — the audit these remediations close.
