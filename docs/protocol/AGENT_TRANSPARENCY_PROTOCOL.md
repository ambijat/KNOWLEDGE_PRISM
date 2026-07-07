# Agent Transparency Protocol

## Purpose

Knowledge Prism should be legible to any future AI agent or human visitor.

No agent should be able to quietly change the project, promote claims, alter
ontology, or use hidden reasoning without leaving a recoverable trace.

This protocol defines how every meaningful action should be logged, checked, and
sealed.

## Core Principle

The project uses blockchain philosophy, not public blockchain deployment.

That means:

- every important action is append-only,
- each log record links to the previous record by hash,
- project milestones are sealed as hash-chained ledger blocks,
- generated artifacts are fingerprinted,
- claims are promoted only through explicit claim events,
- hidden intent is treated as a protocol violation.

The goal is not financial decentralisation. The goal is epistemic
transparency.

## The Trust Problem

AI agents can be useful, but they can also:

- silently change files,
- overstate what they verified,
- treat guesses as knowledge,
- hide uncertainty,
- import outside claims without grading them,
- perform broad actions without explaining why,
- leave future agents unable to reconstruct what happened.

Knowledge Prism prevents this by requiring a visible trail from intention to
artifact.

## The Action Ladder

Every non-trivial agent action should pass through this ladder:

```text
intent -> scope -> action -> artifact -> evidence grade -> log record -> ledger block
```

Not every tiny keystroke needs its own block. But every meaningful task should
leave an action-log record, and every completed work package should be sealed as
a provenance block.

## Mandatory Shift-Start Ritual

Every future agent shift must begin with:

```bash
python3 scripts/05_start_agent_shift.py \
  --task-id "<short-task-id>" \
  --intent "<why this shift is starting>" \
  --scope "<expected file or area>"
```

This is the project rally point. It runs the restore briefing, verifies the
action-log chain, verifies the milestone ledger, logs the new task intent, and
verifies the action log again.

No agent should edit files, run corpus verification, alter ontology, change the
GUI, or promote claims before this start ritual succeeds.

## What Must Be Logged

Log these actions:

- creating or editing project documents,
- creating or editing scripts,
- changing `index.html`,
- generating reports or manifests,
- mapping corpus rows,
- extracting text,
- importing verdicts,
- promoting or rejecting claims,
- adding ontology nodes or edges,
- adding external-source material,
- changing project protocol,
- changing evidence-grade rules,
- changing GUI behaviour,
- sealing a ledger block.

Do not log trivial reading actions unless they produce a decision, artifact, or
project state change.

## The Action Record

Each action-log record should include:

| Field | Meaning |
|---|---|
| `ts` | ISO timestamp |
| `actor` | `codex`, `human`, `script`, or named agent |
| `task_id` | Stable task label |
| `action_type` | `inspect`, `edit`, `generate`, `verify`, `seal`, `decide`, `promote`, `reject` |
| `intent` | Why the action was taken |
| `scope` | Files, tables, or concepts affected |
| `inputs` | Source files or sources used |
| `outputs` | Files or records produced |
| `commands` | Important commands run |
| `evidence_grade` | Evidence level of the action or claim |
| `hidden_io` | Whether any hidden network, secret, or off-ledger input was used |
| `notes` | Short explanation |
| `prev_record_hash` | Hash of previous action record |
| `record_hash` | Hash of this action record |

The `hidden_io` field should normally be `false`. If it is ever `true`, the
record must explain why.

## Evidence Rules For Agent Actions

Agent actions inherit the project's evidence discipline.

Allowed grades:

- `infrastructure`: scripts, GUI, protocol, validation tools.
- `metadata_only`: file names, folders, titles, paths.
- `metadata_manifest`: structured registers or manifests.
- `hypothesis_only`: AI-generated or unverified interpretive claim.
- `frontmatter_seen`: front matter inspected.
- `sampled_text`: text sample inspected.
- `analysis`: computed or reasoned analysis.
- `concept_verified`: concept checked against textual evidence.

An agent must not promote a claim to `concept_verified` from interface play,
metadata, graph proximity, or stylistic plausibility.

## The No Hidden Agenda Rule

Every agent should make its purpose visible before acting.

For significant work, the agent should state:

```text
I am doing X
because Y
using inputs Z
and I will produce outputs A/B/C.
```

If a future agent cannot explain why an action was taken, that action should not
be treated as authoritative.

## External Information Quarantine

External claims must be quarantined until graded.

For example:

- tweets,
- news reports,
- blog posts,
- Reddit posts,
- model-company claims,
- political or commercial allegations.

These may inspire workflow improvements, but they must not become ontology facts
unless they pass through the project's evidence process.

External information should be logged with:

- source,
- date accessed,
- claim type,
- confidence,
- whether it affects project ontology,
- whether it is only methodological inspiration.

## GUI Transparency Requirements

The GUI must remain honest.

It may:

- inspire ideas,
- show graph relations,
- assemble provisional arguments,
- export learning notes,
- surface evidence grades.

It must not:

- imply that graph proximity is proof,
- hide weak evidence,
- promote metadata claims,
- silently send project data elsewhere,
- obscure how synthesis was generated.

Every GUI export should preserve:

- selected nodes,
- evidence grades,
- synthesis,
- weak evidence warning,
- next verification task.

## Ledger Levels

Knowledge Prism uses two levels of provenance.

### Level 1: Action Log

The action log is granular.

It records meaningful actions in:

```text
logs/agent_actions.jsonl
```

Each row is hash-linked to the previous row.

### Level 2: Provenance Blocks

The ledger block is milestone-level.

It records completed work packages in:

```text
db/knowledge_prism.db
ledger/blocks/*.json
```

Use blocks for:

- completed protocols,
- generated datasets,
- GUI revisions,
- verification batches,
- ontology promotions,
- published reports.

## Required Commands

After non-trivial work:

```bash
python3 scripts/04_log_agent_action.py log ...
python3 scripts/04_log_agent_action.py verify
python3 db/prism.py verify
```

After project milestones:

```bash
python3 db/prism.py blocks
python3 db/prism.py claims accepted
```

## Stop Conditions

An agent must stop and ask for human direction if:

- a file contains secrets and the task does not require reading them,
- an ontology claim would be promoted without textual evidence,
- an external claim is politically or commercially loaded and unverified,
- a script would delete or overwrite prior provenance,
- a change would make the ledger unverifiable,
- the agent cannot explain the intent of a requested action.

## Definition Of Transparent Work

Work is transparent when:

- the intent is visible,
- the scope is bounded,
- the files changed are known,
- the evidence grade is explicit,
- generated artifacts are named,
- commands can be rerun,
- the action log verifies,
- the provenance chain verifies,
- a future agent can reconstruct what happened.

## The Project Oath

For Knowledge Prism, a good agent does not merely produce.

A good agent leaves a trail.

The trail must be clear enough that another intelligence can enter the project,
inspect the record, and say:

```text
I know what happened.
I know why it happened.
I know what evidence supported it.
I know what remains provisional.
```

That is the standard.
