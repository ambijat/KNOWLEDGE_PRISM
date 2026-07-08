# RECOLL KALEIDOSCOPE PROTOCOL
### A governed retrieval cycle that amplifies the scholar's *reach* — design specification (v1, design-only)

**Status:** DESIGN SPEC. No Recoll query has been run under this document. Nothing here retrieves, samples, grades, dispositions, or promotes. Running the cycle requires separate, explicit approval.
**Governed by:** `CHARTER.md` (doctrine block 19). Where this protocol and the Charter appear to differ, the Charter governs.
**Charter register:** this is **corpus physiology** — how relevant material *circulates* toward a living research question.

---

## 1. PURPOSE OF THE KALEIDOSCOPE

A static 53 GB library cannot rearrange itself around a question; it is a shelf. The kaleidoscope is the mechanism that makes the corpus *turn*: pose a research goal and the same fragments of glass — the same files — fall into a new pattern, ranked and interpreted for *that* goal. Nothing in the glass changes; the arrangement does.

Its single purpose is to **amplify the scholar's gathering gesture** — "go to where the books are stored, seek the relevant ones, bring them to the table" — across a corpus far larger than any memory can hold, and to hand the scholar a *ranked, interpreted, provenance-stamped* candidate set instead of a raw pile. It replaces hand-picking-by-folder as the way the verification queue is filled.

It is a *surface instrument*: the scholar stands at the cave mouth and turns the lens. Turning it never requires descending into the corpus, and every turn is recorded, so depth stays always knowable.

---

## 2. HOW IT AMPLIFIES REACH WITHOUT REPLACING JUDGMENT

| The gesture | What the scholar keeps | What the kaleidoscope supplies (amplification) |
|---|---|---|
| Form the question | **Holds the question.** Only the scholar authors the research goal. | — |
| Turn it into search terms | Approves/edits the lens. | Proposes a query expansion (synonyms, actors, regions, theory terms). |
| Find relevant material | **Judges what actually matters.** | Ranks the whole corpus in seconds; supplies reach (memory of 12,000+ books). |
| Decide what to read next | **Selects** which candidates enter the queue. | Presents candidates with clue-scores + what we already know about each. |
| Read and weigh evidence | **Reads the text; that alone is evidence.** | Nothing — retrieval never reads *for* the scholar. |

The amplifications are **reach, memory, endurance** — never *thinking*. The kaleidoscope proposes; the scholar (and the verification queue) dispose.

---

## 3. THE CARDINAL DISTINCTION — RETRIEVAL RELEVANCE ≠ SCHOLARLY EVIDENCE

This is the load-bearing rule of the whole protocol.

- **Recoll relevance is a CLUE.** It is lexical: term frequency, field weighting, proximity. A book ranked #1 for "securitization" contains the *word* prominently. That is a strong reason to *look*, and no reason at all to *believe*.
- **Scholarly evidence is TEXT SEEN.** A concept is real for KNOWLEDGE_PRISM only when a human/agent has read the bounded sample and seen the concept doing work in an argument (per `VERIFICATION_RUBRIC.md`).

Therefore: **a retrieval result is never a verdict.** The highest-ranked, most novel, most on-topic hit is a *candidate* with evidence grade `provisional_unverified` until it passes text sampling. The kaleidoscope *feeds* the verification queue; it never substitutes for it and never writes to the evidence ladder, dispositions, functional roles, or ontology.

---

## 4. INPUT FORMAT — THE RESEARCH QUESTION

A cycle begins only from a scholar-authored research goal. Input record:

```yaml
research_question:
  id: RQ-YYYYMMDD-nn            # assigned at intake
  author: <scholar>            # must be the scholar; the machine holds no question of its own
  question: "<one sentence, natural language>"
  layer_intent: A | B | AB     # empirical / method-theory / both, as the scholar reads it
  seed_terms: [ ... ]          # optional scholar-supplied must-include terms
  region_focus: [ ... ]        # optional: Afghanistan, Central Asia, Eurasia, ...
  notes: "<why this question now>"
```

Only `question` is mandatory; everything else refines the lens. No cycle may be initiated from a machine-generated question.

---

## 5. QUERY EXPANSION LOGIC (forming the lens)

The lens is a *proposal* the scholar can edit before any query runs. Expansion is transparent and bounded — never a black box.

1. **Core terms** — extracted from `question` + `seed_terms`.
2. **Controlled expansion** — for each core term, add:
   - morphological variants (Recoll stems automatically; we note it, do not fight it);
   - a short, *declared* synonym/near-term set from the project's own vocabulary (e.g. securitization ↔ threat construction ↔ Copenhagen School);
   - region aliases (Afghanistan ↔ Af-Pak ↔ Hindu Kush; Central Asia ↔ Turkestan ↔ the 'stans);
   - theory-name aliases (RSCT ↔ regional security complex; critical geopolitics ↔ Ó Tuathail).
3. **Layer biasing** — if `layer_intent=B`, add method/theory anchor terms; if `A`, add empirical/place anchors. Declared, not silent.
4. **Lens record** — the final boolean lens is written down verbatim (the exact Recoll query string) so the run is reproducible and the expansion is auditable. Expansion that cannot be shown is not used.

**Discipline:** expansion widens *reach*, never *admission*. A term added by expansion can surface a book; it can never grade one.

---

## 6. RESULT RANKING LOGIC (clue-scoring, not verdicts)

Recoll returns, per hit, at minimum: `url`/path, title, mime, size, and its relevance score. From these clues the cycle computes a **composite clue-score** with three declared components. All three are *clues*; none is evidence.

1. **Relevance (R)** — Recoll's own lexical score (normalised 0–1). "Does the text mention this a lot, prominently?"
2. **Novelty (N)** — is this file *new* to our attention? Computed by joining the hit path to what we already hold:
   - already in `master_corpus` (catalogued)? already carries an `evidence_grade`? already has a `functional_role` reading? already dispositioned in `verdict_disposition`?
   - N is highest for a strong-relevance file we have *never looked at*, lowest for one already fully read. Novelty surfaces the unexplored rather than re-surfacing the known.
3. **Project fit (F)** — coarse, honest, and provisional: does the file's folder/topdir (via `recoll_subject_folders.domain`/`knowledge`) and title sit inside the Charter's Layer A/B boundary, or is it plainly out-of-domain (the Histology lesson)? F is a *prior*, explicitly overridable by the scholar, never a final relevance judgment.

Composite clue-score = a **declared, tunable weighting** of (R, N, F) — the weights are written into the run record, not hidden. The output is a *ranked candidate list*, labelled at the top: **"relevance clues for triage — not evidence, not verdicts."**

**Intersection step (what makes a raw list a *pattern*):** every candidate is left-joined to `master_corpus` (on `path_norm`), `functional_role` (on `file`), and `verdict_disposition` (on `file`), so each row carries "what we already know" — catalogued? graded? functionally read? dispositioned? This is the step that turns a search result into an interpreted kaleidoscope pattern.

---

## 7. GREY-ZONE LOGGING RULES (Charter Second Law: judge freely, never silently)

Retrieval is the natural home of "reach further or hold back" judgment. Every such call is logged — not to constrain it, but to keep it auditable and reversible.

A **grey-zone judgment** occurs whenever the cycle (or the scholar via the cycle) does any of:
- surfaces/keeps a candidate **below** the normal clue-score cutoff because it looks important (gate bent *open*);
- drops a high-scoring candidate as noise/duplicate/out-of-domain (gate bent *closed*);
- overrides the project-fit prior F in either direction;
- widens the lens with a non-obvious expansion term.

Each is written to a **retrieval judgment log** (JSONL, alongside the run record — *not* the evidence ledger, since nothing is being verified):
```json
{"rq_id":"RQ-...","file":"<path>","call":"kept_below_cutoff|dropped_high|override_fit|lens_widen",
 "clue_score":0.xx,"reason":"<one line>","decided_by":"claude|scholar","ts":"<iso>"}
```
No grey-zone call is ever silent. A cycle with hidden judgment is a faulty cycle.

---

## 8. BOUNDARY-KINEMATICS RULES (Charter Third Law)

The relevance/novelty/fit cutoffs and the fit-prior are **boundaries**, and boundaries learn.

- **Move on surprise.** When a cycle produces a result the current boundary got *wrong* — a top-fit file that turns out out-of-domain, or a low-fit file the scholar rules clearly central — that case is tagged a **boundary-learning candidate** (`surprise=true` in the run record). Accumulated surprises are what justify adjusting a cutoff or the fit-prior *later*, deliberately, with the change recorded on the ledger.
- **Rest on confirmation.** When results land where the boundary predicted, the boundary does **not** move. Confirming cases are logged as confirmations, not triggers.
- **Avoid overfitting.** A single surprising book never moves a boundary by itself. A boundary shifts only when a *pattern* of surprises accumulates (a standing threshold, e.g. repeated same-direction surprises across ≥N cycles), and only by explicit, sealed decision — never automatically mid-run. The scholar who redefines "relevant" on every shiny hit ends with no domain at all.

Crucially: **the kaleidoscope proposes boundary moves; it never enacts them.** Enacting a boundary change is a separate, sealed ledger act.

---

## 9. PATH FROM RECOLL RESULT TO VERIFICATION QUEUE

The only exit a candidate has toward the core runs through text.

```
research_question
   → lens (query expansion)
   → Recoll ranked hits            [CLUES]
   → composite clue-score + intersection with what-we-know   [PATTERN]
   → scholar/agent SELECTS candidates (grey-zone calls logged)
   → selected candidates ENTER the verification queue at grade `provisional_unverified`
   → bounded text sampling (VERIFICATION_RUBRIC.md)          [EVIDENCE]
   → two-axis disposition + functional-IR reading
   → (only on passing, by separate sealed act) evidence-grade promotion
```

Selection **into the queue** is the kaleidoscope's last legitimate step. Everything downstream of "enter the queue" is the existing, unchanged pipeline. The kaleidoscope adds an intelligent *front door*; it moves no wall behind it.

---

## 10. PROHIBITED ACTIONS

The cycle must **never**:
1. treat a Recoll relevance score, rank, folder, or title as scholarly evidence;
2. write to `evidence_grade`, `verdict_disposition`, `functional_role`, `claim`, or any ontology-core table directly from retrieval;
3. promote any candidate to `concept_verified` or `ontology_core`;
4. admit a candidate to the core without bounded text sampling;
5. move a boundary automatically, mid-run, or on a single surprise;
6. make a grey-zone judgment silently (unlogged);
7. initiate a cycle from a machine-generated (non-scholar) question;
8. use a query expansion term that cannot be shown in the run record;
9. scale to batch retrieval across the corpus without explicit approval of *this* protocol first.

---

## 11. OUTPUT SCHEMA FOR A FUTURE RETRIEVAL RUN

A run (when approved) produces one **run record** — self-describing, reproducible, provenance-stamped. It is a *proposal artifact*, not a ledger mutation.

```yaml
kaleidoscope_run:
  run_id: KAL-YYYYMMDD-nn
  research_question: { id, author, question, layer_intent }
  lens:
    expansion_terms: [ ... ]
    recoll_query_string: "<verbatim>"     # exact, reproducible
    weights: { relevance: w_R, novelty: w_N, fit: w_F }
    cutoff: <clue-score threshold used>
  ts_run: <iso>
  hit_count_total: <int>                  # e.g. Recoll's "N results"
  candidates:                             # top-K after clue-scoring + intersection
    - file: <path_norm>
      title: <str>
      recoll_relevance: 0.xx
      novelty: 0.xx
      project_fit: 0.xx
      clue_score: 0.xx
      known_state:                        # from the intersection joins
        in_master_corpus: bool
        evidence_grade: <str|null>
        functional_role: <present|null>
        disposition: <str|null>
      selected_for_queue: bool
      surprise: bool                      # boundary-learning candidate?
  grey_zone_log: [ {file, call, reason, decided_by, ts}, ... ]
  boundary_learning:
    surprises: [ ... ]
    confirmations_count: <int>
    proposed_boundary_moves: [ ... ]      # PROPOSALS ONLY — enacted separately, sealed
  outputs:
    selected_into_queue: [ <file>, ... ]  # these get grade provisional_unverified, nothing more
    changed_evidence_state: false         # ALWAYS false for a retrieval run
```

A run record changes **no** evidence state. Its only downstream effect is that `selected_into_queue` files become *known targets* for a later, separate sampling act.

---

## 12. EXAMPLE DRY-RUN (hypothetical — NO Recoll query executed)

*Illustration only. The numbers below are fabricated to show the shape of a run record; no retrieval was performed to produce them.*

**Research question (hypothetical):**
> RQ-20260708-01 · author: scholar · *"How is Russia's imagination of its Central Asian frontier constructed in geopolitical thought?"* · layer_intent: AB · region_focus: [Central Asia, Eurasia].

**Lens (proposed, would be shown for approval before any run):**
- core: Russia, Central Asia, frontier, geopolitical imagination
- expansion: Russia↔Russian↔Eurasian; Central Asia↔Turkestan↔the 'stans; frontier↔borderland↔near abroad; geopolitical imagination↔critical geopolitics↔spatial identity
- layer bias (AB): +empire, +security complex, +Mackinder/Heartland
- verbatim query (illustrative): `(russia OR eurasian) AND ("central asia" OR turkestan) AND (frontier OR borderland OR "near abroad") AND (geopolit* OR imagination OR heartland)`

**Illustrative candidate pattern (fabricated, post-intersection):**

| file (illustrative) | R | N | F | clue | known state | selected? | surprise? |
|---|---|---|---|---|---|---|---|
| .../Eurasia_Heartland_Mackinder.pdf | 0.91 | 0.80 | 0.85 | 0.87 | in corpus, ungraded | ✔ | — |
| .../Russia_and_the_Mongols.pdf | 0.74 | 0.20 | 0.70 | 0.55 | disposition=review_required | ✔ (re-sample) | — |
| .../NearAbroad_Identity.pdf | 0.68 | 0.95 | 0.75 | 0.79 | not in corpus | ✔ | ✔ (novel, high-fit, unseen) |
| .../Central_Asian_Gas_Pipelines.pdf | 0.82 | 0.60 | 0.30 | 0.52 | not in corpus | ✘ (F low: energy-policy, not frontier-thought) | ✔ (high R, low F → boundary note) |

**Grey-zone calls that would be logged (illustrative):**
- kept `Russia_and_the_Mongols` *below* the novelty floor because it is an open `review_required` item this question directly bears on (`call: kept_below_cutoff`);
- dropped `Central_Asian_Gas_Pipelines` despite high relevance as out-of-frontier-thought (`call: dropped_high`, `override_fit`).

**Boundary-learning implication (illustrative):** the gas-pipelines case is a high-relevance / low-fit *surprise* — one instance, so it moves nothing; it is tagged and parked. If several cycles keep surfacing energy-corridor texts for frontier-thought questions, that accumulation would *later* justify a deliberate, sealed refinement of the fit-prior (perhaps a `connectivity` sub-facet). Not now, not automatically.

**Evidence state after this dry-run:** unchanged. Three files would be *proposed* for the verification queue at `provisional_unverified`; none graded, dispositioned, or promoted.

---

## APPENDIX — CHARTER TRACEABILITY
- **Exoskeleton / reach amplification** → §§1,2. **Kaleidoscope (non-static corpus)** → §1. **Clue-not-evidence cardinal rule** → §§3,6,9,10. **Second Law (judge freely, never silently)** → §7. **Third Law (move on surprise / rest on confirmation / avoid overfitting)** → §8. **Physiology register** → header. **Pipeline unbypassed** → §9.
