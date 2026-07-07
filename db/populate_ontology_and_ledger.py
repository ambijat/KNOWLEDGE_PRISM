#!/usr/bin/env python3
"""
Populate the ontology layer + lay down the provenance ledger.

Ontology nodes/edges are rebuilt cleanly (interpretive, derivable).
The blocks / claims / claim_events / artifact_hashes are APPEND-ONLY and
idempotent (guarded by natural keys), so re-running never duplicates history
and never rewrites the chain.

Run:  python3 db/populate_ontology_and_ledger.py [SESSION_ID]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import prism_ledger as L

ROOT=L.ROOT
SESSION = sys.argv[1] if len(sys.argv)>1 else "7b564c3e-8699-4f40-98e6-07c5c35d7649"
con=L.connect(); cur=con.cursor()

# ============================================================ PROVENANCE BLOCKS
# Block 0000 — genesis (Claude Science reconnaissance / domain mapping)
b0=L.seal_block(con,"block_0000_genesis_recon",
    "Genesis: Claude Science reconnaissance & two-layer domain mapping",
    "prior-claude-session","claude",
    inputs=["Zotero library","Recoll index","SOLEMON drive"],
    operations=["zotero inventory (1841)","recoll manifest (12594)","solemon crawl (35178)",
                "bridge concept extraction (392)","two-layer domain definition"],
    outputs=["zotero_inventory.csv","recoll_corpus_manifest.csv","solemon_crawl.csv",
             "bridge_concepts.csv","domain_definition_v2.md","domain_map.png"],
    ts="2026-07-05T00:00:00+00:00")

# Block 0001 — Codex takeover (evidence-grade regime imposed)
b1=L.seal_block(con,"block_0001_codex_takeover",
    "Codex takeover: evidence-graded master register & verification regime",
    "codex-session","codex",
    inputs=["Claude reconnaissance artifacts"],
    operations=["path-union master register (35861)","dedupe (3347 groups, 7259 dup rows)",
                "preliminary class: 11453 Core / 839 Peripheral / 432 Noise / 23137 Unknown",
                "evidence grading: 23267 metadata_only / 12594 metadata_manifest",
                "bridge concepts flagged hypothesis_only","revised protocol + corrected domain boundary"],
    outputs=["MASTER_CORPUS_REGISTER_PRELIMINARY.csv","ZOTERO_REGISTER_PRELIMINARY.csv",
             "BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv","REVISED_PROJECT_PROTOCOL.md",
             "CORRECTED_DOMAIN_BOUNDARY.md","takeover_summary.json"],
    ts="2026-07-06T13:03:30+00:00")

# Block 0002 — this session: eigenspace + Step-2 loop + DB consolidation under PoP
b2=L.seal_block(con,"block_0002_eigenspace_step2_db",
    "Eigenspace analysis, Step-2 literature loop, and Proof-of-Provenance DB",
    SESSION,"claude",
    inputs=["Google Scholar publications (47)","OpenAlex","arXiv","all inherited registers"],
    operations=["publication eigenspace: NMF on weighted 47x45 matrix -> 5 latent axes",
                "weighted A×B intersection seam (136)",
                "Step-2 looping literature pull -> 86 papers (47 seed/27 loop/12 frontier)",
                "consolidated all sources into knowledge_prism.db",
                "installed hash-chained provenance ledger"],
    outputs=["eigenspace.png","intersection_seam.csv","step2_corpus.csv",
             "step2_methodology.md","knowledge_prism.db"])

print(f"blocks sealed: genesis={b0} takeover={b1} current={b2}")

# ============================================================ CLAIMS (transactions)
# (claim_text, scope, source_file, grade, created_by, block, status)
claims=[
 ("Domain is two-layer: empirical geopolitical core (A) × method/epistemology apparatus (B).",
  "domain","domain_definition_v2.md","reconnaissance","AI",b0,"provisional"),
 ("Empirical core: Afghanistan/Taliban → South/Central Asia, Eurasia, China connectivity (BRI), Russian energy.",
  "domain.layerA","domain_definition_v2.md","reconnaissance","AI",b0,"provisional"),
 ("SOLEMON crawl yields 35,178 documents; master register unions to 35,861 rows.",
  "corpus.size","takeover_summary.json","metadata_manifest","codex",b1,"accepted"),
 ("Corpus dedupe: 3,347 duplicate groups spanning 7,259 rows.",
  "corpus.dedupe","takeover_summary.json","metadata_manifest","codex",b1,"accepted"),
 ("Preliminary corpus classes: 11,453 Core / 839 Peripheral / 432 Noise / 23,137 Unknown.",
  "corpus.class","MASTER_CORPUS_REGISTER_PRELIMINARY.csv","metadata_only","codex",b1,"provisional"),
 ("Bridge concepts for 392 books are AI-generated hypotheses pending verification.",
  "bridge","BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv","hypothesis_only","AI",b1,"provisional"),
 ("Publication eigenspace (47 works, citation×recency weighted) resolves into 5 latent A×B axes.",
  "eigenspace","eigenspace.png","analysis","AI",b2,"accepted"),
 ("Top intersectionable: regional security complex × classical geopolitics (weight 5.42).",
  "eigenspace.seam","intersection_seam.csv","analysis","AI",b2,"accepted"),
 ("Step-2 literature loop assembled 86 unique papers (47 seed + 27 loop + 12 method-frontier).",
  "step2","step2_corpus.csv","analysis","AI",b2,"accepted"),
 ("Target intersection (formal/computational models of RSC knowledge structures) is sparse in the literature.",
  "step2.finding","step2_methodology.md","analysis","AI",b2,"provisional"),
]
cids=[]
for c in claims:
    cid=L.register_claim(con,*c); cids.append(cid)
# the two accepted metadata-manifest claims get an explicit verification event (once)
for cid in (cids[2], cids[3]):
    has_verify=con.execute("""SELECT 1 FROM claim_event WHERE claim_id=? AND event='verified'
                              LIMIT 1""",(cid,)).fetchone()
    if not has_verify:
        L.advance_claim(con,cid,"verified","accepted","recomputed from source manifest","codex",b1)
print(f"claims registered: {len(cids)}")

# ============================================================ ARTIFACT FINGERPRINTS
nh=L.hash_tree(con, ROOT, b2, "project",
               exts=(".csv",".json",".md",".png",".py",".db",".txt",".sh"))
print(f"artifacts fingerprinted: {nh}")

# ============================================================ ONTOLOGY (derivable)
cur.execute("DELETE FROM ontology_node"); cur.execute("DELETE FROM ontology_edge")

# five latent axes from the publication eigenspace
axes=[
 ("axis1","Axis","Af-Pak regional security × realism/RSCT","meta",None),
 ("axis2","Axis","Afghan state & ethnicity × critical geopolitics/ethnogeopolitics","meta",None),
 ("axis3","Axis","India energy corridors × classical geopolitics/subaltern","meta",None),
 ("axis4","Axis","BRI connectivity × geoeconomic simulacrum/semiotics","meta",None),
 ("axis5","Axis","China–Central Asia–Eurasia × classical geopolitics/RSCT","meta",None),
]
# layer A empirical objects, layer B method lenses
layerA=["Afghanistan","Taliban","Pakistan/Af-Pak","Central Asia","South Asia","Russia","China",
 "India","Eurasia","Heartland","energy security","energy corridors/pipelines","BRI/Silk Road",
 "connectivity/infrastructure","regional security complex","borders/Durand Line","ethnic politics","environment"]
layerB=["classical geopolitics","critical geopolitics","geopolitical constructivism","realism/neorealism",
 "English School","semiotics","simulacrum/geoeconomics","ontology","systems theory","GIS/spatial analysis",
 "grounded theory","ethnogeopolitics","subaltern/critical theory","securitisation theory","state-building",
 "social network analysis","agent-based modeling","complex adaptive systems","knowledge representation","AI-for-IR"]

nodes=[]
for nid,typ,lab,layer,det in axes: nodes.append((nid,typ,lab,layer,None,det))
for x in layerA: nodes.append(("A:"+x,"Empirical Object",x,"A",None,None))
for y in layerB: nodes.append(("B:"+y,"Method/Theory",y,"B",None,None))
cur.executemany("INSERT INTO ontology_node VALUES (?,?,?,?,?,?)",nodes)

# seam edges from intersection_seam table (weighted A×B)
rows=cur.execute("SELECT layerA,layerB,weight FROM intersection_seam").fetchall()
edges=[("A:"+a,"B:"+b,"fuses_with",float(w)) for a,b,w in rows if w]
cur.executemany("INSERT INTO ontology_edge VALUES (?,?,?,?)",edges)
# update node weights = summed seam mass
for lay,pref in [("A","A:"),("B","B:")]:
    idx=0 if lay=="A" else 1
    agg={}
    for a,b,w in rows:
        k=(pref+(a if lay=="A" else b)); agg[k]=agg.get(k,0)+ (float(w) if w else 0)
    for k,v in agg.items():
        cur.execute("UPDATE ontology_node SET weight=? WHERE node_id=?",(round(v,3),k))

con.commit()

# ============================================================ SESSION LOG (append-only, dedup)
actions=[
 ("analyze","publication eigenspace","NMF on weighted 47×45 pub-concept matrix; 5 latent axes",b2),
 ("analyze","intersection seam","136 weighted A×B seams computed",b2),
 ("deliver","eigenspace.png","two-panel figure: seam heatmap + axis loadings",b2),
 ("analyze","step2 literature loop","3-pass citation snowball via OpenAlex+arXiv; 86 papers",b2),
 ("deliver","step2_corpus.csv","final 86-paper corpus with provenance",b2),
 ("build","knowledge_prism.db","consolidated all sources into SQLite spine",b2),
 ("build","provenance ledger","hash-chained blocks + claims + artifact fingerprints",b2),
 ("build","ontology layer","5 axes + 38 nodes + weighted seam edges",b2),
]
have=set(a+"|"+t for a,t in cur.execute(
    "SELECT action,target FROM session_log WHERE session_id=?",(SESSION,)).fetchall())
for act,tgt,det,bn in actions:
    if act+"|"+tgt not in have:
        cur.execute("INSERT INTO session_log VALUES (?,?,?,?,?,?,?)",
            (SESSION,L.now(),"claude",act,tgt,det,bn))
con.commit()

# ============================================================ CHAIN VERIFY + SUMMARY
ok,problems=L.verify_chain(con)
n_blk=cur.execute("SELECT COUNT(*) FROM block").fetchone()[0]
n_cl =cur.execute("SELECT COUNT(*) FROM claim").fetchone()[0]
n_ev =cur.execute("SELECT COUNT(*) FROM claim_event").fetchone()[0]
n_ah =cur.execute("SELECT COUNT(*) FROM artifact_hash").fetchone()[0]
n_nodes=cur.execute("SELECT COUNT(*) FROM ontology_node").fetchone()[0]
n_edges=cur.execute("SELECT COUNT(*) FROM ontology_edge").fetchone()[0]
n_log=cur.execute("SELECT COUNT(*) FROM session_log").fetchone()[0]
print(f"ontology: {n_nodes} nodes, {n_edges} edges | session_log: {n_log}")
print(f"provenance: {n_blk} blocks, {n_cl} claims, {n_ev} claim_events, {n_ah} artifact hashes")
print(f"chain integrity: {'OK' if ok else 'BROKEN'}" + ("" if ok else f" -> {problems}"))
con.close()
