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
  detail       TEXT
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
""")

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
