# Obsidian Vertical Slice (SYNTHETIC fixture)

This directory is a **synthetic** projection package that exercises the whole
Obsidian integration contract end to end. Nothing here is drawn from the live
corpus — every record is marked `[SYNTHETIC]`. It exists so Codex can build and
test the frontend against a fixed, schema-valid target before any real
projection is authorised.

## Contents

- `export_manifest.json` — index-of-truth (counts, record list, id_crosswalk).
- `records/` — 12 projection records: 2 sources, 3 concepts (1 researcher
  synthesis), 3 entities, 4 claims. Five typed relationships across them
  (`associated_with`, `defines`, `fuses_with`, `located_in`, `supports`).
- `notes/` — one generated Obsidian note per record, each with a
  `KP:GENERATED` region and a preserved `RESEARCHER:NOTES` region. The
  `CON-000003` synthesis note carries a researcher-authored paragraph that must
  survive regeneration.
- `proposals/inbox/PROP-000001.json` — one proposed relationship
  (`constrains`) awaiting review. It is NOT canonical.
- `proposals/{accepted,revised,rejected,receipts}/` — lifecycle destinations.
- `vertical_slice.canvas` — an Obsidian Canvas linking the real note files,
  with relationship-labelled edges.

## Milestone checks this fixture supports

1. Canonical records → correct notes (record_type mapping).
2. Provenance visible (status + origin_table in every note header).
3. Researcher annotations survive regeneration (protected-region merge).
4. Proposed relationship enters the review inbox (PROP-000001).
5. Proposal is not auto-canonical (status `proposed`; no DB write).
6. Accept/reject reflected back (decision receipt schema + lifecycle dirs).
7. Canvas links to real note files.

## Validate

```
python scripts/08_validate_obsidian_projection.py all \
    docs/protocol/examples/obsidian_vertical_slice
```
