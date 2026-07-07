# KNOWLEDGE PRISM — Stage 4 Verification Rubric (v2, supervisor-approved corrections)

**Purpose.** Take 392 bridge-concept rows from `hypothesis_only` (a folder- and
title-guess about what each book argues) to *claims that have been sampled and
evidence-graded against the text.* This is the first stage where we read the
text instead of the metadata.

**The object under test is the CLAIM, not the book.** We are not "verifying a
book." We are testing the AI-generated claim *about* a book: does the sampled
text support the hypothesized thesis, and are the hypothesized concepts actually
present? A row's outcome is therefore always phrased as "claim sampled and
evidence-graded," never "book verified."

**Scope of the queue:** 392 rows — 220 theory, 70 mixed, 57 empirical,
45 method — across 7 folders (IR Theory 167, cognitive philosophy 66, Social
Science Theories & Geography 63, semiotics 36, research methods 32, classical
political philosophy 17, Advaita Vedanta & IR 11). Each row carries an
AI-generated `thesis` (median 216 chars) and a `concepts` list (median 6).

**Nothing here is executed yet.** This document is the standard. On approval it
is sealed as `block_0004`; even then, only the pilot list is generated — no
sampling, no promotion, no status changes until the pilot list is approved.

---

## 1. What counts as evidence (the sampling protocol)

For each book we sample a bounded, *reproducible* slice of text — not the whole
book (that is neither affordable nor necessary to verify a thesis claim):

| Slice | What | Why |
|-------|------|-----|
| **Front-matter** | title page, TOC, and the first ~2–3 pages of the preface/introduction | states the book's own claim about itself |
| **Introduction sample** | first ~2,500 words of chapter 1 / introduction | where the thesis is declared |
| **Concept probe** | for each hypothesized concept, the pages where the term (or a close variant) first appears — up to 2 short windows per concept | tests whether the *concept* is actually in the text, not just plausible from the title |
| **Extra chapter sample** *(theory-heavy books only)* | one additional ~2,000-word window around the densest cluster of relevant-concept hits (the page range where the most hypothesized concepts co-occur) | theory arguments are developed mid-chapter, not just declared in the intro; this is where a thesis is actually made or broken |

**Theory-heavy = axis `theory` or `mixed`** (290 of 392 rows). Those receive the
extra chapter sample; `empirical` and `method` books use front-matter + intro +
concept probes only unless the intro sample is inconclusive.

The exact page ranges and character offsets sampled are **recorded** with every
verdict, so any judgment can be re-checked against the same text later. That
recording is the difference between `frontmatter_seen` and an unfalsifiable
opinion.

---

## 2. The verdict taxonomy — three independent tracks

A claim has parts that must be judged separately. We do **not** collapse them,
and we do **not** require every concept to be found before a row counts as
sampled. Each row produces three distinct results:

### Track A — Thesis support (the main verdict)

| Verdict | Meaning | Resulting claim status | Evidence grade |
|---------|---------|------------------------|----------------|
| **SUPPORTED** | sampled text clearly states/argues the hypothesized thesis | `claim_sampled_supported` | `sampled_text` |
| **PARTIAL** | text supports part of the thesis, or a narrower version of it | `claim_sampled_partial` | `sampled_text` |
| **CONTRADICTED** | text argues something materially different from the hypothesis | `flagged_contradicted` *(human review required — never auto-applied)* | `sampled_text` |
| **ABSENT** | thesis not evidenced in the sampled slices (may exist in unsampled text) | `claim_sampled_insufficient` | `frontmatter_seen` |
| **UNREADABLE** | scanned/no text layer, corrupt, or wrong file | `blocked_unreadable` | `metadata_only` |

Note the deliberate wording: a row is **"claim sampled and evidence-graded,"**
never "book verified." We have sampled a slice and graded the claim against it;
we have not exhaustively read the book.

### Track B — Key-concept observation
The concepts the AI marked as central to the thesis. Each gets a tag:
`seen_in_text` · `variant_seen` · `not_found`. These are what the ontology may
later inherit — only concepts actually observed in text.

### Track C — Peripheral-concept absence
Concepts listed but not central. If `not_found`, that is **recorded, not
penalised** — a peripheral concept being absent from a text sample says nothing
against the thesis. Tracked purely so we know what was and wasn't seen.

A row is **"sampled"** once Track A has a verdict and Tracks B/C are tagged. It
does **not** require every concept to be found. Thesis support, key-concept
observation, and peripheral-concept absence are three separate facts.

---

## 3. The evidence-grade ladder (how a verdict promotes a claim)

```
metadata_only → metadata_manifest → hypothesis_only
   → frontmatter_seen → sampled_text → concept_verified
```

- A claim starts at `hypothesis_only`.
- ABSENT moves it to `frontmatter_seen` (we looked, text was reachable, thesis
  not evidenced in the sample) — an honest "not yet", not a rejection.
- SUPPORTED / PARTIAL move it to `sampled_text` (a text-grounded judgment).
- CONTRADICTED is graded `sampled_text` but its status stays
  `flagged_contradicted` until a human adjudicates — the grade records that we
  read text, the status records that no rejection is final without human sign-off.
- `concept_verified` is reserved for a **later** stage requiring deeper reading
  than a sample — it is never assigned by this stage.

A claim is usable as scholarly evidence only at `sampled_text` or above, and only
when its Track-A verdict is SUPPORTED or PARTIAL. Reaching `sampled_text` means
*the claim has been sampled and evidence-graded* — not that the book is
"verified."

---

## 4. What gets recorded (verdict schema)

Every verdict is written as an **append-only** transaction in the ledger — one
`claim` per book-thesis, and a `claim_event` per verdict, so re-verification
never erases the prior judgment:

```json
{
  "book_file": "Agents structures & international relations.pdf",
  "folder": "International Relations Theory",
  "axis": "theory",
  "hypothesized_thesis": "...",
  "verdict": "SUPPORTED | PARTIAL | CONTRADICTED | ABSENT | UNREADABLE",
  "confidence": 0.0-1.0,
  "thesis_verdict": "SUPPORTED | PARTIAL | CONTRADICTED | ABSENT | UNREADABLE",
  "confidence": 0.0-1.0,
  "argument_quote": "<=25-word verbatim span evidencing the THESIS (argument evidence)",
  "argument_locator": {"pages": [14], "char_span": [...]},
  "key_concepts": {"agent-structure problem": {"tag":"seen_in_text","term_quote":"...","page":2},
                   "structuration theory":   {"tag":"variant_seen","term_quote":"...","page":31}},
  "peripheral_concepts": {"elite choice-processes": "not_found"},
  "reviewer": "AI-first-pass | human_review",
  "basis": "sampled_text",
  "notes": "..."
}
```

**Two kinds of evidence, kept distinct (the "no quote, no promotion" rule
preserved but split):**

- **Argument evidence** (`argument_quote`) — a verbatim span (≤25 words) showing
  the text actually *makes the thesis argument*. Mandatory for a Track-A
  SUPPORTED/PARTIAL/CONTRADICTED verdict. A term appearing is **not** argument
  evidence; the quote must carry the claim, not just the vocabulary.
- **Term evidence** (`term_quote` per concept in Track B) — a short verbatim span
  showing the *concept term* (or a close variant) is present. This supports a
  `seen_in_text` / `variant_seen` tag only. It does **not** by itself promote the
  thesis.

No argument quote → no thesis promotion. No term quote → no `seen_in_text` tag.
The anchor holds at both levels; we simply never let term presence masquerade as
argument support.

- **`confidence`** below **0.75** is auto-flagged for human review rather than
  auto-accepted.

---

## 5. Two-tier review (AI first pass, human adjudication)

1. **AI first pass** — the **stronger reasoning model** reads the sampled slices
   and returns the schema above. (The pilot uses the reasoning model, not the
   utility model: thesis adjudication is genuine judgment work, and the pilot's
   purpose is to see the best available reading quality before scaling.)
2. **Auto-accept** only when: Track-A verdict ∈ {SUPPORTED, PARTIAL},
   confidence ≥ **0.75**, and a valid `argument_quote` is present.
3. **Route to mandatory human review** when: **CONTRADICTED (always — no AI
   contradiction verdict may auto-reject a claim)**, confidence < 0.75, ABSENT on
   a high-value theory book, or any UNREADABLE. You get a compact queue of just
   these.
4. Every human decision appends its own `claim_event` (reviewer =
   `human_review`) — the AI pass is never silently overwritten, it is
   *superseded on the record.*

This keeps scholarly authority with you while the AI does the reading labour, and
it keeps the strongest/riskiest calls — every rejection, and anything below 0.75
— under your eye.

---

## 6. Pilot before scale

The first run is a **pilot of ~15–20 books** drawn from the load-bearing theory
folders (IR Theory, general systems theory, semiotics). We inspect the verdicts
together, confirm the quotes are real and the grades are right, tune the
confidence threshold, and only then run the remaining ~370. Budget and method
are both validated before the large spend.

---

## 7. Open parameters for your decision

1. **Sample depth** — is front-matter + intro + concept probes enough, or do
   you want a deeper chapter sample for the 220 theory books?
2. **Confidence threshold** — default 0.6 for auto-accept; raise for stricter
   scholarship, lower to reduce your review queue.
3. **Concept granularity** — verify the *thesis* only, or also require every
   listed concept to be text-tagged before a book is "done"?
4. **Reviewer model** — the per-book reading can use the utility model (cheap,
   large batch) or the reasoning model (better judgment, higher cost). Pilot
   will show which is adequate.
5. **Rejection standard** — should CONTRADICTED always require human sign-off
   (recommended), or may high-confidence AI rejections auto-record?
