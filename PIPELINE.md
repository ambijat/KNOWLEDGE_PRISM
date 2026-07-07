# KNOWLEDGE PRISM — The Governing Pipeline

The project advances through eight disciplined stages. Each stage has an
**evidence gate**: work may not be *used as scholarship* until it clears the
grade its stage requires. Nothing is silently promoted; every promotion is a
`claim_event` in the ledger with a stated basis.

```
Reconnaissance → Master Register → Evidence Ledger → Verification Queue
   → Core Corpus → Ontology → OpenAlex Enrichment → Codex Handover
```

**The cardinal rule of this project:** *folder names, titles, tags, and
metadata are clues, not evidence.* A concept is only real when it has been seen
in the text. Until then it is `hypothesis_only` and stays provisional.

---

## Stage status (honestly graded)

| # | Stage | Sealed block | Status | Evidence grade | Gate to advance |
|---|-------|-------------|--------|----------------|-----------------|
| 1 | **Reconnaissance** | `block_0000` | ✅ complete *(provisional)* | `metadata_only` / `folder_inferred` | — done, but never promotable past metadata without text |
| 2 | **Master Register** | `block_0001` | ✅ built | `metadata_only` + `metadata_manifest` | dedupe verified; corpus classes are still heuristic |
| 3 | **Evidence Ledger** | `block_0002` | ✅ operational | `infrastructure` | hash chain verifies + idempotent ✔ |
| 4 | **Verification Queue** | `block_0003+` | ⏳ ready, not executed | queue = `hypothesis_only` | sample front-matter/chapter text of the 392 bridge books |
| 5 | **Core Corpus** | — | ⛔ not started | — | text-level Core / Peripheral / Noise triage |
| 6 | **Ontology (verified)** | — | 🟡 provisional | `analysis` (eigenspace) + `metadata` (domain) | promote nodes/edges to `concept_verified` from text |
| 7 | **OpenAlex Enrichment** | partial | 🟡 partial | Step-2 loop done (86 papers); corpus not reconciled | reconcile the 12,594-doc corpus against the scholarly graph |
| 8 | **Codex Handover** | — | ⛔ not started | — | stages 1–7 mature + software packaged |

---

## What each stage means here

**1 · Reconnaissance** — *Discovering the shape of the archive.* Zotero (1,841
items), Recoll manifest (12,594 unique docs, ~53 GB across 8 folders), subject-
folder classification, first two-layer domain inference. **This is
metadata-level only.** It correctly mapped the terrain; it did not read the
books. Recorded as `block_0000`.

**2 · Master Register** — *One unified, deduplicated register.* 35,861 rows
after path-union; 3,347 duplicate groups; preliminary classes
(11,453 Core / 839 Peripheral / 432 Noise / 23,137 Unknown). The classes are
**heuristic guesses from paths and titles**, not verified. Recorded as
`block_0001`.

**3 · Evidence Ledger** — *Proof-of-provenance spine.* Hash-chained blocks,
claims-as-transactions with an append-only lifecycle, artifact fingerprints.
This is what lets every later stage promote a claim honestly and prove it
later. Recorded as `block_0002`.

**4 · Verification Queue** — *The first real text-level scholarship.* The 392
bridge-concept books each carry an AI-hypothesized thesis + concept list, all
`provisional_unverified`. Verification = open the PDF, sample front-matter /
chapter text, and decide whether the text **supports, partially supports,
contradicts, or does not mention** the hypothesis. Each decision is a
`claim_event` (basis = `sampled_text`) that promotes or rejects the claim.

**5 · Core Corpus** — *A defensible working set.* Once verification method is
proven, triage the ~11,453 preliminary-Core candidates to a text-confirmed core.
Distinguishes the corpus we can cite from the corpus we merely possess.

**6 · Ontology (verified)** — *The knowledge structure, grounded.* The current
5 latent axes + A×B seam come from the publication eigenspace (a real
computation, graded `analysis`) plus metadata inference (provisional). Nodes and
edges get promoted to `concept_verified` only as verified text accumulates
beneath them.

**7 · OpenAlex Enrichment** — *Anchor to the external scholarly graph.* The
Step-2 loop already pulled 86 papers via OpenAlex/arXiv. The remaining work is
reconciling the corpus itself (DOIs, citations, canonical metadata) against
OpenAlex so the ontology sits on verifiable bibliographic ground.

**8 · Codex Handover** — *Baton to autonomous software.* Only once 1–7 are
mature: packaged scripts, stable schema, verified core, documented ontology —
a state another agent (or Codex) can safely inherit.

---

## How the ledger enforces this

- A claim's **evidence grade** records how it was established
  (`metadata_only` → `metadata_manifest` → `hypothesis_only` →
  `frontmatter_seen` → `sampled_text` → `analysis` → `concept_verified`).
- A claim may be **used as fact only when `accepted`**, and it only becomes
  accepted through a `claim_event` with a real basis.
- `python3 db/prism.py boot` at the start of every session reprints which
  stage each claim sits at, so we never mistake a clue for a finding again.
