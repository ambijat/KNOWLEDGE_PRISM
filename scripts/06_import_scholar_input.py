#!/usr/bin/env python3
"""KNOWLEDGE_PRISM scholar-input desktop JSON importer (schema v0.2).

DOCTRINE — scholar input is NOT evidence. This importer lands validated JSON
records into the persistent `scholar_input` table at status `imported_not_evidence`
ONLY. It never creates a claim, disposition, functional role, verified concept,
ontology node, or verification_queue document, and never seals an evidence block.

The epistemic sequence it must never bypass:
  scholar_input -> approved_to_question -> research question / retrieval lens
  -> retrieval -> verification_queue of real documents -> sampling -> evidence
Approval-to-question is a SEPARATE governed act and is NOT implemented here.

Interface:
  python3 scripts/06_import_scholar_input.py --input <file-or-dir> [--dry-run|--commit] [--recursive]
  --dry-run   (DEFAULT, safe)  validate + report only, no DB write
  --commit                     validate whole batch, then insert in ONE transaction
  --recursive                  only with a directory input; opt-in subdir descent

Writes ONLY to scholar_input. Reads scholar_input_status_taxonomy. Touches no
research-state table.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, sqlite3, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB   = ROOT / "db" / "knowledge_prism.db"

SCHEMA_VERSION = "0.2"
RECORD_TYPE    = "scholar_input_not_evidence"
INSERT_STATUS  = "imported_not_evidence"     # forced on every inserted row
SOURCES        = {"android_app", "desktop_manual", "desktop_import"}
# Statuses acceptable AS SOURCE INPUT (pre-import). approved_to_question /
# rejected_archived are governed transitions, not import states; approved_to_evidence
# never exists. All accepted inputs are forced to imported_not_evidence on write.
ACCEPTABLE_SOURCE_STATUSES = {"raw_captured", "imported_not_evidence", "under_review", None, ""}
FORBIDDEN_STATUSES = {"approved_to_question", "rejected_archived", "approved_to_evidence"}
FROZEN_ORGANS = {
    "Title","Background","Statement_of_Problem","Research_Gap","Research_Questions",
    "Objectives","Scope","Methodology","Conceptual_Framework","Literature_Clusters",
    "Evidence_Needs","Case_Region_Time_Period","Chapterisation","Supervisor_Questions",
    "Revision_Tasks","Unassigned",
}
# Governance fields the importer must NEVER accept from JSON; forced NULL on insert.
GOVERNANCE_FIELDS = ["became_question","became_queue_id","decided_by","decided_ts",
                     "rejection_reason","block_no"]
# Columns actually written (26-col schema). status/imported_ts/content_sha256 handled explicitly.
COPY_FIELDS = ["schema_version","record_type","source","captured_ts","idea",
               "draft_organ","draft_diagnosis","draft_search_plan","supervisor_brief",
               "raw_notes","voice_transcript","tags","confidence","project_title",
               "course_or_context"]

# ---- canonical content hash --------------------------------------------------
# Canonicalisation (MUST match gui/services/scholar_input_schema.py.canonical_content
# so a hash computed in the GUI and in the backend agree):
#   * Fields hashed, in fixed order: idea, raw_notes, voice_transcript.
#   * Each absent-or-null field -> empty string (absent and null treated identically).
#   * Fields joined by a single '\n'.
#   * Unicode NFC-normalised, encoded UTF-8, sha256 hex (lowercase).
#   * Governance/db-generated fields (scholar_id, imported_ts, content_sha256,
#     status, all GOVERNANCE_FIELDS) are EXCLUDED from the hash.
HASH_FIELDS = ["idea", "raw_notes", "voice_transcript"]
def canonical_content(rec: dict) -> str:
    return "\n".join(str(rec.get(f) or "") for f in HASH_FIELDS)
def content_sha256(rec: dict) -> str:
    canon = unicodedata.normalize("NFC", canonical_content(rec))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()

def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

# ---- record loading ----------------------------------------------------------
def load_records(path: Path, recursive: bool):
    """Yield (source_file_relpath, record_index, record_or_None, load_error)."""
    files = []
    if path.is_dir():
        it = path.rglob("*.json") if recursive else path.glob("*.json")
        files = sorted(p for p in it if p.is_file())
    elif path.is_file():
        if path.suffix.lower() != ".json":
            yield (path.name, 0, None, "not a .json file"); return
        files = [path]
    else:
        yield (str(path), 0, None, "path does not exist"); return
    for f in files:
        rel = f.name if path.is_file() else str(f.relative_to(path))
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            yield (rel, 0, None, f"JSON parse error: {e}"); continue
        # single record (dict) or multi-record (list of dicts)
        if isinstance(data, dict):
            yield (rel, 0, data, None)
        elif isinstance(data, list):
            for i, r in enumerate(data):
                if isinstance(r, dict):
                    yield (rel, i, r, None)
                else:
                    yield (rel, i, None, "list element is not an object")
        else:
            yield (rel, 0, None, "top-level JSON is neither object nor array")

# ---- validation --------------------------------------------------------------
def validate(rec: dict) -> list[str]:
    errs = []
    if rec.get("schema_version") != SCHEMA_VERSION:
        errs.append(f"schema_version != {SCHEMA_VERSION} (got {rec.get('schema_version')!r})")
    if rec.get("record_type") != RECORD_TYPE:
        errs.append(f"record_type != {RECORD_TYPE} (got {rec.get('record_type')!r})")
    if rec.get("source") not in SOURCES:
        errs.append(f"source not in {sorted(SOURCES)} (got {rec.get('source')!r})")
    if not str(rec.get("idea") or "").strip():
        errs.append("idea is empty or missing")
    cts = rec.get("captured_ts")
    if not cts:
        errs.append("captured_ts missing")
    else:
        try:
            dt.datetime.fromisoformat(str(cts).replace("Z", "+00:00"))
        except Exception:
            errs.append(f"captured_ts not valid ISO-8601 (got {cts!r})")
    organ = rec.get("draft_organ")
    if organ not in (None, "") and organ not in FROZEN_ORGANS:
        errs.append(f"draft_organ not in frozen 16-organ vocab (got {organ!r})")
    st = rec.get("status")
    if st in FORBIDDEN_STATUSES:
        errs.append(f"status {st!r} is not an acceptable import status "
                    f"(approval/rejection/evidence are governed acts, not imports)")
    elif st not in ACCEPTABLE_SOURCE_STATUSES:
        errs.append(f"status {st!r} unrecognised for import")
    # governance fields must be absent/null in the incoming JSON
    for gf in GOVERNANCE_FIELDS:
        if rec.get(gf) not in (None, ""):
            errs.append(f"governance field {gf!r} must be null on import (got {rec.get(gf)!r})")
    return errs

# ---- id allocation -----------------------------------------------------------
def max_si_number(cur) -> int:
    """Highest numeric suffix among well-formed KP-SI-###### ids; gap-safe (max, not count)."""
    hi = 0
    for (sid,) in cur.execute("SELECT scholar_id FROM scholar_input WHERE scholar_id LIKE 'KP-SI-%'"):
        tail = str(sid).split("KP-SI-")[-1]
        if tail.isdigit():
            hi = max(hi, int(tail))
    return hi

def fmt_si(n: int) -> str:
    return f"KP-SI-{n:06d}"

# ---- main --------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Scholar-input desktop JSON importer (v0.2). Dry-run is default.")
    ap.add_argument("--input", required=True, help="a .json file or a directory of .json files")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="validate + report only (DEFAULT)")
    g.add_argument("--commit", action="store_true", help="insert eligible records in one transaction")
    ap.add_argument("--recursive", action="store_true", help="descend subdirectories (directory input only)")
    ap.add_argument("--db", default=str(DB), help="database path (for test copies)")
    args = ap.parse_args()
    commit = bool(args.commit)          # dry-run is the safe default
    path = Path(args.input)

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    # importer reads the taxonomy but never writes it
    tax = {r[0] for r in cur.execute("SELECT status FROM scholar_input_status_taxonomy")}
    assert INSERT_STATUS in tax, f"taxonomy missing {INSERT_STATUS}; run build_prism_db.py first"

    existing_hashes = {r[0] for r in cur.execute(
        "SELECT content_sha256 FROM scholar_input WHERE content_sha256 IS NOT NULL")}

    files_seen, valid, invalid, dup = set(), [], [], []
    batch_hashes = {}   # hash -> first (file,idx) within this batch (intra-batch dedupe)
    order = []
    for rel, idx, rec, load_err in load_records(path, args.recursive):
        files_seen.add(rel)
        tag = f"{rel}#{idx}"
        if load_err:
            invalid.append((tag, [load_err])); continue
        errs = validate(rec)
        if errs:
            invalid.append((tag, errs)); continue
        h = content_sha256(rec)
        if h in existing_hashes:
            dup.append((tag, h, "existing_row")); continue
        if h in batch_hashes:
            dup.append((tag, h, f"same-as {batch_hashes[h]}")); continue
        batch_hashes[h] = tag
        valid.append((tag, rec, h)); order.append(tag)

    # proposed ids (dry-run preview + commit allocation both use gap-safe max+1)
    start = max_si_number(cur) + 1
    proposed = {tag: fmt_si(start + i) for i, (tag, _, _) in enumerate(valid)}

    def rpt():
        print("=== SCHOLAR-INPUT IMPORT REPORT ===")
        print(f"mode: {'COMMIT' if commit else 'DRY-RUN (default, no write)'}")
        print(f"input: {path.name}{'/' if path.is_dir() else ''}  recursive={args.recursive}")
        print(f"files discovered:   {len(files_seen)}")
        print(f"records discovered: {len(valid)+len(invalid)+len(dup)}")
        print(f"records valid:      {len(valid)}")
        print(f"records invalid:    {len(invalid)}")
        print(f"records duplicate:  {len(dup)}")
        print(f"records eligible for insertion: {len(valid)}")
        if valid:
            print("proposed KP-SI identifiers:")
            for tag, _, h in valid:
                print(f"  {proposed[tag]}  <- {tag}  sha={h[:12]}…")
        if dup:
            print("duplicates (skipped):")
            for tag, h, why in dup:
                print(f"  {tag}  sha={h[:12]}…  {why}")
        if invalid:
            print("validation errors:")
            for tag, errs in invalid:
                for e in errs:
                    print(f"  {tag}: {e}")

    if not commit:
        rpt()
        print("no database changes (dry-run).")
        con.close(); return 0

    # COMMIT: whole-batch gate — if any record is invalid, refuse the batch.
    if invalid:
        rpt()
        print("COMMIT REFUSED: batch contains invalid records; fix or split the batch. No rows written.")
        con.close(); return 2
    if not valid:
        rpt()
        print("nothing eligible to insert; no rows written.")
        con.close(); return 0

    imported_ts = now_iso()
    inserted = []
    try:
        cur.execute("BEGIN")
        n = max_si_number(cur) + 1          # allocate inside the transaction
        for tag, rec, h in valid:
            sid = fmt_si(n); n += 1
            row = {k: rec.get(k) for k in COPY_FIELDS}
            row["scholar_id"]     = sid
            row["status"]         = INSERT_STATUS      # FORCED
            row["imported_ts"]    = imported_ts
            row["content_sha256"] = h
            for gf in GOVERNANCE_FIELDS:               # FORCED NULL
                row[gf] = None
            cols = (["scholar_id","schema_version","record_type","source","captured_ts",
                     "imported_ts","idea","draft_organ","draft_diagnosis","draft_search_plan",
                     "supervisor_brief","raw_notes","voice_transcript","tags","confidence",
                     "project_title","course_or_context","status","content_sha256"]
                    + GOVERNANCE_FIELDS)
            ph = ",".join("?" for _ in cols)
            cur.execute(f"INSERT INTO scholar_input({','.join(cols)}) VALUES ({ph})",
                        [row.get(c) for c in cols])
            inserted.append((sid, tag, h))
        con.commit()
    except Exception as e:
        con.rollback()
        print(f"COMMIT FAILED — transaction rolled back, no rows written: {e}")
        con.close(); return 3

    print("=== SCHOLAR-INPUT COMMIT REPORT ===")
    print(f"records inserted:  {len(inserted)}")
    print(f"records skipped as duplicates: {len(dup)}")
    print(f"records rejected:  {len(invalid)}")
    print("assigned scholar IDs:")
    for sid, tag, h in inserted:
        print(f"  {sid}  <- {tag}  sha={h[:12]}…")
    print(f"final status (every row): {INSERT_STATUS}")
    print(f"imported_ts: {imported_ts}")
    print("forced-null governance fields: became_question, became_queue_id, decided_by, decided_ts, rejection_reason, block_no")
    print("transaction result: COMMITTED")
    con.close(); return 0

if __name__ == "__main__":
    sys.exit(main())
