# Knowledge Prism

## Preamble For A Visitor

Welcome to Knowledge Prism.

This project is a museum of ideas, but not a quiet museum where objects sit
behind glass. It is closer to an active workshop: a place where books, concepts,
regions, actors, theories, methods, and evidence traces are arranged so that a
larger intellectual structure can gradually become visible.

At first glance, Knowledge Prism may look like a collection of files. It is more
than that. It is an attempt to transform a scattered scholarly archive into a
researchable map of geopolitical knowledge.

The central question is:

> How can a large archive become a disciplined field of ideas without pretending
> that every document has already been read?

Knowledge Prism answers by building an auditable path from clue to claim.

## The Whole Idea

The project studies how geopolitical knowledge is organised, represented, and
made meaningful in International Relations, using Afghanistan, Central Asia, and
Eurasia as its empirical core.

Its methodological apparatus includes:

- International Relations theory,
- regional security complex theory,
- critical geopolitics,
- systems theory,
- semiotics,
- network analysis,
- grounded theory,
- AI-assisted ontology building.

The project is not simply asking what is in the archive. It is asking how the
archive thinks.

It treats texts, folders, concepts, metadata, maps, and citations as pieces of a
larger knowledge system. These pieces can be sorted, connected, verified, and
eventually assembled into an ontology: a structured account of what kinds of
regions, actors, processes, theories, methods, and knowledge objects the archive
contains.

## The Museum Metaphor

Imagine entering a museum.

In the first gallery, you see the archive as terrain: thousands of files,
folders, registers, and bibliographic records. This is the reconnaissance
gallery.

In the second gallery, you see the same archive turned into a master register.
Items are counted, classified, deduplicated, and assigned evidence grades. This
is the catalogue room.

In the third gallery, you see a ledger. Every claim must state how it was
created, what evidence supports it, and whether it is provisional or accepted.
This is the conservation lab, where nothing is silently altered.

In the fourth gallery, you see the verification queue. Here, AI-generated bridge
claims wait to be checked against actual text. This is the reading room.

In the fifth gallery, you see the graph lab. Concepts appear as movable nodes.
Regions, actors, theories, methods, and evidence objects can be assembled like
building blocks. This is the interactive exhibition.

In the final gallery, still under construction, the verified ontology will
appear: a map of the archive's knowledge structure, grounded in textual
evidence.

## What The Project Contains

Knowledge Prism currently contains several layers.

### 1. The Corpus Layer

This is the archive-facing layer.

It includes:

- Zotero bibliographic records,
- Recoll-indexed corpus material,
- SOLEMON filesystem crawl data,
- raw inherited artifacts,
- a master corpus register,
- duplicate-candidate information,
- preliminary corpus classes.

This layer tells us what the project appears to possess. It does not by itself
prove what the texts argue.

### 2. The Evidence Layer

This is the discipline layer.

Every claim is assigned an evidence grade. The project distinguishes between:

- metadata-only clues,
- manifest-level information,
- hypothesis-only bridge claims,
- sampled text,
- analysis,
- concept verification.

This matters because the project refuses to treat folder names, titles, or AI
summaries as final scholarly evidence.

### 3. The Verification Layer

This is where the archive begins to become scholarship.

The project contains a queue of 392 bridge-concept claims. These are provisional
claims generated from earlier reconnaissance. They are useful, but they are not
yet evidence.

The next work is to open the actual PDFs, sample front matter and chapter text,
test the proposed thesis, and record whether each claim is supported, partially
supported, contradicted, absent, or unreadable.

### 4. The Ontology Layer

This is the conceptual architecture.

The project organises knowledge through classes such as:

- Empirical Region,
- Actor,
- Process,
- Theory,
- Method,
- Knowledge Object,
- Pedagogic Use.

The current ontology is provisional. It becomes stronger only when its nodes and
edges are supported by verified textual evidence.

### 5. The Interface Layer

This is the human-facing layer.

The `index.html` graph lab lets a visitor move concepts, inspect relations, add
nodes to an idea stack, and generate provisional syntheses. It is designed to be
playful, but not careless.

It teaches a habit:

> Build ideas freely, but always ask what evidence grade each piece carries.

### 6. The Provenance Layer

This is the memory of the project.

The SQLite database and ledger record:

- sealed provenance blocks,
- accepted and provisional claims,
- claim events,
- artifact hashes,
- retrievable deliverables.

The project is designed so that future sessions can restore the state, verify
the chain, and continue without relying on chat memory.

## The Main Attributes Of Knowledge Prism

Knowledge Prism is:

### Auditable

Every serious claim should be traceable. The project keeps a ledger so that
claims, outputs, and changes can be checked later.

### Evidence-Graded

Not all knowledge pieces are equal. A title is weaker than a sampled chapter. A
folder clue is weaker than a verified concept. The interface and documents keep
that hierarchy visible.

### Corpus-Based

The project begins from an actual archive rather than from abstract theory
alone. It asks what this particular body of material can support.

### Interpretive

The project is not merely counting files. It is asking how meaning, power,
region, theory, and method are organised through texts.

### Computational

The project uses registers, graphs, databases, hashes, and structured workflows
to make a large archive navigable.

### Philosophical

The project treats knowledge itself as an object of inquiry. It asks how regions
become thinkable, how concepts travel, and how methods shape what can be seen.

### Pedagogic

The project can also teach. It shows students and researchers how a messy
archive can be turned into a researchable domain without skipping the hard work
of verification.

## The Red Line

The most important rule is simple:

> A concept is only real when it has been seen in the text.

Until then, it is a clue, a hypothesis, or a possible path.

This rule protects the project from a common danger: making beautiful maps too
early. Knowledge Prism welcomes visualisation and play, but it does not confuse
visual elegance with scholarly proof.

## How To Enter The Project

If you are a visitor, begin in this order:

1. Read this preamble.
2. Open `index.html` and explore the graph lab.
3. Read `docs/KNOWLEDGE_PRISM_GUI_BROCHURE.md` to understand how to drive the
   interface.
4. Read `PIPELINE.md` to understand the evidence-gated workflow.
5. Read `ACTION_PLAN.md` to see what should happen next.
6. Run `python3 db/prism.py boot` if you are taking over the technical work.

This order lets you move from meaning to method, and then from method to
implementation.

## What A Visitor Should Learn

A visitor should leave with five insights.

First, a research archive is not automatically knowledge. It must be organised,
tested, and interpreted.

Second, metadata is useful but dangerous if treated as evidence too soon.

Third, AI can help generate hypotheses and maps, but verification must remain
explicit.

Fourth, an ontology should emerge from disciplined contact with texts, not from
folder names alone.

Fifth, research can be both playful and rigorous. The Lego-like play of the
graph lab is valuable precisely because the evidence ledger keeps it honest.

## The Invitation

Knowledge Prism invites you to walk through an archive as if it were a living
museum of geopolitical thought.

Move the pieces.

Notice the patterns.

Ask what the graph is tempting you to believe.

Then ask what the text can actually support.

That movement from imagination to evidence is the project.
