#!/usr/bin/env python3
"""KNOWLEDGE_PRISM scholar-input governed state-transition CLI (block 28).

DOCTRINE — the only valid epistemic sequence is:
  scholar_input -> approved_to_question -> research question / retrieval lens
  -> retrieval -> verification_queue of real documents -> sampling -> evidence
This tool implements ONLY the segment that STOPS at approved_to_question. It
never retrieves, never writes verification_queue, never creates evidence,
claims, dispositions, functional roles, verified concepts, or ontology.

Three governed transitions:
  start-review        imported_not_evidence -> under_review
  approve-to-question under_review         -> approved_to_question  (+ 1 research_question seed row)
  reject              under_review         -> rejected_archived

Writes ONLY to `scholar_input` and its governed destination `research_question`.
Dry-run by default; --commit performs one atomic transaction.

Interface:
  python3 scripts/07_transition_scholar_input.py --db <db> --scholar-id KP-SI-000001 \
      --action start-review|approve-to-question|reject --decided-by <actor> [--commit]
  approve-to-question: --question-text <text>  (or --question-file <path>)
                       [--lens-type research_question|retrieval_lens]
  reject:              --rejection-reason <text>

No SQL fragments are accepted; no shell interpolation is used (argparse only).
"""
from __future__ import annotations
import argparse, datetime as dt, os, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB   = ROOT / "db" / "knowledge_prism.db"
sys.path.insert(0, str(ROOT / "db"))

# ---- controlled vocab (must match scholar_input_status_taxonomy, block 26) ---
S_IMPORTED   = "imported_not_evidence"
S_UNDER      = "under_review"
S_APPROVED   = "approved_to_question"
S_REJECTED   = "rejected_archived"
LENS_TYPES   = {"research_question", "retrieval_lens"}
RQ_STATUS    = "approved_seed"        # max status of a question at this layer (no retrieval yet)

# Allowed transitions: action -> (required_from_status, resulting_status)
TRANSITIONS = {
    "start-review":        (S_IMPORTED, S_UNDER),
    "approve-to-question": (S_UNDER,    S_APPROVED),
    "reject":              (S_UNDER,    S_REJECTED),
}

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def next_rq_id(cur) -> str:
    """Gap-safe max+1 over KP-RQ-###### ids (never row count)."""
    hi = 0
    for (qid,) in cur.execute("SELECT question_id FROM research_question WHERE question_id LIKE 'KP-RQ-%'"):
        tail = str(qid).split("KP-RQ-")[-1]
        if tail.isdigit():
            hi = max(hi, int(tail))
    return f"KP-RQ-{hi+1:06d}"

# ---- validation (pre-transaction, argument-level) ----------------------------
def validate_args(a) -> list[str]:
    errs = []
    if not a.scholar_id or not str(a.scholar_id).startswith("KP-SI-"):
        errs.append("--scholar-id must be a KP-SI-###### id")
    if not a.decided_by or not a.decided_by.strip():
        errs.append("--decided-by (actor) is required and must be non-empty")
    if a.action == "approve-to-question":
        text = read_question_text(a)
        if text is None:
            errs.append("approve-to-question requires --question-text or --question-file")
        elif not text.strip():
            errs.append("approve-to-question requires NON-EMPTY research-question / retrieval-lens text")
        if a.lens_type not in LENS_TYPES:
            errs.append(f"--lens-type must be one of {sorted(LENS_TYPES)}")
    if a.action == "reject":
        if a.rejection_reason is None or not a.rejection_reason.strip():
            errs.append("reject requires a NON-EMPTY --rejection-reason")
    # Caller must never pre-populate backend-controlled fields (they are not even CLI args;
    # this guard exists so a future caller extension cannot smuggle them in).
    for f in ("became_question", "became_queue_id", "block_no"):
        if getattr(a, f, None) is not None:
            errs.append(f"caller may not supply backend-controlled field {f}")
    return errs

def read_question_text(a):
    if getattr(a, "question_file", None):
        return Path(a.question_file).read_text(encoding="utf-8")
    return a.question_text

# ---- the transition (single transaction) ------------------------------------
def do_transition(con, a, commit: bool) -> dict:
    cur = con.cursor()
    required_from, result_status = TRANSITIONS[a.action]
    # BEGIN one transaction; re-read status INSIDE it.
    cur.execute("BEGIN IMMEDIATE")
    try:
        row = cur.execute(
            "SELECT status, became_question FROM scholar_input WHERE scholar_id=?",
            (a.scholar_id,)).fetchone()
        if row is None:
            raise Refuse(f"scholar_id {a.scholar_id} not found")
        cur_status, cur_became_q = row

        # Idempotent already-approved result (repeat approval must not duplicate).
        if a.action == "approve-to-question" and cur_status == S_APPROVED:
            existing = cur.execute(
                "SELECT question_id FROM research_question WHERE origin_scholar_id=?",
                (a.scholar_id,)).fetchone()
            con.rollback()
            return {"status": "already_approved", "scholar_id": a.scholar_id,
                    "question_id": existing[0] if existing else cur_became_q,
                    "note": "no new question created (idempotent)"}

        if cur_status != required_from:
            raise Refuse(f"illegal transition: status is '{cur_status}', "
                         f"'{a.action}' requires '{required_from}'")

        ts = now()
        result = {"status": "ok", "action": a.action, "scholar_id": a.scholar_id,
                  "from": cur_status, "to": result_status, "ts": ts}

        if a.action == "start-review":
            cur.execute("UPDATE scholar_input SET status=?, decided_by=?, decided_ts=? "
                        "WHERE scholar_id=? AND status=?",
                        (S_UNDER, a.decided_by, ts, a.scholar_id, required_from))

        elif a.action == "approve-to-question":
            # guard: one scholar_input -> at most one question (UNIQUE also enforces at DB level)
            dup = cur.execute("SELECT question_id FROM research_question WHERE origin_scholar_id=?",
                              (a.scholar_id,)).fetchone()
            if dup:
                raise Refuse(f"destination question {dup[0]} already exists for {a.scholar_id}")
            qid = next_rq_id(cur)
            qtext = read_question_text(a)
            cur.execute(
                "INSERT INTO research_question(question_id,question_text,lens_type,"
                "origin_scholar_id,status,created_by,created_ts,block_no) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (qid, qtext, a.lens_type, a.scholar_id, RQ_STATUS, a.decided_by, ts, a.block_seal))
            cur.execute(
                "UPDATE scholar_input SET status=?, became_question=?, decided_by=?, "
                "decided_ts=?, rejection_reason=NULL WHERE scholar_id=? AND status=?",
                (S_APPROVED, qid, a.decided_by, ts, a.scholar_id, required_from))
            result["question_id"] = qid

        elif a.action == "reject":
            cur.execute(
                "UPDATE scholar_input SET status=?, decided_by=?, decided_ts=?, "
                "rejection_reason=?, became_question=NULL WHERE scholar_id=? AND status=?",
                (S_REJECTED, a.decided_by, ts, a.rejection_reason, a.scholar_id, required_from))

        if cur.rowcount != 1:
            raise Refuse("row status changed concurrently; refusing (0 rows updated)")

        if commit:
            con.commit()
            result["committed"] = True
        else:
            con.rollback()
            result["committed"] = False
            result["note"] = "dry-run: rolled back, no database changes"
        return result
    except Exception:
        con.rollback()
        raise

class Refuse(Exception):
    pass

def build_parser():
    p = argparse.ArgumentParser(description="Governed scholar_input state transition (stops at approved_to_question).")
    p.add_argument("--db", default=str(DB))
    p.add_argument("--scholar-id", required=True)
    p.add_argument("--action", required=True, choices=list(TRANSITIONS))
    p.add_argument("--decided-by", required=True)
    p.add_argument("--question-text")
    p.add_argument("--question-file")
    p.add_argument("--lens-type", default="research_question")
    p.add_argument("--rejection-reason")
    p.add_argument("--block-seal", type=int, default=None,
                   help="block_no to stamp on new rows (set by the governed seal step; default NULL)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--commit", dest="commit", action="store_true", default=False)
    # backend-controlled fields are intentionally NOT exposed as args; placeholders for the guard:
    p.set_defaults(became_question=None, became_queue_id=None, block_no=None)
    return p

def main(argv=None):
    a = build_parser().parse_args(argv)
    errs = validate_args(a)
    if errs:
        print("TRANSITION REFUSED:")
        for e in errs:
            print("  -", e)
        return 2
    con = sqlite3.connect(a.db)
    con.execute("PRAGMA foreign_keys=ON")
    try:
        res = do_transition(con, a, commit=a.commit)
    except Refuse as r:
        print("TRANSITION REFUSED:", r)
        return 2
    finally:
        con.close()
    import json as _j
    print(_j.dumps(res, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
