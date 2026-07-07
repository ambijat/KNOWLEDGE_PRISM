# KNOWLEDGE PRISM — Session Restore & Provenance Guide

This project is a **persistent, cross-session knowledge base** for modelling
knowledge structures in International Relations. Its spine is a single SQLite
database governed by a **proof-of-provenance** discipline: nothing is silently
overwritten, and every claim, classification, and output carries a verifiable
audit trail.

---

## 1. Start an agent shift (required first step)

Every future AI or human-assisted shift must begin with the boot + action-log
ritual:

```bash
cd KNOWLEDGE_PRISM
python3 scripts/05_start_agent_shift.py \
  --task-id "<short-task-id>" \
  --intent "<why this shift is starting>" \
  --scope "<expected file or area>"
```

This command:

1. runs the full project restore briefing,
2. verifies the granular action-log chain,
3. verifies the milestone provenance chain,
4. appends a hash-linked start record for the task,
5. verifies the action-log chain again.

Do not edit files, promote claims, run verification batches, or alter the GUI
before this ritual succeeds.

## 2. Restore a session manually

```bash
cd KNOWLEDGE_PRISM
python3 db/prism.py boot
```

`boot` prints the full restore briefing:
- **Chain integrity** — recomputes every block hash and confirms the links.
- **Provenance blocks** — the sealed history (genesis → codex takeover → latest).
- **Ontology** — the 5 latent axes and the top weighted A×B seam edges.
- **Accepted claims** — the load-bearing, verified assertions.
- **Provisional claims** — open questions still needing verification.
- **Retrievables** — every deliverable with its artifact version id.

Other commands: `verify`, `blocks`, `claims [provisional|accepted]`,
`ontology`, `retrievables`, `facts`.

---

## 3. What lives where

| Path | Role |
|------|------|
| `db/knowledge_prism.db` | The spine — 18 tables (see below). |
| `db/build_prism_db.py` | Idempotent builder: rebuilds **derived** tables from `db/_staging/` CSVs. Persistent tables are never dropped. |
| `db/populate_ontology_and_ledger.py` | Lays down provenance **blocks**, **claims**, **artifact fingerprints**, and the ontology. Append-only + idempotent. |
| `db/prism_ledger.py` | The proof-of-provenance library (blocks, claims, hashing, chain verify). |
| `db/prism.py` | The boot / query CLI. |
| `ledger/blocks/*.json` | Human-readable JSON mirror of each sealed block (recovery source). |
| `data/processed/`, `outputs/` | Deliverables (registers, seams, maps, reports). |

---

## 4. The proof-of-provenance model

**Blocks** — work is sealed in hash-chained blocks. Each block's hash is
`sha256(block_no | prev_hash | payload | ts)`. Change any sealed payload and
`verify` reports a mismatch *and* a broken link at the next block. Tamper-evident
by construction.

**Claims are transactions.** Every assertion is a row in `claim` with an
`evidence_grade`, and its life is an **append-only** trail in `claim_event`
(`created → verified / corrected / rejected / superseded`). The current status
is the latest event; history is never erased.

**Evidence grades** (weakest → strongest):
`metadata_only` · `metadata_manifest` · `hypothesis_only` · `frontmatter_seen`
· `sampled_text` · `analysis` · `concept_verified`.
A claim may only be *used* as settled fact when it is **accepted**. AI-generated
bridge concepts are `hypothesis_only` and stay provisional until a human or a
text-level check verifies them.

**Artifact fingerprints** — `artifact_hash` is a change-only log of every
project file's sha256. Re-running only records a file when its hash actually
changes, so the log is a true modification history.

---

## 5. Adding new work (for future sessions)

```python
import sys; sys.path.insert(0,"db"); import prism_ledger as L
con = L.connect()

# 1. seal the session's work as the next block
bn = L.seal_block(con, "block_0003_<slug>", "<title>", "<session_id>", "claude",
                  inputs=[...], operations=[...], outputs=[...])

# 2. register any new assertions as claims
cid = L.register_claim(con, "<claim text>", "<scope>", "<source_file>",
                       "analysis", "AI", bn, status="provisional")

# 3. when verified, append a lifecycle event (never overwrite)
L.advance_claim(con, cid, "verified", "accepted", "<basis>", "human_review", bn)

# 4. fingerprint changed/added files
L.hash_tree(con, L.ROOT, bn, "project",
            exts=(".csv",".json",".md",".png",".py"))

# 5. register deliverables
L.add_retrievable(con, "<name>", "<kind>", "<disk_path>",
                  "<artifact_version_id>", "<session_id>", "<note>")
```

Always `python3 db/prism.py verify` after, and confirm the JSON mirror in
`ledger/blocks/` matches.

---

## 6. Recovery from tampering

If `verify` reports BROKEN and the payload edit was accidental: clear the
persistent provenance tables (`block`, `claim`, `claim_event`, `artifact_hash`),
delete `ledger/blocks/*.json`, and re-run `populate_ontology_and_ledger.py` —
it re-seals the canonical history from the source-of-truth script. The JSON
mirror and the DB are then re-verified to agree.

---

## 7. Database tables

**Persistent (never dropped — the history):**
`block`, `claim`, `claim_event`, `artifact_hash`, `session_log`,
`ontology_node`, `ontology_edge`, `retrievable`, `source_registry`.

**Derived (rebuilt from `db/_staging/` each build):**
`master_corpus` (35,861), `zotero_register` (1,841), `bridge_concepts` (392),
`recoll_subject_folders` (502), `deepread_folders` (13),
`solemon_crawl` (35,178), `pub_eigenspace` (47), `intersection_seam` (136),
`step2_corpus` (86).
