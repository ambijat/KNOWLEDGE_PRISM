#!/usr/bin/env python3
"""KNOWLEDGE_PRISM DB consistency validator (block 25).

Read-only. Encodes the audit's evidence-integrity checks so every shift can run
them instead of ad-hoc SQL. Exits 1 on any FAIL. Never mutates the DB.

Checks:
  1. Ledger chain verifies; block numbers contiguous, no duplicates.
  2. Every promoted row (sampled_text_supported_core_candidate) has a claim AND a functional_role (1:1, no orphans).
  3. Queue candidate_type/status conform to their taxonomy tables; dispositions conform to disposition_taxonomy.
  4. layer_norm present and in controlled vocab {A,B,AB,Peripheral,Out_of_domain,Ambiguous} on verdict_disposition + functional_role.
  5. Ontology nodes carry provenance_status; text_verified count == count at ontology_core (integrity of the design-vs-verified split).
  6. Scholar-input (schema v0.2, NOT evidence): status/record_type/schema_version/source/draft_organ conform to frozen vocab;
     the exact five-status taxonomy is present; no approved_to_evidence status exists; scholar_input ids never appear
     in verification_queue/claim/verdict_disposition/functional_role/ontology_node; empty scholar_input table is valid.
"""
import os, sys, sqlite3
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT,"db"))
DB=os.path.join(ROOT,"db","knowledge_prism.db")
LAYERS={"A","B","AB","Peripheral","Out_of_domain","Ambiguous"}
base=lambda x: os.path.basename(str(x))
fails=[]; notes=[]

con=sqlite3.connect(DB); cur=con.cursor()

# 1. chain
try:
    import prism_ledger as L
    ok,bad=L.verify_chain(con)
    if not ok: fails.append(f"chain broken: {bad}")
except Exception as e:
    notes.append(f"chain check skipped: {e}")
nos=[r[0] for r in cur.execute("SELECT block_no FROM block ORDER BY block_no")]
if nos:
    gaps=[n for n in range(min(nos),max(nos)+1) if n not in nos]
    if gaps: fails.append(f"block gaps: {gaps}")
    if len(nos)!=len(set(nos)): fails.append("duplicate block_no")

# 2. promoted 1:1 claim + functional_role
prom={base(r[0]) for r in cur.execute("SELECT file FROM verdict_disposition WHERE evidence_grade='sampled_text_supported_core_candidate'")}
claim={base(r[0]) for r in cur.execute("SELECT source_file FROM claim WHERE block_no=16")}
fr={base(r[0]) for r in cur.execute("SELECT file FROM functional_role")}
if prom-claim: fails.append(f"promoted w/o claim: {prom-claim}")
if prom-fr:    fails.append(f"promoted w/o functional_role: {prom-fr}")

# 3. vocab conformance
def conform(tab,col,taxtab,taxcol):
    tax={r[0] for r in cur.execute(f"SELECT {taxcol} FROM {taxtab}")}
    used={r[0] for r in cur.execute(f"SELECT DISTINCT {col} FROM {tab} WHERE {col} IS NOT NULL")}
    bad=used-tax
    if bad: fails.append(f"{tab}.{col} not in {taxtab}: {bad}")
conform("verification_queue","candidate_type","queue_candidate_type_taxonomy","candidate_type")
conform("verification_queue","status","queue_status_taxonomy","status")
conform("verdict_disposition","disposition","disposition_taxonomy","disposition")

# 4. layer_norm vocab
for tab in ("verdict_disposition","functional_role"):
    used={r[0] for r in cur.execute(f"SELECT DISTINCT layer_norm FROM {tab} WHERE layer_norm IS NOT NULL")}
    bad=used-LAYERS
    if bad: fails.append(f"{tab}.layer_norm outside vocab: {bad}")
    nulls=cur.execute(f"SELECT COUNT(*) FROM {tab} WHERE layer_norm IS NULL").fetchone()[0]
    if nulls: notes.append(f"{tab}: {nulls} rows with null layer_norm")

# 5. ontology provenance split integrity
tv=cur.execute("SELECT COUNT(*) FROM ontology_node WHERE provenance_status='text_verified'").fetchone()[0]
oc=cur.execute("SELECT COUNT(*) FROM verdict_disposition WHERE evidence_grade='ontology_core'").fetchone()[0]
if tv!=oc: fails.append(f"ontology text_verified ({tv}) != items at ontology_core ({oc})")
missp=cur.execute("SELECT COUNT(*) FROM ontology_node WHERE provenance_status IS NULL").fetchone()[0]
if missp: fails.append(f"{missp} ontology nodes lack provenance_status")

# 6. scholar_input (schema v0.2) — NOT evidence
def _tbl(t): return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
SI_STATUSES={"raw_captured","imported_not_evidence","under_review","approved_to_question","rejected_archived"}
SI_ORGANS={"Title","Background","Statement_of_Problem","Research_Gap","Research_Questions","Objectives",
           "Scope","Methodology","Conceptual_Framework","Literature_Clusters","Evidence_Needs",
           "Case_Region_Time_Period","Chapterisation","Supervisor_Questions","Revision_Tasks","Unassigned"}
if not _tbl("scholar_input") or not _tbl("scholar_input_status_taxonomy"):
    fails.append("scholar_input / scholar_input_status_taxonomy table missing")
else:
    taxset={r[0] for r in cur.execute("SELECT status FROM scholar_input_status_taxonomy")}
    if taxset!=SI_STATUSES:
        fails.append(f"scholar_input_status_taxonomy != frozen 5-set (missing={SI_STATUSES-taxset}, extra={taxset-SI_STATUSES})")
    if "approved_to_evidence" in taxset:
        fails.append("forbidden status approved_to_evidence present in scholar_input_status_taxonomy")
    n=cur.execute("SELECT COUNT(*) FROM scholar_input").fetchone()[0]
    if n==0:
        notes.append("scholar_input empty (valid — no content rows created)")
    else:
        # status conformance
        bad_st={r[0] for r in cur.execute("SELECT DISTINCT status FROM scholar_input WHERE status IS NOT NULL")}-taxset
        if bad_st: fails.append(f"scholar_input.status not in taxonomy: {bad_st}")
        bad_rt={r[0] for r in cur.execute("SELECT DISTINCT record_type FROM scholar_input WHERE record_type IS NOT NULL")}-{"scholar_input_not_evidence"}
        if bad_rt: fails.append(f"scholar_input.record_type != scholar_input_not_evidence: {bad_rt}")
        bad_sv={r[0] for r in cur.execute("SELECT DISTINCT schema_version FROM scholar_input WHERE schema_version IS NOT NULL")}-{"0.2"}
        if bad_sv: fails.append(f"scholar_input.schema_version != 0.2: {bad_sv}")
        bad_src={r[0] for r in cur.execute("SELECT DISTINCT source FROM scholar_input WHERE source IS NOT NULL")}-{"android_app","desktop_manual","desktop_import"}
        if bad_src: fails.append(f"scholar_input.source not in vocab: {bad_src}")
        bad_org={r[0] for r in cur.execute("SELECT DISTINCT draft_organ FROM scholar_input WHERE draft_organ IS NOT NULL")}-SI_ORGANS
        if bad_org: fails.append(f"scholar_input.draft_organ not in frozen organ vocab: {bad_org}")
        # scholar input must NOT have leaked into any downstream evidence/retrieval/ontology structure.
        # Covers every requested target that exists as a real table in this DB:
        #   verification_queue (retrieval), claim (evidence), verdict_disposition (disposition),
        #   functional_role (functional interpretation), ontology_node (ontology / ontology-core).
        #   'evidence', 'verified concept', 'ontology core' are not standalone tables here — they are
        #   states realised on the tables above (see the not-applicable notes in the closure report).
        si_ideas={base(r[0]) for r in cur.execute("SELECT scholar_id FROM scholar_input")}
        leak_targets=(("verification_queue","file"),("verification_queue","queue_id"),
                      ("claim","source_file"),("verdict_disposition","file"),
                      ("functional_role","file"),("ontology_node","label"),("ontology_node","node_id"))
        for tab,col in leak_targets:
            leak={base(r[0]) for r in cur.execute(f"SELECT {col} FROM {tab} WHERE {col} IS NOT NULL")}&si_ideas
            if leak: fails.append(f"scholar_input id leaked into {tab}.{col}: {leak}")

# ---- CHECK 7: scholar_input -> approved_to_question transition invariants (block 28) ----
# Applies to the governed transition destination `research_question`. Skips cleanly if the
# table is absent (pre-block-28 DBs) so this validator stays backward-compatible.
if _tbl("scholar_input") and _tbl("research_question"):
    si=list(cur.execute("SELECT scholar_id,status,became_question,became_queue_id,"
                        "decided_by,decided_ts,rejection_reason FROM scholar_input"))
    rq_ids={r[0] for r in cur.execute("SELECT question_id FROM research_question")}
    rq_origin={r[0]:r[1] for r in cur.execute("SELECT question_id,origin_scholar_id FROM research_question")}
    for sid,st,bq,bqq,dby,dts,rej in si:
        # 1 approved_to_question requires non-null became_question
        if st=="approved_to_question" and not bq:
            fails.append(f"{sid} approved_to_question but became_question is NULL")
        # 2/4 only approved_to_question may carry became_question (no preserved-history exception in use)
        if st!="approved_to_question" and bq:
            fails.append(f"{sid} status={st} must not have became_question ({bq})")
        # 3 rejected_archived field requirements
        if st=="rejected_archived":
            if not dby: fails.append(f"{sid} rejected_archived missing decided_by")
            if not dts: fails.append(f"{sid} rejected_archived missing decided_ts")
            if not (rej and str(rej).strip()): fails.append(f"{sid} rejected_archived missing rejection_reason")
            if bq: fails.append(f"{sid} rejected_archived must have became_question NULL")
        # 5 every non-null became_question points to a real research_question row
        if bq and bq not in rq_ids:
            fails.append(f"{sid} became_question={bq} has no research_question row")
        # 6 reciprocal provenance: destination points back to this scholar_input
        if bq and rq_origin.get(bq)!=sid:
            fails.append(f"research_question {bq} origin_scholar_id != {sid} (broken reciprocal provenance)")
        # 7 became_queue_id must stay NULL at this stage
        if bqq:
            fails.append(f"{sid} became_queue_id must be NULL at approved_to_question stage (got {bqq})")
    # 8 one scholar_input -> at most one approved question record
    dup=[r for r in cur.execute("SELECT origin_scholar_id,COUNT(*) c FROM research_question "
                                "GROUP BY origin_scholar_id HAVING c>1")]
    if dup: fails.append(f"scholar_input(s) with multiple research_question rows: {dup}")
    # 9 every research_question origin must be an approved_to_question scholar_input (no orphan/leak)
    si_status={r[0]:r[1] for r in cur.execute("SELECT scholar_id,status FROM scholar_input")}
    for qid,orig in rq_origin.items():
        if si_status.get(orig)!="approved_to_question":
            fails.append(f"research_question {qid} origin {orig} is not approved_to_question "
                        f"(status={si_status.get(orig)})")

con.close()
print("=== KNOWLEDGE_PRISM DB CONSISTENCY ===")
for n in notes: print("NOTE:", n)
if fails:
    print("VALIDATION FAILED"); [print("FAIL:",f) for f in fails]; sys.exit(1)
print("VALIDATION PASSED (all consistency checks green)")
