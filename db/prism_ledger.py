#!/usr/bin/env python3
"""
KNOWLEDGE PRISM — Proof-of-Provenance ledger library.

Blockchain PHILOSOPHY, not blockchain deployment: a local, hash-chained,
append-only audit ledger. Nothing is silently overwritten; every corpus object,
AI claim, classification, correction and output is a provenance-bearing
transaction.

Public API
----------
  con = connect()
  seal_block(con, block_id, title, session, actor, inputs, operations, outputs)
  register_claim(con, text, scope, source_file, grade, created_by, block_no, status)
  advance_claim(con, claim_id, event, to_status, basis, actor, block_no)
  hash_artifact(con, path, block_no, role)
  hash_tree(con, root, block_no, role)     # fingerprint many files
  verify_chain(con)                         # returns (ok, [problems])
  add_retrievable(con, name, kind, disk_path, artifact_version_id, session, note)

Also writes a JSON mirror of each sealed block to ledger/blocks/ for the
file-based ledger the project brief specifies.
"""
import sqlite3, os, json, hashlib, datetime

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
DB=os.path.join(ROOT,"db","knowledge_prism.db")
BLOCKS_DIR=os.path.join(ROOT,"ledger","blocks")
GENESIS_PREV="0"*64

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def _h(s): return hashlib.sha256(s.encode()).hexdigest()

def connect(): 
    con=sqlite3.connect(DB); con.execute("PRAGMA journal_mode=WAL"); return con

def sha_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(65536),b''): h.update(c)
    return h.hexdigest()

# ---------------------------------------------------------------- BLOCKS
def _next_block_no(con):
    r=con.execute("SELECT MAX(block_no) FROM block").fetchone()[0]
    return 0 if r is None else r+1

def _prev_hash(con, block_no):
    if block_no==0: return GENESIS_PREV
    r=con.execute("SELECT block_hash FROM block WHERE block_no=?",(block_no-1,)).fetchone()
    return r[0] if r else GENESIS_PREV

def seal_block(con, block_id, title, session, actor, inputs, operations, outputs, ts=None):
    """Seal a batch of work as a hash-linked block. Idempotent on block_id."""
    ex=con.execute("SELECT block_no FROM block WHERE block_id=?",(block_id,)).fetchone()
    if ex: return ex[0]
    no=_next_block_no(con); ts=ts or now(); prev=_prev_hash(con,no)
    payload=json.dumps({"inputs":inputs,"operations":operations,"outputs":outputs},sort_keys=True)
    bhash=_h(f"{no}|{prev}|{payload}|{ts}")
    con.execute("INSERT INTO block VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (no,block_id,title,ts,session,actor,json.dumps(inputs),
         json.dumps(operations),json.dumps(outputs),prev,bhash))
    con.commit()
    os.makedirs(BLOCKS_DIR,exist_ok=True)
    with open(os.path.join(BLOCKS_DIR,f"{block_id}.json"),"w") as f:
        json.dump({"block_no":no,"block_id":block_id,"title":title,"ts":ts,
                   "session_id":session,"actor":actor,"inputs":inputs,
                   "operations":operations,"outputs":outputs,
                   "prev_hash":prev,"block_hash":bhash},f,indent=2)
    return no

def verify_chain(con):
    """Recompute every block hash and confirm prev_hash linkage. Detect tampering."""
    rows=con.execute("""SELECT block_no,ts,inputs,operations,outputs,prev_hash,block_hash
                        FROM block ORDER BY block_no""").fetchall()
    problems=[]; expect_prev=GENESIS_PREV
    for no,ts,i,o,ou,prev,bh in rows:
        payload=json.dumps({"inputs":json.loads(i),"operations":json.loads(o),
                            "outputs":json.loads(ou)},sort_keys=True)
        recomputed=_h(f"{no}|{prev}|{payload}|{ts}")
        if recomputed!=bh: problems.append(f"block {no}: hash mismatch (tampered payload)")
        if prev!=expect_prev: problems.append(f"block {no}: broken chain link")
        expect_prev=bh
    return (len(problems)==0, problems)

# ---------------------------------------------------------------- CLAIMS (transactions)
def _next_claim_id(con):
    r=con.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
    return f"KP-CLAIM-{r+1:06d}"

def register_claim(con, text, scope, source_file, grade, created_by, block_no, status="provisional"):
    """Introduce a claim as a transaction. De-dup by (text,scope)."""
    ex=con.execute("SELECT claim_id FROM claim WHERE claim_text=? AND scope=?",(text,scope)).fetchone()
    if ex: return ex[0]
    cid=_next_claim_id(con); ts=now()
    con.execute("INSERT INTO claim VALUES (?,?,?,?,?,?,?,?,?)",
        (cid,text,scope,source_file,grade,created_by,ts,block_no,status))
    con.execute("INSERT INTO claim_event VALUES (?,?,?,?,?,?,?,?)",
        (cid,ts,"created",None,status,f"grade={grade}",created_by,block_no))
    con.commit(); return cid

def advance_claim(con, claim_id, event, to_status, basis, actor, block_no):
    """Append a lifecycle event (verified/corrected/rejected/superseded). Never overwrites."""
    cur=con.execute("""SELECT to_status FROM claim_event WHERE claim_id=?
                       ORDER BY rowid DESC LIMIT 1""",(claim_id,)).fetchone()
    frm=cur[0] if cur else None
    con.execute("INSERT INTO claim_event VALUES (?,?,?,?,?,?,?,?)",
        (claim_id,now(),event,frm,to_status,basis,actor,block_no))
    con.commit()

def claim_status(con, claim_id):
    r=con.execute("""SELECT to_status FROM claim_event WHERE claim_id=?
                     ORDER BY rowid DESC LIMIT 1""",(claim_id,)).fetchone()
    return r[0] if r else None

# ---------------------------------------------------------------- ARTIFACT HASHING
def hash_artifact(con, path, block_no, role):
    """Append a fingerprint ONLY when the file's hash differs from its last
    recorded hash (change-only log). Unchanged files are not re-recorded."""
    if not os.path.exists(path): return None
    rel=os.path.relpath(path,ROOT); sh=sha_file(path); sz=os.path.getsize(path)
    last=con.execute("""SELECT sha256 FROM artifact_hash WHERE path=?
                        ORDER BY rowid DESC LIMIT 1""",(rel,)).fetchone()
    if last and last[0]==sh: return sh   # unchanged -> no new row
    con.execute("INSERT INTO artifact_hash VALUES (?,?,?,?,?,?)",
        (rel,sh,sz,now(),block_no,role))
    con.commit(); return sh

def hash_tree(con, root, block_no, role, exts=None):
    # The live DB and its WAL/SHM sidecars cannot have a stable self-hash
    # (they mutate as we write), so they are excluded from the fingerprint log.
    skip={"knowledge_prism.db","knowledge_prism.db-wal","knowledge_prism.db-shm"}
    n=0
    for dp,_,fs in os.walk(root):
        if "/db/_staging" in dp or "/.git" in dp: continue
        for fn in fs:
            if fn in skip: continue
            if exts and not any(fn.endswith(e) for e in exts): continue
            if hash_artifact(con,os.path.join(dp,fn),block_no,role): n+=1
    return n

# ---------------------------------------------------------------- RETRIEVABLES
def add_retrievable(con, name, kind, disk_path, artifact_version_id, session, note=""):
    sh=sha_file(disk_path) if disk_path and os.path.exists(disk_path) else None
    con.execute("INSERT INTO retrievable VALUES (?,?,?,?,?,?,?,?)",
        (name,kind,disk_path,artifact_version_id,session,now(),sh,note))
    con.commit()
