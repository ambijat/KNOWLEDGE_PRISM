# Recoll Kaleidoscope — Trial 001

**Status:** governed retrieval trial (retrieval stage only). No evidence state changed.
**Date:** 2026-07-08
**Protocol:** docs/protocol/RECOLL_KALEIDOSCOPE_PROTOCOL.md
**Cardinal rule:** every Recoll hit is a *clue*, not scholarly evidence. Evidence exists only when text is seen under the Verification Rubric.

---

## 1. Research question
> How does geopolitical thinking about Russia, Central Asia, frontier space, and regional order help explain the making of Eurasian security imaginaries?

## 2. Query lens used
The lens conjoins four semantic bands — a Russia/Eurasia actor band, a Central-Asia spatial band, a frontier/regional-order band, and a geopolitical-imagination/security band — so that a hit must touch all four to rank. This is a *relevance filter*, not a claim about content.

## 3. Recoll query string used
```
(russia OR russian OR eurasia OR eurasian) AND ("central asia" OR turkestan OR "the stans") AND (frontier OR borderland OR "near abroad" OR "regional order" OR "regional security") AND (geopolit* OR imaginary OR imagination OR heartland OR security)
```
Run with the local Recoll configuration and `recollq -F "url title" -n 60`. One query cycle only. Local configuration paths are intentionally not published.

## 4. Number of hits returned
- **1,081** total results in the live index (`dbtotdocs = 45,467`).
- Top 60 pulled; **48 unique** after basename de-duplication (the same book recurs across SOLEMON drives — Winstore / GHANA_B / BOOKLIBDATA).
- Top 25 uniques scored and carried into this report.

## 5. Top candidate hits
Clue-score = 0.5·rank + 0.25·novelty + 0.25·project-fit (all in [0,1]). Rank is the Recoll relevance order (relevancerating field was not emitted by this build, so rank position is the relevance signal).

| rank | clue | layer (prior) | novelty | candidate |
|---|---|---|---|---|
| 1 | 0.75 | Ambiguous | in corpus | The Return of Geopolitics in Europe? |
| 2 | 0.86 | A | in corpus | 02papava.indd |
| 3 | 0.74 | Out-of-domain | new | 0034_20260113_1000_Output_File_Organization.txt |
| 4 | 0.72 | Ambiguous | in corpus | Empire De/centrered |
| 5 | 0.83 | A | in corpus | PDF-file: Dmitri Trenin. The End of Eurasia: Russia on the |
| 6 | 0.82 | A | in corpus | A Geopolitical Perspective on Central Asia-China Relations |
| 7 | 0.81 | B | in corpus | Geopolitics and International Relations Grounding World Po |
| 8 | 0.80 | A | in corpus | The Belt and Road Initiative; Geopolitical and Geoeconomic |
| 9 | 0.79 | A | in corpus | PDF-file: Dmitri Trenin. The End of Eurasia: Russia on the |
| 10 | 0.78 | A | in corpus | New Central Asia |
| 11 | 0.65 | Ambiguous | in corpus | Geopolitics |
| 12 | 0.76 | B | in corpus | Great Powers and Geopolitics International Affairs in a Re |
| 13 | 0.75 | A | in corpus | 460541_1_En_Print.indd |
| 14 | 0.61 | Ambiguous | in corpus | FGEO11(1).book(FGEO_A_152395.fm) |
| 15 | 0.73 | A | in corpus | FGEO11(1).book(FGEO_A_152395.fm) |
| 16 | 0.72 | A | in corpus | central-asia-is-a-region-of-five-stans-dispute-with-kazakh |

## 6. Why each top hit appears relevant
The lens is aimed correctly. The strongest signals are squarely on the research question:
- **Trenin, *The End of Eurasia: Russia on the Border Between Geopolitics and Globalization*** (ranks 5 & 9) — Russia/Eurasia/post-Soviet frontier, the exact conceptual spine of the RQ. See §Supervisory Observation below.
- **A Geopolitical Perspective on Central Asia–China Relations** (rank 6) — regional order + connectivity.
- **The Belt and Road Initiative: Geopolitical and Geoeconomic Aspects** (rank 8) and **China's Belt and Road Vision** (rank 13) — connectivity/regional-order axis.
- **The New Central Asia** (rank 10) — regional formation and post-Soviet spatial order.
- **Geopolitics and International Relations: Grounding World Politics** (rank 7) and **Great Powers and Geopolitics** (rank 12) — Layer-B theory/method framing of geopolitical reasoning.

## 7. Layer classification of each hit
Assigned by a transparent path/title keyword prior — **a clue, overridable, not a verdict**:
- **Layer A (empirical Eurasia/Central Asia/connectivity):** ranks 2, 5, 6, 8, 9, 10, 13, 15, 16 …
- **Layer B (theory/method):** ranks 7, 12.
- **Ambiguous** (title too thin to classify from metadata): ranks 1, 4, 11, 14.
- **Out-of-domain (genre noise):** rank 3 — a ChatGPT session export `.txt`, not scholarship.
Layer AB is reserved for texts that substantively fuse empirical Eurasia with theory/method; Trenin is the leading AB candidate pending text.

## 8. Grey-zone judgement notes
Logged as *observations only* (no evidence-ledger entry):
- **Rank 3 — ChatGPT export `.txt`.** High lexical relevance, high novelty (unseen), but non-scholarly genre. Grey-zone call: **drop from candidate consideration**; retrieval matched a conversation transcript that merely discusses these terms. This is exactly the "relevance ≠ evidence" gap the cardinal rule guards.
- **Empty-title hits (ranks 7, 12, 16, etc.).** Metadata title missing; identity taken from filename/folder. Legible, kept, but flagged that title-based fit is provisional.
- **Duplicate anchor (Trenin at 5 and 9).** Same book, two drives. Treated as one work; the duplication is itself corpus-hygiene signal, not two sources.

## 9. Boundary-surprise notes
- The genre-noise hit (ChatGPT export) is a **boundary-learning candidate**: the project's out-of-domain filter should explicitly recognise self-generated transcripts/exports as noise, so they never dilute a candidate set.
- **Layer boundary surprise (see Trenin observation):** the strength of the Russia/Eurasia/post-Soviet-order cluster suggests the Layer A / Layer AB boundary should explicitly name *Eurasian security imaginaries* and *post-Soviet spatial order* as **central**, not peripheral.

## 10. Recommended candidates for future verification queue
Proposed for later text sampling (order = clue-score), **not entered into any queue by this trial**:
1. **Trenin, *The End of Eurasia*** — anchor candidate (see below).
2. A Geopolitical Perspective on Central Asia–China Relations.
3. The Belt and Road Initiative: Geopolitical and Geoeconomic Aspects.
4. The New Central Asia.
5. Geopolitics and International Relations: Grounding World Politics (Layer B).

## 11. State-change confirmation
No text was sampled. No evidence grade was assigned or changed. No disposition was created or modified. Nothing was promoted. No ontology-core action occurred. No ledger block was sealed. This trial changed **no** evidence or ontology state. Outputs are the report and CSV only.

---

## Supervisory Observation: Trenin as Anchor Piece

Per supervisory direction, **Trenin, *The End of Eurasia: Russia on the Border Between Geopolitics and Globalization*** is recorded not as an ordinary retrieval hit but as a **`kaleidoscope_anchor_piece` / `anchor_candidate`**. It surfaced at ranks 5 and 9 of the very first governed retrieval cycle.

Its functional significance is that it connects, in a single work, the concepts the research question holds together: **Russia, Eurasia, post-Soviet space, Central Asia, regional order, geopolitical imagination, and security imaginaries.** It plausibly anchors the Eurasian/Russia/Central-Asia geopolitical lens for the whole project.

Recorded carefully, with explicit limits:
1. Trenin is **not yet verified**.
2. Trenin is **not yet promoted**.
3. Trenin is **not ontology-core**.
4. Recoll has surfaced it **only as a highly relevant candidate**.
5. Its functional role is nonetheless **stronger than a normal hit**: it anchors the Eurasian / Russia / Central-Asia geopolitical lens.
6. It is **recommended for future verification-queue entry** (retrieval-stage recommendation only).
7. **Boundary-learning observation:** the project's Layer A / Layer AB boundary should explicitly recognise *Eurasian security imaginaries* and *post-Soviet spatial order* as **central, not peripheral**. This is logged as a candidate boundary movement (move-on-surprise), to be ratified — not enacted here.

CSV marking: the two Trenin rows carry `notes = anchor_candidate=yes; kaleidoscope_anchor_piece; recommend future verification-queue entry`.

**This remains a retrieval-stage scholarly observation only.** It authorises no sampling, grading, disposition, promotion, or ontology change.
