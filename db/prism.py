#!/usr/bin/env python3
"""
KNOWLEDGE PRISM — session boot & query CLI.

At the START of any new session, run:   python3 db/prism.py boot
to restore ontology + fidelity (provenance chain, claims, retrievables).

Commands
--------
  boot          full restore briefing (chain status, blocks, ontology, claims, retrievables)
  verify        recompute & check the hash chain only
  blocks        list provenance blocks
  claims [S]    list claims (optional status filter: provisional|accepted|rejected)
  ontology      dump axes + top-weighted A×B nodes and seam edges
  retrievables  list registered deliverables + version ids
  facts         alias for accepted claims (the load-bearing assertions)
"""
import sys, os, sqlite3, json
sys.path.insert(0, os.path.dirname(__file__))
import prism_ledger as L

def con(): return sqlite3.connect(L.DB)

def _rule(t): print("\n"+"="*66+f"\n {t}\n"+"="*66)

def verify():
    ok,probs=L.verify_chain(con())
    print("CHAIN INTEGRITY:", "OK — every block hash recomputes and links" if ok else "BROKEN")
    for p in probs: print("  !",p)
    return ok

def blocks():
    _rule("PROVENANCE BLOCKS (hash-chained)")
    for no,bid,title,ts,actor,bh in con().execute(
        "SELECT block_no,block_id,title,ts,actor,block_hash FROM block ORDER BY block_no"):
        print(f"[{no}] {bid}  ({actor}, {ts[:10]})\n     {title}\n     hash={bh[:16]}…")

def claims(status=None):
    _rule(f"CLAIMS{' — '+status if status else ''}")
    q="""SELECT c.claim_id,c.claim_text,c.scope,c.evidence_grade,
         (SELECT to_status FROM claim_event e WHERE e.claim_id=c.claim_id ORDER BY rowid DESC LIMIT 1)
         FROM claim c ORDER BY c.claim_id"""
    for cid,txt,scope,grade,st in con().execute(q):
        if status and st!=status: continue
        print(f"{cid} [{st}/{grade}] ({scope})\n    {txt}")

def ontology():
    c=con()
    _rule("ONTOLOGY — 5 latent axes")
    for lab, in c.execute("SELECT label FROM ontology_node WHERE node_type='Axis' ORDER BY node_id"):
        print("  •",lab)
    _rule("TOP A×B SEAM EDGES (weighted intersection)")
    for a,b,w in c.execute("SELECT src,dst,weight FROM ontology_edge ORDER BY weight DESC LIMIT 12"):
        print(f"  {w:5.2f}  {a[2:]:28s} × {b[2:]}")

def retrievables():
    _rule("RETRIEVABLES (deliverables index)")
    for name,kind,vid,note in con().execute(
        "SELECT name,kind,artifact_version_id,note FROM retrievable ORDER BY kind,name"):
        v=f" v={vid}" if vid else ""
        print(f"  [{kind}] {name}{v}\n      {note}")

def boot():
    print("#"*66); print("#  KNOWLEDGE PRISM — SESSION RESTORE BRIEFING"); print("#"*66)
    c=con()
    nb=c.execute("SELECT COUNT(*) FROM block").fetchone()[0]
    nn=c.execute("SELECT COUNT(*) FROM ontology_node").fetchone()[0]
    ncl=c.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
    nmc=c.execute("SELECT COUNT(*) FROM master_corpus").fetchone()[0]
    print(f"\nDB: {L.DB}")
    print(f"scale: {nb} provenance blocks · {nn} ontology nodes · {ncl} claims · {nmc:,} corpus rows")
    verify(); blocks(); ontology()
    claims("accepted"); 
    _rule("OPEN QUESTIONS (provisional claims — need verification)")
    claims("provisional")
    retrievables()
    print("\n(For the newest session state, also read outputs/reports/step2_methodology.md.)")

if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "boot"
    arg=sys.argv[2] if len(sys.argv)>2 else None
    {"boot":boot,"verify":verify,"blocks":blocks,"ontology":ontology,
     "retrievables":retrievables,"claims":lambda:claims(arg),
     "facts":lambda:claims("accepted")}.get(cmd, boot)()
