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
                                             [--output-format text|json] [--ack-file <path>]
  --dry-run        (DEFAULT, safe)  validate + report only, no DB write
  --commit                          validate whole batch, then insert in ONE transaction
  --recursive                       only with a directory input; opt-in subdir descent
  --output-format  text (DEFAULT) prints the human-readable report; json prints a
                   single machine-readable acknowledgement batch object to stdout
  --ack-file       optional path; writes the acknowledgement batch object as JSON
                   (independent of --output-format)

Writes ONLY to scholar_input. Reads scholar_input_status_taxonomy. Touches no
research-state table.

OUTPUT-ONLY ENHANCEMENT (2026-07, import-acknowledgement cycle): this revision
adds a stable structured acknowledgement so browser/Android capture clients can
learn each record's fate. The per-record `acks[]` entry carries the contract §11
fields {client_record_id, result, backend_scholar_id, content_sha256, message}
plus one machine-readable `error_code` (null on success). `result` is the closed
enum: eligible | imported | duplicate_skipped | invalid | batch_refused |
transport_failed.

Acknowledgement contract v0.1.1 (supervisor-authorised, 2026-07):
  - a valid record under --dry-run emits result="eligible" (it would be inserted
    on --commit); batch-level transaction_result=DRY_RUN stays the authoritative
    "nothing written" signal;
  - an exact content-hash duplicate of an already-committed row echoes that row's
    existing KP-SI id in backend_scholar_id (an intra-batch duplicate, whose first
    copy is only being inserted this run, keeps backend_scholar_id=null);
  - ack_schema_version = exchange_contract_version = "0.1.1".
Per §11, `message` never carries paths, SQL, or submitted idea-content.

It changes IMPORT OUTPUT BEHAVIOUR ONLY. The scholar_input payload schema is
UNCHANGED at 0.2 and remains fully compatible with existing Android/browser v0.1
exports. Validation decisions, canonical-hash rule, duplicate DETECTION and
hashing, KP-SI id allocation, batch atomicity, forced-status and forced-null
governance fields, and every return code are unchanged; the default
--output-format text report is byte-for-byte identical to the prior behaviour.
Error codes are taken verbatim from the Android exchange contract §15; where the
importer validates something the table has no code for (captured_ts, load/parse
failures) error_code is left null rather than inventing one.
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

# ---- acknowledgement contract (Android exchange contract v0.1.1) -------------
# v0.1.1 (2026-07, supervisor-authorised): dry-run valid records emit
# result="eligible"; exact content-hash duplicates echo the existing KP-SI id.
# The scholar_input payload schema is UNCHANGED at 0.2 and remains fully
# compatible with existing Android/browser v0.1 exports.
ACK_SCHEMA_VERSION        = "0.1.1"   # acknowledgement envelope version
EXCHANGE_CONTRACT_VERSION = "0.1.1"   # Android exchange contract version
# Frozen §15 error codes. Keys are stable; the importer emits ONLY these codes.
# A validation failure with no matching frozen code carries error_code = None
# (documented gap: captured_ts and load/parse failures have no §15 code).
ERR_INVALID_SCHEMA_VERSION = "INVALID_SCHEMA_VERSION"
ERR_INVALID_RECORD_TYPE    = "INVALID_RECORD_TYPE"
ERR_INVALID_SOURCE         = "INVALID_SOURCE"
ERR_INVALID_STATUS         = "INVALID_STATUS"
ERR_EMPTY_IDEA             = "EMPTY_IDEA"
ERR_INVALID_DRAFT_ORGAN    = "INVALID_DRAFT_ORGAN"
ERR_FORBIDDEN_GOV_FIELD    = "FORBIDDEN_GOVERNANCE_FIELD"
ERR_DUPLICATE_CONTENT      = "DUPLICATE_CONTENT"
ERR_BATCH_ATOMIC_REFUSAL   = "BATCH_ATOMIC_REFUSAL"

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
    """Backward-compatible: return the list of human-readable error messages.

    Message strings are unchanged from the prior importer so the text report is
    byte-for-byte identical. Frozen §15 error codes are exposed separately via
    validate_coded(); this wrapper simply drops the codes.
    """
    return [msg for _code, msg in validate_coded(rec)]

def validate_coded(rec: dict) -> list[tuple[str | None, str]]:
    """Return [(error_code_or_None, message), ...]. Codes are the frozen §15
    vocabulary; None where the contract table has no code for that check."""
    errs: list[tuple[str | None, str]] = []
    if rec.get("schema_version") != SCHEMA_VERSION:
        errs.append((ERR_INVALID_SCHEMA_VERSION,
                     f"schema_version != {SCHEMA_VERSION} (got {rec.get('schema_version')!r})"))
    if rec.get("record_type") != RECORD_TYPE:
        errs.append((ERR_INVALID_RECORD_TYPE,
                     f"record_type != {RECORD_TYPE} (got {rec.get('record_type')!r})"))
    if rec.get("source") not in SOURCES:
        errs.append((ERR_INVALID_SOURCE,
                     f"source not in {sorted(SOURCES)} (got {rec.get('source')!r})"))
    if not str(rec.get("idea") or "").strip():
        errs.append((ERR_EMPTY_IDEA, "idea is empty or missing"))
    cts = rec.get("captured_ts")
    if not cts:
        errs.append((None, "captured_ts missing"))   # no frozen §15 code
    else:
        try:
            dt.datetime.fromisoformat(str(cts).replace("Z", "+00:00"))
        except Exception:
            errs.append((None, f"captured_ts not valid ISO-8601 (got {cts!r})"))
    organ = rec.get("draft_organ")
    if organ not in (None, "") and organ not in FROZEN_ORGANS:
        errs.append((ERR_INVALID_DRAFT_ORGAN,
                     f"draft_organ not in frozen 16-organ vocab (got {organ!r})"))
    st = rec.get("status")
    if st in FORBIDDEN_STATUSES:
        errs.append((ERR_INVALID_STATUS,
                     f"status {st!r} is not an acceptable import status "
                     f"(approval/rejection/evidence are governed acts, not imports)"))
    elif st not in ACCEPTABLE_SOURCE_STATUSES:
        errs.append((ERR_INVALID_STATUS, f"status {st!r} unrecognised for import"))
    # governance fields must be absent/null in the incoming JSON
    for gf in GOVERNANCE_FIELDS:
        if rec.get(gf) not in (None, ""):
            errs.append((ERR_FORBIDDEN_GOV_FIELD,
                         f"governance field {gf!r} must be null on import (got {rec.get(gf)!r})"))
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
    ap.add_argument("--output-format", choices=["text", "json"], default="text",
                    help="text (DEFAULT) human-readable report; json prints one ack batch object")
    ap.add_argument("--ack-file", default=None,
                    help="optional path to write the acknowledgement batch object as JSON")
    args = ap.parse_args()
    commit = bool(args.commit)          # dry-run is the safe default
    path = Path(args.input)

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    # importer reads the taxonomy but never writes it
    tax = {r[0] for r in cur.execute("SELECT status FROM scholar_input_status_taxonomy")}
    assert INSERT_STATUS in tax, f"taxonomy missing {INSERT_STATUS}; run build_prism_db.py first"

    # hash -> existing KP-SI id (v0.1.1 echoes the existing id for duplicates)
    existing_by_hash = {r[0]: r[1] for r in cur.execute(
        "SELECT content_sha256, scholar_id FROM scholar_input WHERE content_sha256 IS NOT NULL")}
    existing_hashes = set(existing_by_hash)

    files_seen, valid, invalid, dup = set(), [], [], []
    batch_hashes = {}   # hash -> first (file,idx) within this batch (intra-batch dedupe)
    order = []
    entries = []            # parallel per-record ack scaffold, in discovery order
    seen_batch_ids = set()  # export_batch_id values across records (for batch_id resolution)
    for rel, idx, rec, load_err in load_records(path, args.recursive):
        files_seen.add(rel)
        tag = f"{rel}#{idx}"
        crid = rec.get("client_record_id") if isinstance(rec, dict) else None
        if isinstance(rec, dict) and rec.get("export_batch_id"):
            seen_batch_ids.add(str(rec.get("export_batch_id")))
        if load_err:
            invalid.append((tag, [load_err]))
            entries.append({"tag": tag, "record_index": idx, "source": rel,
                            "client_record_id": crid, "category": "invalid",
                            "error_code": None, "message": load_err,
                            "content_sha256": None})
            continue
        coded = validate_coded(rec)
        if coded:
            errs = [m for _c, m in coded]
            invalid.append((tag, errs))
            first_code, first_msg = coded[0]
            entries.append({"tag": tag, "record_index": idx, "source": rel,
                            "client_record_id": crid, "category": "invalid",
                            "error_code": first_code, "message": first_msg,
                            "content_sha256": None})
            continue
        h = content_sha256(rec)
        if h in existing_hashes:
            dup.append((tag, h, "existing_row"))
            entries.append({"tag": tag, "record_index": idx, "source": rel,
                            "client_record_id": crid, "category": "duplicate",
                            "error_code": ERR_DUPLICATE_CONTENT,
                            "message": "exact content already present; existing KP-SI id echoed; no new row",
                            "content_sha256": h,
                            "existing_scholar_id": existing_by_hash.get(h)})
            continue
        if h in batch_hashes:
            dup.append((tag, h, f"same-as {batch_hashes[h]}"))
            # intra-batch duplicate: the first copy is being inserted THIS run,
            # so no committed KP-SI id exists yet to echo -> backend id stays null.
            entries.append({"tag": tag, "record_index": idx, "source": rel,
                            "client_record_id": crid, "category": "duplicate",
                            "error_code": ERR_DUPLICATE_CONTENT,
                            "message": "duplicate of an earlier record in this batch; skipped",
                            "content_sha256": h,
                            "existing_scholar_id": None})
            continue
        batch_hashes[h] = tag
        valid.append((tag, rec, h)); order.append(tag)
        entries.append({"tag": tag, "record_index": idx, "source": rel,
                        "client_record_id": crid, "category": "valid",
                        "error_code": None, "message": None, "content_sha256": h})

    # proposed ids (dry-run preview + commit allocation both use gap-safe max+1)
    start = max_si_number(cur) + 1
    proposed = {tag: fmt_si(start + i) for i, (tag, _, _) in enumerate(valid)}

    text_mode = (args.output_format == "text")

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

    # ---- decide outcome (no early return; single emit at the end) -----------
    inserted = []                # list of (sid, tag, h)
    imported_ts = None
    batch_errors = []            # batch-level [(code_or_None, message)]

    if not commit:
        transaction_result, committed, rc = "DRY_RUN", False, 0
        if text_mode:
            rpt(); print("no database changes (dry-run).")
    elif invalid:
        # COMMIT whole-batch gate — any invalid record refuses the batch.
        transaction_result, committed, rc = "REFUSED_INVALID_IN_BATCH", False, 2
        batch_errors.append((ERR_BATCH_ATOMIC_REFUSAL,
                             "batch contains invalid records; nothing was written"))
        if text_mode:
            rpt(); print("COMMIT REFUSED: batch contains invalid records; fix or split the batch. No rows written.")
    elif not valid:
        transaction_result, committed, rc = "NOTHING_TO_COMMIT", False, 0
        if text_mode:
            rpt(); print("nothing eligible to insert; no rows written.")
    else:
        imported_ts = now_iso()
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
            transaction_result, committed, rc = "COMMITTED", True, 0
        except Exception as e:
            con.rollback()
            transaction_result, committed, rc = "ROLLED_BACK", False, 3
            batch_errors.append((None, "commit failed; transaction rolled back; no rows written"))
            if text_mode:
                print(f"COMMIT FAILED — transaction rolled back, no rows written: {e}")

        if committed and text_mode:
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

    # ---- build the machine-readable acknowledgement batch object ------------
    processed_ts = imported_ts or now_iso()
    tag2sid = {tag: sid for sid, tag, h in inserted}

    def resolve_batch_id():
        ids = sorted(seen_batch_ids)
        if len(ids) == 1:
            return ids[0]
        stem = "|".join(sorted(e.get("client_record_id") or e["tag"] for e in entries))
        short = hashlib.sha256(stem.encode("utf-8")).hexdigest()[:8]
        return (f"multi-{short}" if len(ids) > 1 else f"synth-{short}")

    # Per-record entries follow the FROZEN contract §11 shape exactly:
    #   acks[] = {client_record_id, result, backend_scholar_id, content_sha256, message}
    # `result` is the CLOSED §11 enum: imported | duplicate_skipped | invalid |
    # batch_refused | transport_failed  (there is NO dry-run value; dry-run valid
    # records surface as result=null, see PROPOSED_DRY_RUN_RESULT below).
    # `error_code` is an ADDITIVE machine field (null on success); a reader that
    # honours only the five frozen fields ignores it. NO paths, NO SQL, NO
    # submitted idea-content are ever placed in `message` (§11 rule).
    acks = []
    for e in entries:
        cat = e["category"]
        err = e["error_code"]
        if cat == "invalid":
            result, bid, msg = "invalid", None, e["message"]
        elif cat == "duplicate":
            # v0.1.1: echo the existing KP-SI id for a content-hash duplicate of a
            # committed row (null for an intra-batch dup whose first copy is only
            # being inserted this run).
            result = "duplicate_skipped"; bid = e.get("existing_scholar_id"); msg = e["message"]
        else:  # valid
            if committed:
                result = "imported"; bid = tag2sid.get(e["tag"]); err = None
                msg = f"landed at {INSERT_STATUS}"
            elif transaction_result == "DRY_RUN":
                # v0.1.1: a valid record in dry-run is "eligible" — it would be
                # inserted on --commit. Batch-level transaction_result=DRY_RUN
                # remains the authoritative "nothing was written" signal.
                result = "eligible"; bid = None; err = None
                msg = "eligible for insertion; run --commit to write"
            else:   # REFUSED_INVALID_IN_BATCH / ROLLED_BACK
                result = "batch_refused"; bid = None; err = None
                msg = "valid, but batch refused (atomic); nothing written"
        acks.append({
            "client_record_id":   e["client_record_id"],
            "result":             result,
            "backend_scholar_id": bid,
            "content_sha256":     e["content_sha256"],
            "message":            msg,
            "error_code":         err,          # additive; null on success
        })

    ack = {
        "ack_schema_version":        ACK_SCHEMA_VERSION,
        "exchange_contract_version": EXCHANGE_CONTRACT_VERSION,
        "batch_id":                  resolve_batch_id(),
        "committed":          committed,
        "transaction_result": transaction_result,
        "files_discovered":   len(files_seen),
        "records_discovered": len(entries),
        "records_valid":      len(valid),
        "records_invalid":    len(invalid),
        "records_duplicate":  len(dup),
        "records_eligible":   len(valid),
        "records_inserted":   len(inserted),
        "processed_ts":       processed_ts,
        "acks":               acks,
        "errors":             [{"error_code": c, "message": m} for c, m in batch_errors],
    }

    if args.ack_file:
        Path(args.ack_file).write_text(
            json.dumps(ack, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if text_mode:
            print(f"acknowledgement written: {args.ack_file}")
    if not text_mode:
        print(json.dumps(ack, indent=2, ensure_ascii=False))

    con.close(); return rc

if __name__ == "__main__":
    sys.exit(main())
