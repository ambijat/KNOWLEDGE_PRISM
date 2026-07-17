# The Recipe — How KNOWLEDGE_PRISM Is Actually Used
### Backend / research-governance view of the researcher's experience

> Written for the backend department. It states what the researcher brings, what
> the kitchen (this backend) does with it, and what the front end (Codex) must be
> handed so the experience feels enriched rather than like a raw search box.
> It changes no evidence, disposition, queue, ontology, boundary, corpus, or ledger state.

---

## 0. The dish (what the researcher is actually trying to cook)

A PhD student or paper author does not want "search results." They want, for a
specific claim they are about to commit to print:

> *the smallest set of texts that actually earn the claim, each one read at least
> in sample, tagged with what it does for the argument, and carrying provenance
> strong enough to cite and to defend in a viva.*

Everything below is in service of that one dish. Raw Recoll gives hits. Zotero
gives a shelf. Neither tells the researcher **which passage earns which sentence**,
or **how confident they are allowed to be**. That gap is what the backend fills.

---

## 1. The ingredients (inputs the researcher supplies)

| Ingredient | What it is | What the backend does NOT assume |
|---|---|---|
| **Corpus** | ~53 GB, ~12,594 unique docs across drives | that folder/title/tag = content. Metadata is a *clue*. |
| **Zotero library** | 1,841 items, collections, tags, some with PDFs + notes | that a Zotero tag is a verified concept |
| **Recoll index** | desktop full-text search, 45,467 items | that rank = truth. Rank is a *relevance clue*. |
| **A research question** | one sentence, the aim of the paper/chapter | that it is fixed — it sharpens as evidence arrives |
| **A claim / sub-claim** | the specific thing to be defended | that it is true until text supports it |
| **A layer intent** | is this empirical (Layer A) or method/theory (Layer B)? | that the researcher pre-knows — the backend can propose |

**Minimum viable order.** The researcher needs to supply only two things to start
cooking: a **research question** and a **layer intent** (empirical vs method). The
claim can be discovered during retrieval. Everything else the backend already holds.

---

## 2. The kitchen (what the backend turns ingredients into)

The backend runs a fixed pipeline. Each station is already built and sealed in the
ledger; the recipe just names them in the order the researcher meets them.

```
research question
      │  (kaleidoscope: corpus turns to face the question)
      ▼
[1] RETRIEVAL          Recoll lens → ranked hits          → clue score, never evidence
      │
      ▼
[2] VERIFICATION QUEUE  candidate rows, deduped            → queued, awaiting approval-to-sample
      │  (human approves what is worth reading)
      ▼
[3] SAMPLING           bounded read: front-matter + intro  → evidence grade: sampled_text_*
      │                + concept probe
      ▼
[4] DISPOSITION         two axes: is the thesis accurate?   → core_candidate / peripheral /
      │                 is it in domain?                       out_of_domain / review_required
      ▼
[5] FUNCTIONAL ROLE     what does this text DO for IR?      → anchor / mechanism / case / lens / foil
      │
      ▼
[6] CLAIM + LEDGER      every step sealed, hash-chained     → citable, defensible, reproducible
```

The researcher never sees SQL. They see: *"you asked X; here are 6 texts that earn
it, 2 are anchors, 1 contradicts you, all sampled, all provenance-stamped."*

---

## 3. Recipe A — writing one paper section

1. **State the sentence you want to write.** ("Post-Soviet Central Asian security
   is best read through geopolitical-imagination, not balance-of-power.")
2. **Backend turns the corpus** — one Recoll lens built from the sentence's own
   terms. Returns ranked clues, deduped across drives. *No PDF opened yet.*
3. **Researcher approves a sampling budget** — e.g. "read the top 5." This is the
   consent gate; the kaleidoscope never auto-reads.
4. **Backend samples** each approved text to a bounded slice and grades it.
5. **Backend dispositions** each: does it support your sentence, contradict it, or
   sit out of domain? A contradiction is surfaced, not hidden — that is the foil
   that makes the section defensible.
6. **Backend hands back a section-evidence card**: the sentence, the 5 texts, each
   with grade + functional role + one verified quote + provenance. That card is
   what the researcher writes from, and what a reviewer can re-run.

## 4. Recipe B — a PhD chapter (many sections, over weeks)

Same stations, but the ledger becomes the memory. Because every sample, grade, and
disposition is a sealed block, the researcher can **stop for a month and resume
without re-reading anything.** The chapter is assembled from cards; the bibliography
is generated from claims that reached `sampled_text` or higher; the "further reading"
is the verification queue that was never approved. The viva defense is the chain:
*every citation traces to a sampled passage and a block.*

---

## 5. What makes the experience *enriched* (backend obligations)

These are the seven things the backend must guarantee so the front end can feel
like a research companion rather than a search bar:

1. **Relevance honesty** — hits are labelled *clue*, with a clue score, never
   dressed as verified evidence. The researcher always knows what they are looking at.
2. **Consent gates** — nothing is read, graded, promoted, or adopted without an
   explicit approval. The corpus never runs ahead of the researcher.
3. **Two-axis truth** — "is the thesis accurate" is kept separate from "is it in my
   project." A brilliant out-of-domain book is marked accurate *and* excluded, not
   silently dropped. This is the distinction that stops the ontology becoming overconfident.
4. **Functional reading** — every kept text carries *what it does for the argument*
   (anchor / mechanism / case / lens / foil), not just an audit grade. A status is
   plumbing; the functional role is the meaning.
5. **Provenance to the passage** — every claim links to a sampled slice, a quote
   (verbatim-checked where the rubric demands), a file hash, and a block. Citable
   and viva-defensible.
6. **Kaleidoscopic freshness** — the corpus re-faces each new question; the same
   53 GB yields a different relevant slice per aim. The researcher is never asked
   "which of 12,000 books" — the question chooses.
7. **Resumable memory** — the ledger means the work survives interruption. Come back
   after weeks; the state is exactly as sealed.

---

## 6. The backend↔Codex contract (research semantics only)

Codex builds the surface; the backend must expose these objects so the surface has
something true to render. **Field names and statuses are backend-owned vocab;
Codex reads them, never invents them.**

| Object the front end shows | Backend source of truth | Governance rule the front end must respect |
|---|---|---|
| "Relevant now" panel | `verification_queue` + clue score | show as *clues*; label unverified |
| "Read this next" | queue rows at `queued` | approval-to-sample is a user action, not a click-through |
| Evidence card | `claim` + `verdict_disposition` + `functional_role` | never show `concept_verified`/`ontology_core` unless the row truly holds that grade |
| Confidence badge | `evidence_grade` + `thesis_confidence` | badge reflects the grade; do not round up |
| "What it does" tag | `functional_role.ir_function` | display the functional role, not only the audit status |
| Provenance trail | `block` chain + file hash + quote | every card links to its block; chain is read-only |
| Boundary notice | `boundary_proposal` status | show `proposed_*` as proposal, never as adopted doctrine |

**One rule above all for the front end:** the interface may *display* research
state but may never *create* it. Grades, dispositions, promotions, adoptions, and
samplings originate in the backend under user authority and are sealed in the
ledger. The front end is a window, not a hand.

---

## 7. What the researcher supplies vs. what is automatic

| Researcher supplies (human authority) | Backend does automatically (governed) |
|---|---|
| research question | build Recoll lens, rank, dedupe |
| layer intent (A/B) | propose layer, flag surprises as boundary candidates |
| approval to sample (budget) | bounded sampling + evidence grade |
| ruling on disposition | compute two-axis proposal, await ruling |
| ruling on promotion | register claim, seal block |
| ratification of boundary shifts | propose boundary refinement, never adopt |

The division is deliberate: **the machine does reach, memory, endurance, and
integrity; the researcher keeps judgement.** That is the exoskeleton doctrine of
the Charter, expressed as a daily workflow.

---
*Design note, not evidence-bearing. Backend feedback for the Codex front-end team.
Authored 2026-07-09. Changes no corpus or ledger state.*
