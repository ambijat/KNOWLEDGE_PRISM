#!/usr/bin/env python3
"""
KNOWLEDGE PRISM — database builder.

Consolidates every inherited + generated artifact into a single SQLite DB
(knowledge_prism.db) that is the project's persistent spine across sessions.

Design principles
------------------
* Idempotent: re-running rebuilds the DERIVED tables from source CSVs, so the
  DB can always be regenerated from raw files (Phase-1 requirement).
* Append-only history: the session ledger (session_log, fact_ledger) is NEVER
  dropped — it accumulates across sessions so ontology + fidelity are restored.
* Evidence-graded: honors the takeover regime — every corpus/biblio/concept row
  keeps its evidence_grade and claim_use_allowed.

Run:  python3 db/build_prism_db.py
"""
import sqlite3, csv, json, os, sys, hashlib, datetime, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB   = os.path.join(ROOT, "db", "knowledge_prism.db")
STG  = os.path.join(ROOT, "db", "_staging")

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(65536),b''): h.update(c)
    return h.hexdigest()

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def read_csv(name):
    p=os.path.join(STG,name)
    if not os.path.exists(p): return [],[]
    # tolerate \r\n and BOM
    with open(p, newline='', encoding='utf-8-sig') as f:
        r=csv.reader(f)
        rows=list(r)
    if not rows: return [],[]
    return rows[0], rows[1:]

con=sqlite3.connect(DB)
con.execute("PRAGMA journal_mode=WAL")
cur=con.cursor()

# ---------------------------------------------------------------- PERSISTENT (never dropped)
# Proof-of-Provenance layer: hash-chained blocks, append-only claims, artifact fingerprints.
cur.executescript("""
CREATE TABLE IF NOT EXISTS block (
  block_no    INTEGER PRIMARY KEY,  -- 0 = genesis
  block_id    TEXT UNIQUE,          -- human label e.g. block_0002_codex_takeover
  title       TEXT,
  ts          TEXT,
  session_id  TEXT,
  actor       TEXT,                 -- claude | codex | user
  inputs      TEXT,                 -- JSON list
  operations  TEXT,                 -- JSON list
  outputs     TEXT,                 -- JSON list
  prev_hash   TEXT,                 -- hash of block_no-1 (chain link)
  block_hash  TEXT                  -- sha256 over (block_no|prev_hash|payload|ts)
);
CREATE TABLE IF NOT EXISTS claim (
  claim_id       TEXT PRIMARY KEY,  -- KP-CLAIM-000001
  claim_text     TEXT,
  scope          TEXT,
  source_file    TEXT,
  evidence_grade TEXT,              -- metadata_only|metadata_manifest|hypothesis_only|frontmatter_seen|sampled_text|concept_verified|analysis
  created_by     TEXT,             -- AI | human_review | codex
  created_ts     TEXT,
  block_no       INTEGER,          -- block that introduced it
  initial_status TEXT DEFAULT 'provisional'  -- provisional|accepted|rejected
);
CREATE TABLE IF NOT EXISTS claim_event (   -- append-only lifecycle; current status = latest event
  claim_id    TEXT,
  ts          TEXT,
  event       TEXT,                 -- created|verified|corrected|rejected|superseded
  from_status TEXT,
  to_status   TEXT,
  basis       TEXT,                 -- verification_basis
  actor       TEXT,
  block_no    INTEGER
);
CREATE TABLE IF NOT EXISTS artifact_hash (  -- append-only fingerprint log
  path        TEXT,
  sha256      TEXT,
  size_bytes  INTEGER,
  ts          TEXT,
  block_no    INTEGER,
  role        TEXT                  -- raw|register|report|map|db|script|external
);
CREATE TABLE IF NOT EXISTS session_log (
  session_id   TEXT,          -- frame_id or manual tag
  ts           TEXT,          -- ISO timestamp
  actor        TEXT,          -- 'claude' | 'user' | 'codex' | ...
  action       TEXT,          -- short verb: ingest, analyze, deliver, decide, correct
  target       TEXT,          -- what it acted on
  detail       TEXT,          -- free text / JSON
  block_no     INTEGER
);
CREATE TABLE IF NOT EXISTS ontology_node (
  node_id      TEXT PRIMARY KEY,
  node_type    TEXT,   -- Empirical Region | Actor | Process | Theory | Method | Knowledge Object | Pedagogic Use | Axis | Seam
  label        TEXT,
  layer        TEXT,   -- A (empirical) | B (method) | meta
  weight       REAL,
  detail       TEXT,
  provenance_status TEXT  -- design_hypothesis (Stage-1 eigenspace/domain map) | text_verified (block 25).
                          -- Distinguishes the a-priori design map from a text-verified ontology.
                          -- text_verified requires an item promoted to ontology_core; 0 so far.
);
CREATE TABLE IF NOT EXISTS ontology_edge (
  src TEXT, dst TEXT, rel TEXT, weight REAL
);
CREATE TABLE IF NOT EXISTS retrievable (
  name TEXT, kind TEXT, disk_path TEXT, artifact_version_id TEXT,
  session_id TEXT, ts TEXT, sha256 TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS source_registry (
  source_file TEXT, sha256 TEXT, n_rows INTEGER, ingested_ts TEXT, target_table TEXT
);
CREATE TABLE IF NOT EXISTS verdict_disposition (
  -- Persistent record of a sampling verdict + its two-axis disposition.
  -- Survives derived-table rebuilds. One row per (file, block_no) decision.
  file            TEXT,    -- source filename (joins bridge_concepts.file when present)
  title           TEXT,
  folder          TEXT,
  provisional_axis TEXT,   -- folder-inferred axis at sampling time
  thesis_verdict  TEXT,    -- AXIS 1: SUPPORTED|PARTIAL|CONTRADICTED|ABSENT|UNREADABLE
  thesis_confidence REAL,
  corpus_membership TEXT,  -- AXIS 2: core_candidate | excluded | review_required
  disposition     TEXT,    -- taxonomy value (see disposition_taxonomy)
  reason          TEXT,    -- human/AI free-text basis
  argument_quote  TEXT,    -- verbatim evidence if any
  quote_verified  INTEGER, -- 1 if quote found verbatim in slice, 0 if not, NULL if none
  decided_by      TEXT,    -- AI | human_review | codex
  layer_tag       TEXT,    -- optional sub-tag e.g. Layer_B_method_theory_core
  layer_norm      TEXT,    -- controlled: A|B|AB|Peripheral|Out_of_domain|Ambiguous (block 25); prose stays in functional_role
  evidence_grade  TEXT,    -- promotion grade on the evidence ladder (NULL until promoted)
  ts              TEXT,
  block_no        INTEGER
);
CREATE TABLE IF NOT EXISTS disposition_taxonomy (
  -- Controlled vocabulary for verdict_disposition.disposition.
  disposition   TEXT PRIMARY KEY,
  axis1_thesis  TEXT,   -- typical Axis-1 verdict for this disposition
  axis2_corpus  TEXT,   -- core_candidate | excluded | review_required
  meaning       TEXT,
  added_block   INTEGER
);
CREATE TABLE IF NOT EXISTS functional_role (
  -- Functional IR interpretation of an item (FUNCTIONAL_IR_INTERPRETATION_PROTOCOL.md).
  -- Subordinates the ledger to interpretation: the evidence grade is a confidence
  -- annotation ON the functional reading, never a substitute for it. Persistent.
  file            TEXT,    -- joins verdict_disposition.file / bridge_concepts.file
  title           TEXT,
  ir_function     TEXT,    -- Q1: what IR function the text performs
  contribution    TEXT,    -- Q2: empirical|theoretical|methodological|genealogy|historical|discourse (>=1)
  interaction     TEXT,    -- Q3: state-space|region-security|empire-frontier|identity-order|connectivity|conflict|knowledge-production|actor-behaviour
  layer_substantive TEXT,  -- Q4: A|B|AB argued in substance (free-text rationale, kept verbatim)
  layer_norm        TEXT,   -- controlled normalisation of layer_substantive (block 25): A|B|AB|Peripheral|Out_of_domain|Ambiguous
  explanatory_contribution TEXT, -- Q5: how it builds explanation for Eurasia/Afghanistan/C.Asia/geopolitics/IR
  evidence_grade  TEXT,    -- annotation only (mirrors verdict_disposition.evidence_grade)
  decided_by      TEXT,
  ts              TEXT,
  block_no        INTEGER
);
CREATE TABLE IF NOT EXISTS verification_queue (
  -- Auditable retrieval-stage queue. A retrieval clue (e.g. Recoll Kaleidoscope hit)
  -- is recorded here BEFORE any sampling, so the queueing act is visible and the
  -- kaleidoscope never behaves as an automatic research agent. Persistent.
  -- Pipeline: retrieval clue -> verification_queue -> approved sampling ->
  --           evidence grade -> functional interpretation -> possible ontology use.
  queue_id        TEXT,    -- e.g. KP-VQ-000001
  file            TEXT,    -- source basename
  title           TEXT,
  path            TEXT,    -- disk path of the surfaced copy
  source_stage    TEXT,    -- how it entered the queue e.g. recoll_kaleidoscope_trial_001
  candidate_type  TEXT,    -- controlled vocab: see queue_candidate_type_taxonomy
  clue_score      REAL,    -- retrieval clue score at time of queueing (NOT evidence)
  layer_prior     TEXT,    -- provisional layer prior (clue, overridable): A|B|AB|Peripheral|Out_of_domain|Ambiguous
  status          TEXT,    -- controlled vocab: see queue_status_taxonomy
  rationale       TEXT,    -- why queued
  recommended_action TEXT, -- next governed step
  decided_by      TEXT,    -- claude | codex | user
  ts              TEXT,
  block_no        INTEGER,
  -- pre-sampling governance fields (block 24). Null until the governed step that fills them.
  approved_by     TEXT,    -- who authorised queued -> approved_for_sampling
  approved_ts     TEXT,
  sampling_block_no INTEGER,-- block under which sampling occurs (distinct from queueing block_no)
  rubric_version  TEXT,    -- VERIFICATION_RUBRIC version governing the sample
  target_file_sha256 TEXT, -- binds a verdict to exact bytes sampled
  concept_probes  TEXT,    -- hypothesised concept terms to probe
  retrieval_cycle_id TEXT, -- which retrieval cycle surfaced it
  research_question TEXT,  -- RQ under which it surfaced
  raw_rank        INTEGER, -- raw retrieval rank behind clue_score
  duplicate_group_id TEXT, -- groups multiple drive-copies of the same work
  canonical_candidate_id TEXT -- chosen canonical queue_id; NULL until hash-compared
);
CREATE TABLE IF NOT EXISTS queue_candidate_type_taxonomy (
  -- Controlled vocabulary for verification_queue.candidate_type.
  candidate_type TEXT PRIMARY KEY,
  meaning        TEXT,
  synonyms       TEXT,   -- e.g. kaleidoscope_anchor_piece -> anchor_candidate
  added_block    INTEGER
);
CREATE TABLE IF NOT EXISTS queue_status_taxonomy (
  -- Controlled vocabulary for verification_queue.status.
  status      TEXT PRIMARY KEY,
  meaning     TEXT,
  is_terminal INTEGER,   -- 1 if a closed/terminal state
  added_block INTEGER
);
CREATE TABLE IF NOT EXISTS boundary_proposal (
  -- Boundary-kinematics ledger. A surprise during retrieval/verification may suggest
  -- moving the Layer A / Layer B / Layer AB boundary. Such a move is PROPOSED here,
  -- never enacted silently. Status stays 'proposed_boundary_refinement' until a
  -- user-ratified boundary block adopts it. Persistent.
  proposal_id     TEXT,    -- e.g. KP-BP-000001
  scope           TEXT,    -- which boundary e.g. layer_A_AB
  observation     TEXT,    -- the surprise that triggered it
  proposed_change TEXT,    -- the refinement proposed
  status          TEXT,    -- proposed_boundary_refinement | adopted | rejected
  triggered_by    TEXT,    -- source_stage / event
  decided_by      TEXT,
  ts              TEXT,
  block_no        INTEGER
);
CREATE TABLE IF NOT EXISTS scholar_input (
  -- Researcher's own captured ideas (mobile/desktop). Schema v0.2, FROZEN.
  -- CARDINAL RULE: a scholar input is NOT evidence. It may seed a research
  -- question / retrieval lens after explicit approval (status approved_to_question),
  -- but it may never become a verification_queue document, sampled evidence, a
  -- claim, a disposition, a functional role, a verified concept, or an ontology
  -- node. There is deliberately NO approved_to_evidence status. Persistent.
  scholar_id        TEXT PRIMARY KEY,   -- KP-SI-000001
  schema_version    TEXT NOT NULL,      -- '0.2'
  record_type       TEXT NOT NULL,      -- 'scholar_input_not_evidence'
  source            TEXT NOT NULL,      -- android_app | desktop_manual | desktop_import
  captured_ts       TEXT NOT NULL,      -- ISO-8601 (device capture time)
  imported_ts       TEXT,               -- ISO-8601 (desktop import time; null until imported)
  idea              TEXT NOT NULL,      -- required content
  draft_organ       TEXT,               -- advisory only; one of frozen organ vocab or null
  draft_diagnosis   TEXT,               -- advisory
  draft_search_plan TEXT,               -- draft keywords, NOT a Recoll lens
  supervisor_brief  TEXT,
  raw_notes         TEXT,
  voice_transcript  TEXT,
  tags              TEXT,
  confidence        TEXT,               -- researcher's subjective hunch; never an evidence grade
  project_title     TEXT,
  course_or_context TEXT,
  status            TEXT NOT NULL,      -- FK -> scholar_input_status_taxonomy.status
  content_sha256    TEXT NOT NULL,      -- dedupe/provenance hash of canonical content
  became_question   TEXT,               -- research-question id seeded, if approved (nullable)
  became_queue_id   TEXT,               -- verification_queue.queue_id ultimately reached (nullable)
  decided_by        TEXT,               -- 'user'; backend records, never initiates
  decided_ts        TEXT,
  rejection_reason  TEXT,               -- preserved for audit on rejection
  block_no          INTEGER             -- ledger block recording a promotion/rejection
);
CREATE TABLE IF NOT EXISTS scholar_input_status_taxonomy (
  -- Controlled vocabulary for scholar_input.status (schema v0.2, FROZEN).
  status      TEXT PRIMARY KEY,
  meaning     TEXT NOT NULL,
  added_block INTEGER
);

CREATE TABLE IF NOT EXISTS research_question (
  -- Governed destination for a scholar_input approved_to_question (block 28).
  -- This is the SEED of a research question / retrieval lens. It is NOT retrieval,
  -- NOT a verification_queue entry, NOT evidence. It only records that a rumination
  -- was promoted to a formal question, with reciprocal provenance to its origin.
  question_id       TEXT PRIMARY KEY,      -- KP-RQ-000001 (gap-safe max+1, 6-digit)
  question_text     TEXT NOT NULL,         -- the approved research-question / retrieval-lens text
  lens_type         TEXT NOT NULL,         -- 'research_question' | 'retrieval_lens'
  origin_scholar_id TEXT NOT NULL,         -- REVERSE provenance -> scholar_input.scholar_id
  status            TEXT NOT NULL,         -- 'approved_seed' (max status at this layer; no retrieval yet)
  created_by        TEXT NOT NULL,         -- reviewer/actor who approved
  created_ts        TEXT NOT NULL,
  block_no          INTEGER,
  UNIQUE(origin_scholar_id)                -- one scholar_input -> at most one approved question
);
""")

# Backfill layer_tag column on pre-existing verdict_disposition tables (idempotent).
_cols = [c[1] for c in cur.execute("PRAGMA table_info(verdict_disposition)").fetchall()]
if "layer_tag" not in _cols:
    cur.execute("ALTER TABLE verdict_disposition ADD COLUMN layer_tag TEXT")
if "evidence_grade" not in _cols:
    cur.execute("ALTER TABLE verdict_disposition ADD COLUMN evidence_grade TEXT")
if "layer_norm" not in _cols:
    cur.execute("ALTER TABLE verdict_disposition ADD COLUMN layer_norm TEXT")

# Backfill layer_norm on functional_role + provenance_status on ontology_node (block 25, idempotent).
_frcols = [c[1] for c in cur.execute("PRAGMA table_info(functional_role)").fetchall()]
if "layer_norm" not in _frcols:
    cur.execute("ALTER TABLE functional_role ADD COLUMN layer_norm TEXT")
_oncols = [c[1] for c in cur.execute("PRAGMA table_info(ontology_node)").fetchall()]
if "provenance_status" not in _oncols:
    cur.execute("ALTER TABLE ontology_node ADD COLUMN provenance_status TEXT")
# Any ontology node lacking a provenance status is the Stage-1 design/hypothesis map, not text-verified.
cur.execute("UPDATE ontology_node SET provenance_status='design_hypothesis' WHERE provenance_status IS NULL")

# Backfill pre-sampling governance columns on pre-existing verification_queue (block 24, idempotent).
_vqcols = [c[1] for c in cur.execute("PRAGMA table_info(verification_queue)").fetchall()]
for _n,_t in [("approved_by","TEXT"),("approved_ts","TEXT"),("sampling_block_no","INTEGER"),
              ("rubric_version","TEXT"),("target_file_sha256","TEXT"),("concept_probes","TEXT"),
              ("retrieval_cycle_id","TEXT"),("research_question","TEXT"),("raw_rank","INTEGER"),
              ("duplicate_group_id","TEXT"),("canonical_candidate_id","TEXT")]:
    if _n not in _vqcols:
        cur.execute(f"ALTER TABLE verification_queue ADD COLUMN {_n} {_t}")

# Seed queue controlled vocabularies (block 24). INSERT OR IGNORE preserves live rows.
_CAND_TYPES = [
 ("anchor_candidate","High-significance candidate that anchors a lens/region/theory cluster","kaleidoscope_anchor_piece",24),
 ("ordinary_candidate","Standard relevance candidate","normal_candidate|standard_candidate",24),
 ("surprise_candidate","Surfaced against expectation; boundary-learning signal","",24),
 ("resample_candidate","Previously sampled; queued for deeper/validated re-sample","",24),
 ("ocr_candidate","Unreadable/OCR-failed; queued pending reOCR or manual inspection","",24),
 ("manual_nomination","Human-nominated, not retrieval-surfaced","",24),
 ("openalex_candidate","Surfaced via OpenAlex enrichment (Stage 7)","",24),
 ("recoll_candidate","Surfaced via a Recoll retrieval cycle","",24),
]
cur.executemany("INSERT OR IGNORE INTO queue_candidate_type_taxonomy(candidate_type,meaning,synonyms,added_block) VALUES (?,?,?,?)", _CAND_TYPES)
_STATUSES = [
 ("queued","Recorded as retrieval clue; awaiting approval to sample",0,24),
 ("approved_for_sampling","User/governance approved rubric-governed sampling",0,24),
 ("sampling_in_progress","Sampling underway under a rubric version",0,24),
 ("sampled_pending_review","Sample taken; verdict awaiting human review",0,24),
 ("verified_sample_supported","Sample verified; thesis supported (evidence in verdict_disposition/claim)",0,24),
 ("rejected_after_sampling","Sampled and rejected",1,24),
 ("deferred","Parked; revisit later",0,24),
 ("duplicate","Duplicate of another queued candidate",1,24),
 ("closed","Queue item resolved/closed",1,24),
]
cur.executemany("INSERT OR IGNORE INTO queue_status_taxonomy(status,meaning,is_terminal,added_block) VALUES (?,?,?,?)", _STATUSES)

# Seed the controlled vocabulary so it is reproducible from a from-scratch build.
# INSERT OR IGNORE preserves any live-added rows and their original added_block.
_TAXONOMY = [
 ("core_candidate","SUPPORTED|PARTIAL","core_candidate",
  "Thesis accurate AND item belongs to Layer A/B/AB. Eligible for promotion.",14),
 ("claim_supported_but_project_irrelevant","SUPPORTED","excluded",
  "Thesis accurate but domain outside KNOWLEDGE_PRISM. Kept in master_corpus for provenance; excluded from core+ontology. NOT a contradiction.",14),
 ("excluded_misfile_noise","CONTRADICTED|ABSENT|UNCLEAR","excluded",
  "Forms/exams/fragments/admin docs, or content contradicting folder/path inference. Not scholarship; NOT a substantive contradiction.",14),
 ("excluded_unreadable","UNREADABLE","excluded",
  "OCR/extraction failure. Park pending reOCR/manual inspection; not excluded as noise unless later confirmed irrelevant.",14),
 ("review_required","CONTRADICTED|PARTIAL|any","review_required",
  "Below 0.75 gate, failed quote validation, ambiguous relevance, or genuine counter-argument. Human sign-off / re-sample required.",14),
 ("Peripheral_context","SUPPORTED|PARTIAL","peripheral",
  "Topic touches Layer A/B but genre is journalism/primary reportage/media, not scholarship. Empirical contextual material; not core, not ontology-promoted unless a later primary-source/media-evidence layer is created.",15),
]
cur.executemany(
 "INSERT OR IGNORE INTO disposition_taxonomy(disposition,axis1_thesis,axis2_corpus,meaning,added_block) VALUES (?,?,?,?,?)",
 _TAXONOMY)

# Seed scholar_input status controlled vocabulary (schema v0.2 freeze, block 26).
# INSERT OR IGNORE preserves any live-added rows and their original added_block.
# NOTE: approved_to_question is the MAXIMUM promotion status at this layer; there
# is no approved_to_evidence. Scholar input stays OUTSIDE the evidence chain.
_SI_STATUSES = [
 ("raw_captured",
  "Captured on the originating device (mobile/desktop); not yet imported to the desktop store. Not evidence.",26),
 ("imported_not_evidence",
  "Landed in the desktop holding store. Present for review; explicitly NOT evidence; not in verification_queue.",26),
 ("under_review",
  "Researcher is actively considering it. Still not evidence.",26),
 ("approved_to_question",
  "User approved it to SEED a research question / retrieval lens. Maximum promotion status at this layer; NOT direct entry to verification_queue, and there is no approved_to_evidence beyond it.",26),
 ("rejected_archived",
  "User rejected it. Preserved archival exclusion for audit; never deleted, never promoted.",26),
]
cur.executemany(
 "INSERT OR IGNORE INTO scholar_input_status_taxonomy(status,meaning,added_block) VALUES (?,?,?)",
 _SI_STATUSES)

# ---------------------------------------------------------------- DERIVED (rebuilt each run)
for t in ["master_corpus","zotero_register","bridge_concepts",
          "recoll_subject_folders","deepread_folders","solemon_crawl",
          "pub_eigenspace","intersection_seam","step2_corpus"]:
    cur.execute(f"DROP TABLE IF EXISTS {t}")

def load_generic(name, table, coltypes=None):
    hdr, rows = read_csv(name)
    if not hdr:
        print(f"  [skip] {name} (missing)"); return 0
    cols=[c.strip().replace(' ','_').replace('/','_').replace('-','_') or f"c{i}" for i,c in enumerate(hdr)]
    coldef=", ".join(f'"{c}" {((coltypes or {}).get(c,"TEXT"))}' for c in cols)
    cur.execute(f'CREATE TABLE {table} ({coldef})')
    ph=",".join("?"*len(cols))
    cur.executemany(f'INSERT INTO {table} VALUES ({ph})',
                    [r+['']*(len(cols)-len(r)) if len(r)<len(cols) else r[:len(cols)] for r in rows])
    src=os.path.join(STG,name)
    cur.execute("INSERT INTO source_registry VALUES (?,?,?,?,?)",
                (name, sha(src), len(rows), now(), table))
    print(f"  [load] {name} -> {table}: {len(rows)} rows")
    return len(rows)

print("Loading source tables...")
load_generic("MASTER_CORPUS_REGISTER_PRELIMINARY.csv","master_corpus",
             {"size_bytes":"INTEGER","size_mb":"REAL","duplicate_group_size":"INTEGER"})
load_generic("ZOTERO_REGISTER_PRELIMINARY.csv","zotero_register",{"year":"INTEGER"})
load_generic("BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv","bridge_concepts")
load_generic("recoll_subject_folders.csv","recoll_subject_folders",{"n":"INTEGER"})
load_generic("deepread_folders.csv","deepread_folders",{"n":"INTEGER"})
load_generic("solemon_crawl.csv","solemon_crawl",{"size":"INTEGER"})
load_generic("step2_corpus.csv","step2_corpus",{"year":"INTEGER","cites":"INTEGER"})
load_generic("intersection_seam.csv","intersection_seam",{"weight":"REAL"})

# pubs_tagged.json -> pub_eigenspace
pj=os.path.join(STG,"pubs_tagged.json")
if os.path.exists(pj):
    cur.execute("CREATE TABLE pub_eigenspace (title TEXT,venue TEXT,year INTEGER,cites INTEGER,w REAL,tags TEXT)")
    data=json.load(open(pj))
    cur.executemany("INSERT INTO pub_eigenspace VALUES (?,?,?,?,?,?)",
        [(d.get('title'),d.get('venue'),d.get('year'),d.get('cites'),d.get('w'),
          json.dumps(d.get('tags'))) for d in data])
    cur.execute("INSERT INTO source_registry VALUES (?,?,?,?,?)",
                ("pubs_tagged.json", sha(pj), len(data), now(), "pub_eigenspace"))
    print(f"  [load] pubs_tagged.json -> pub_eigenspace: {len(data)} rows")

con.commit()

# ---------------------------------------------------------------- indexes
cur.executescript("""
CREATE INDEX IF NOT EXISTS ix_mc_class ON master_corpus(corpus_class_preliminary);
CREATE INDEX IF NOT EXISTS ix_mc_grade ON master_corpus(evidence_grade);
CREATE INDEX IF NOT EXISTS ix_mc_dupe  ON master_corpus(dedupe_key);
CREATE INDEX IF NOT EXISTS ix_ce_claim ON claim_event(claim_id);
CREATE INDEX IF NOT EXISTS ix_ah_path  ON artifact_hash(path);
CREATE INDEX IF NOT EXISTS ix_sl_session ON session_log(session_id);
""")
con.commit()
print("Build complete:", DB)
con.close()
