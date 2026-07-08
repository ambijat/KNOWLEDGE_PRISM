# FUNCTIONAL IR INTERPRETATION PROTOCOL

**Status:** doctrine (supervisory correction, 2026-07-07). Sealed as a ledger block.
**Scope:** governs every promoted, reviewed, or excluded item from this point forward.
**Relationship to the ledger:** the database, dispositions, evidence grades, and hash-chain remain necessary support systems. They are **subordinated to interpretation**, not the subject of it. A status such as `sampled_text_supported_core_candidate` is an *audit grade* — it certifies how well we have looked at a text. It does **not** explain why the text matters to International Relations. This protocol supplies the missing layer.

---

## 0. The correction, stated plainly

KNOWLEDGE_PRISM had drifted into **corpus anatomy**: tables, dispositions, ledgers, blocks, evidence slices. That is infrastructure. It is not the intellectual centre of a social-science / International Relations project.

The project now shifts from **corpus anatomy to corpus functionality** — from cataloguing what exists to explaining *how geopolitical knowledge functions*: how actors, regions, concepts, theories, texts, and evidence interact to explain International Relations, with an empirical centre of gravity in Eurasia, Afghanistan, and Central Asia.

The front end and the Codex handover must reflect this: not a forensic database of dead files, but a **living research machine** — evidence-supported concepts circulating between empirical regions, theories, methods, and IR questions.

---

## 1. Three registers of the corpus

The project must be legible at three levels. Each answers a different question and uses a different apparatus.

### 1.1 Corpus anatomy — *what exists*
The static inventory. Which texts, folders, concepts, and axes are present; their metadata, dispositions, and evidence grades. This is the register the ledger tables already serve (`master_corpus`, `bridge_concepts`, `verdict_disposition`, `disposition_taxonomy`, the block-chain). Anatomy answers **"is it there, and how well have we verified it?"**

### 1.2 Corpus physiology — *how evidence and concepts circulate*
The flow layer. How a concept moves along the evidence ladder (`provisional_unverified → sampled_text_supported_core_candidate → concept_verified → ontology_core`); how a claim is registered, advanced, or rejected; how a disposition routes a text into core, periphery, or exclusion. Physiology answers **"how does evidence enter, move, and mature — or get filtered out?"** The two-axis disposition model (thesis accuracy × project relevance) is a physiological mechanism: it regulates what circulates into the core.

### 1.3 Corpus biomechanics — *how concepts, actors, regions, and theories interact to produce explanation*
The explanatory layer, and the intellectual centre. How territory, state expansion, identity, security, connectivity, empire, and discourse **act on one another** to explain outcomes in Eurasia / Afghanistan / Central Asia and in IR knowledge structures. Biomechanics answers **"what does this text let us explain, and in combination with what?"** This is where the project earns its standing as IR scholarship rather than archive management.

> Rule of subordination: anatomy and physiology exist to feed biomechanics. Never report a row by its status alone. Always carry the functional reading.

---

## 2. The functional-role field (required for every live item)

For each promoted, reviewed, or excluded item, record a functional interpretation answering five questions:

1. **IR function** — what function does this text perform in International Relations?
2. **Contribution type** — one or more of: *empirical explanation, theoretical framing, methodological apparatus, conceptual genealogy, historical context, discourse/knowledge construction.*
3. **Interaction illuminated** — which interaction does it light up: *state-space, region-security, empire-frontier, identity-order, connectivity, conflict, knowledge production, actor behaviour.*
4. **Layer, substantively** — does it speak to Layer A (empirical: Afghanistan / Central Asia / Eurasia / connectivity), Layer B (method/theory for IR), or Layer AB — argued in substance, **not merely as a label**.
5. **Explanatory contribution** — how does it help build an explanatory framework for Eurasia, Afghanistan, Central Asia, geopolitics, or IR knowledge structures?

These are stored in the persistent `functional_role` table (survives derived rebuilds) and rendered in the functional-role table deliverable. The evidence grade sits **beside** the functional reading, never in place of it.

### Worked example (the standard to meet)
> **Do not say:** "Ratzel: review_required, confidence 0.55."
> **Say:** "Ratzel is potentially important as a *genealogy of political geography and geopolitical reasoning*. Its possible function is to explain how territory, state expansion, demographic imagination, and spatial power entered IR/geopolitical thought. The current evidence is weak; therefore deeper sampling is needed before admitting it into the theory-method layer."

The audit grade still exists — but it is the *last* clause, not the whole sentence.

---

## 3. How this changes the workflow

- **Promotion** now requires a functional reading, not just a passed evidence gate. A text can be `sampled_text_supported_core_candidate` and still owe an account of *what IR work it does*.
- **Exclusion** is also interpreted: an out-of-domain text (`claim_supported_but_project_irrelevant`) is excluded *because its function lies outside the IR biomechanics*, and we say so — the exclusion itself becomes a boundary statement about the domain.
- **Review / re-sample** targets are framed by their *potential* function (what we would gain if the evidence firmed up), so re-sampling is goal-directed, not mechanical.
- **The front end** presents concepts and their interactions (regions ↔ theories ↔ methods ↔ IR questions), with evidence grade as a confidence annotation on each edge — a living machine, not a file registry.

Do not discard the ledger. Subordinate it to interpretation.
