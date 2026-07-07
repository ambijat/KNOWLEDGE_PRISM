# Knowledge Prism Graph Lab

## A Brochure And Driver's Manual For The Human Interface

The `index.html` page is the human-facing cockpit of Knowledge Prism. It is not
only a web page. It is a thinking instrument: a place where concepts, regions,
actors, methods, theories, and evidence objects can be moved around until they
begin to form a larger idea.

Think of it like a modern car.

The engine is the project database and evidence ledger. The road is the corpus.
The dashboard is the graph interface. The driver is the researcher. The point is
not to let the machine drive the research for you. The point is to give your
thinking better steering, better mirrors, better warning lights, and a clearer
sense of motion.

## Why This Interface Exists

Knowledge Prism is trying to solve a difficult research problem: how to turn a
large, scattered scholarly archive into a defensible knowledge structure without
pretending that every file has already been read.

The interface therefore has two jobs:

1. Make the project visually explorable.
2. Keep the evidence discipline visible while you explore.

The page lets you play with knowledge pieces like Lego blocks, but it also keeps
asking a serious question:

> Is this piece verified, or is it still only a clue?

That is the soul of the design.

## The Core Metaphor

The graph is a prism.

Each node is a knowledge piece. Each edge is a possible relationship. The glow
around a node suggests evidence strength. The idea stack is the structure you
are building. The synthesis panel turns that structure into a provisional
research sentence.

The interface is designed around this movement:

```text
knowledge piece -> relation -> cluster -> idea -> evidence question
```

Or, in project terms:

```text
metadata clue -> sampled text -> claim event -> ontology edge
```

## What You Are Looking At

### The Left Panel: The Garage

The left panel contains the available knowledge pieces.

You can search and filter by:

- regions,
- actors,
- processes,
- theories,
- methods,
- knowledge objects,
- evidence grades.

This is like choosing parts before assembling a machine. You are not yet making
an argument. You are selecting possible components.

### The Centre Graph: The Road And Engine Bay

The centre is the living graph simulation.

Nodes can be dragged. Edges pull related nodes toward each other. The graph moves
because the project is not a flat list; it is a field of relationships.

Important controls:

- `Pulse`: shakes the graph so hidden structures become visible.
- `Auto idea`: loads a starter argument.
- `Freeze`: stops the simulation so you can inspect the current arrangement.
- `Reset`: returns the graph to its initial layout.

The graph is intentionally dynamic. The motion helps you feel that concepts are
not isolated boxes. They exert pressure on each other.

### The Right Panel: The Dashboard

The right panel is the cockpit dashboard.

It shows:

- visible nodes,
- visible links,
- idea pieces,
- weak evidence,
- selected-node details,
- the current idea stack,
- philosophical synthesis modes,
- export controls.

If the centre graph is where you drive, the right panel is where you read the
instruments.

## The Controls Explained

### Click

Click a node to inspect it.

The selected-node panel will show:

- what type of piece it is,
- its evidence grade,
- its interpretive meaning,
- some nearby relations.

Use this when you want to understand one component before adding it to an idea.

### Double-Click

Double-click a node to add it to the idea stack.

The idea stack is the current argument under construction. A node in the graph is
only a possible piece. A node in the stack is a chosen piece.

### Drag

Drag nodes to test relationships visually.

For example, pull `Afghanistan` near `Regional Security`, then pull `Critical
Geopolitics` near both. Your eye will begin to see a possible research triangle:

```text
Afghanistan -> regional security -> representation
```

This is not proof. It is a way to generate a question worth verifying.

### Filter

Use filters when the graph becomes too busy.

For example:

- filter to `Theories` to ask what kind of explanation is available;
- filter to `Methods` to ask how the project can discipline interpretation;
- filter to `Knowledge objects` to inspect the evidence system itself.

### Philosophise Modes

The `Philosophise` panel has four modes.

`Thesis` gives you a provisional argument.

`Tension` tells you where the idea is weak or under-verified.

`Method` converts the stack into a possible research procedure.

`Pedagogy` explains how the same stack could be used as a classroom exercise.

These are not final writings. They are thinking modes.

## Evidence Grades As Warning Lights

In a modern car, warning lights tell you what needs attention before you drive
too fast. In Knowledge Prism, evidence grades do the same thing.

### Metadata Only

This means the piece is known from title, path, folder, or bibliographic clues.
It can inspire a question, but it cannot carry a scholarly claim.

### Metadata Manifest

This means structured metadata exists, usually from a register or manifest. It
is stronger than a loose clue, but still not textual evidence.

### Analysis

This means the project has computed or reasoned over a structure, such as the
eigenspace or graph relation. It can guide interpretation but still needs
careful grounding.

### Sampled Text

This means some part of the actual text has been inspected. This is where the
project begins to move from map to evidence.

### Concept Verified

This is the strongest level. It means a concept or claim has been checked
against text and recorded in the evidence system.

## The Basic Driving Lesson

Start here:

1. Press `Auto idea`.
2. Look at the idea stack.
3. Read the `Thesis`.
4. Click `Tension`.
5. Notice which pieces are still weak.
6. Drag the central nodes around.
7. Click one node and read its explanation.
8. Double-click another node to add it.
9. Read the thesis again.
10. Write one human sentence in `Human Notes`.

This is the simplest loop:

```text
assemble -> inspect -> question -> revise -> export
```

## Sandbox Routes

Use these routes like short driving exercises.

### Route 1: Just Move The Graph

1. Press `Pulse`.
2. Drag `Afghanistan` closer to `Regional Security`.
3. Drag `Critical Geopolitics` closer to both.
4. Watch how the graph suggests: region + security + representation.

Goal: feel that ideas are spatial, not only textual.

### Route 2: Build One Tiny Idea

Double-click:

- `Afghanistan`
- `Taliban`
- `Regional Security`
- `Realism`
- `Evidence Ledger`

Then click `Thesis`, followed by `Tension`.

Question to ask:

> What is strong here, and what is still only a clue?

### Route 3: Use The Graph Like A Prism

1. Filter to `Theories`.
2. Click `Critical Geopolitics`.
3. Read the selected-node panel.
4. Filter to `Methods`.
5. Click `Semiotics`.
6. Add both to the idea stack.

Goal: understand that theory explains what kind of seeing you are doing, while
method explains how you discipline that seeing.

### Route 4: Evidence Discipline

Add:

- `392 Bridge Claims`
- `Evidence Ledger`
- `Grounded Theory`

Then click `Method`.

Core idea:

```text
AI finds hypotheses.
Sampling tests them.
The ledger remembers what happened.
```

### Route 5: Make A Bigger Argument

Double-click:

- `Afghanistan`
- `China / BRI`
- `Connectivity Politics`
- `Critical Geopolitics`
- `Semiotics`
- `Evidence Ledger`

Then read the generated `Thesis`.

This route demonstrates the central design move:

```text
empirical object
+ actor
+ process
+ theory
+ method
+ evidence system
= researchable idea
```

### Route 6: Find Weakness

1. Build any idea stack.
2. Look at `Graph State`.
3. Notice `weak evidence`.
4. Click `Tension`.

The page is teaching this habit:

> Do not only ask what idea can be built. Ask which block is too weak to carry
> the argument.

### Route 7: Export A Thought

1. Build a stack you like.
2. Write one sentence in `Human Notes`.
3. Click `Copy brief` or `Download JSON`.

Goal: turn visual play into a reusable research note.

## How To Read The Interface

Use this quick translation table:

| Interface element | Meaning |
|---|---|
| Node | Knowledge piece |
| Edge | Possible relation |
| Glow | Evidence strength |
| Dragging | Testing conceptual proximity |
| Idea stack | Argument under construction |
| Weak evidence count | Warning light |
| Thesis mode | Provisional argument |
| Tension mode | Verification need |
| Method mode | Research procedure |
| Pedagogy mode | Teaching version |
| Export | Reusable research note |

## What The Interface Is Not

It is not a final ontology.

It is not proof that the displayed relations are true.

It is not a replacement for reading.

It is not a decorative graph.

It is a conceptual workbench for disciplined imagination.

## What The Interface Is

It is a place to rehearse ideas before they become claims.

It is a visual way to ask:

- What belongs together?
- What relation is emerging?
- Which method could test it?
- Which evidence grade is still too weak?
- What must be sampled next?

The ideal use of the page is playful but not careless. You should feel free to
move nodes, build stacks, and generate surprising combinations. But every time
an idea begins to look convincing, the interface should pull you back to the
project's central rule:

> A concept is only real when it has been seen in the text.

## The Modern Car Analogy

The page is like a concept car for research thinking.

The graph is the road.

The nodes are moving vehicles.

The edges are lanes of relation.

The evidence grades are dashboard warnings.

The idea stack is the route you are currently driving.

The synthesis panel is the navigation voice.

The ledger is the service record.

The human researcher is still the driver.

Good driving means not simply going fast. It means knowing when to accelerate,
when to brake, when to check the mirrors, and when to stop because a warning
light is on.

That is how this interface should be used.

## The One-Sentence Explanation

Knowledge Prism Graph Lab lets you move evidence-graded research concepts like
building blocks, assemble them into provisional ideas, and immediately see which
parts still need textual verification.
