#!/usr/bin/env python3
"""
08_validate_obsidian_projection.py — validate an Obsidian projection package.

Read-only with respect to research state. Never touches the SQLite DB. Operates
purely on the projection package (records + manifest), inbound proposals, and
generated notes.

Subcommands
-----------
  schema   Validate records / manifest / proposals against the JSON Schemas.
  merge    Validate protected-region merge for a generated note (and, with
           --apply-to-tmp, emit the merged result to a tmp file — never in place).
  all      schema over a package directory + merge dry-run over any .md notes.

Exit code 0 = all checks passed, 1 = at least one failure.

No third-party dependencies: a small draft-07 subset validator is bundled so
this runs anywhere the project's stdlib Python runs.
"""
import argparse
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Minimal JSON-Schema (draft-07 subset) validator.
# Supports: type, enum, const, required, properties, additionalProperties,
# items, pattern, minLength, minimum, allOf, if/then. Sufficient for the
# Knowledge Prism projection schemas; not a general-purpose implementation.
# ---------------------------------------------------------------------------
def _type_ok(value, t):
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path="$", errors=None):
    if errors is None:
        errors = []

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(instance, t) for t in types):
            errors.append(f"{path}: type {type(instance).__name__} not in {types}")

    if isinstance(instance, str):
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: {instance!r} does not match /{schema['pattern']}/")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for k in instance:
                if k not in props:
                    errors.append(f"{path}: additional property '{k}' not allowed")
        for k, subschema in props.items():
            if k in instance:
                validate(instance[k], subschema, f"{path}.{k}", errors)

    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            validate(item, schema["items"], f"{path}[{i}]", errors)

    for sub in schema.get("allOf", []):
        if "if" in sub:
            cond_errs = []
            validate(instance, sub["if"], path, cond_errs)
            if not cond_errs and "then" in sub:
                validate(instance, sub["then"], path, errors)
        else:
            validate(instance, sub, path, errors)

    return errors


# ---------------------------------------------------------------------------
# Protected-region merge (contract §8).
# ---------------------------------------------------------------------------
GEN_START = "<!-- KP:GENERATED:START -->"
GEN_END = "<!-- KP:GENERATED:END -->"
RES_START = "<!-- RESEARCHER:NOTES:START -->"
RES_END = "<!-- RESEARCHER:NOTES:END -->"


def _span(text, start, end):
    """Return (i0, i1) covering start..end inclusive, or a conflict string."""
    s_idx = [m.start() for m in re.finditer(re.escape(start), text)]
    e_idx = [m.start() for m in re.finditer(re.escape(end), text)]
    if len(s_idx) == 0 or len(e_idx) == 0:
        return f"missing marker pair ({start} / {end})"
    if len(s_idx) > 1 or len(e_idx) > 1:
        return f"duplicated marker pair ({start} / {end})"
    if e_idx[0] < s_idx[0]:
        return f"END before START ({start} / {end})"
    return (s_idx[0], e_idx[0] + len(end))


def merge_note(existing_text, new_generated_body):
    """
    Merge: new generated region + existing researcher region.
    Returns (merged_text, None) on success or (None, conflict_reason).
    """
    gen = _span(existing_text, GEN_START, GEN_END)
    res = _span(existing_text, RES_START, RES_END)
    if isinstance(gen, str):
        return None, gen
    if isinstance(res, str):
        return None, res
    # Ordering: generated must precede researcher (contract layout).
    if not (gen[1] <= res[0] or res[1] <= gen[0]):
        return None, "generated and researcher regions interleave"

    researcher_block = existing_text[res[0]:res[1]]
    new_gen_block = f"{GEN_START}\n{new_generated_body.strip()}\n{GEN_END}"
    merged = f"{new_gen_block}\n\n{researcher_block}\n"
    return merged, None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _schemas_dir(args):
    if args.schemas_dir:
        return args.schemas_dir
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "docs", "protocol", "obsidian", "schemas")


def cmd_schema(args):
    sd = _schemas_dir(args)
    schema_for = {
        "projection": _load(os.path.join(sd, "projection.schema.json")),
        "manifest": _load(os.path.join(sd, "export_manifest.schema.json")),
        "proposal": _load(os.path.join(sd, "proposal.schema.json")),
        "receipt": _load(os.path.join(sd, "decision_receipt.schema.json")),
    }
    failures = 0
    checked = 0
    pkg = args.package

    manifest_path = os.path.join(pkg, "export_manifest.json")
    if os.path.exists(manifest_path):
        checked += 1
        errs = validate(_load(manifest_path), schema_for["manifest"])
        _report("export_manifest.json", errs)
        failures += 1 if errs else 0

    for sub, key in [("records", "projection"),
                     ("proposals/inbox", "proposal"),
                     ("proposals/accepted", "proposal"),
                     ("proposals/revised", "proposal"),
                     ("proposals/rejected", "proposal"),
                     ("proposals/receipts", "receipt")]:
        d = os.path.join(pkg, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            checked += 1
            errs = validate(_load(os.path.join(d, fn)), schema_for[key])
            _report(f"{sub}/{fn}", errs)
            failures += 1 if errs else 0

    print(f"\nschema: {checked} file(s) checked, {failures} failed.")
    return 1 if failures else 0


def cmd_merge(args):
    with open(args.note, "r", encoding="utf-8") as fh:
        existing = fh.read()
    new_body = args.new_generated or "(regenerated content)"
    merged, conflict = merge_note(existing, new_body)
    if conflict:
        print(f"CONFLICT {args.note}: {conflict}")
        if args.apply_to_tmp:
            cpath = args.note + ".conflict.md"
            with open(cpath, "w", encoding="utf-8") as fh:
                fh.write(f"# MERGE CONFLICT\n\nreason: {conflict}\n\n---\n\n{existing}")
            print(f"  wrote {cpath}")
        return 1
    print(f"OK {args.note}: merge clean (researcher region preserved verbatim)")
    if args.apply_to_tmp:
        tpath = args.note + ".merged.tmp"
        with open(tpath, "w", encoding="utf-8") as fh:
            fh.write(merged)
        print(f"  wrote {tpath}")
    return 0


def cmd_all(args):
    rc = cmd_schema(args)
    pkg = args.package
    notes = []
    for root, _dirs, files in os.walk(pkg):
        for fn in files:
            if fn.endswith(".md") and not fn.endswith(".conflict.md"):
                notes.append(os.path.join(root, fn))
    mfail = 0
    for n in notes:
        with open(n, "r", encoding="utf-8") as fh:
            text = fh.read()
        if GEN_START not in text and RES_START not in text:
            continue  # plain doc, not a generated note
        merged, conflict = merge_note(text, "(dry-run regeneration)")
        if conflict:
            print(f"CONFLICT {os.path.relpath(n, pkg)}: {conflict}")
            mfail += 1
        else:
            print(f"OK merge {os.path.relpath(n, pkg)}")
    print(f"\nmerge: {len(notes)} note(s) scanned, {mfail} conflict(s).")
    return 1 if (rc or mfail) else 0


def _report(name, errs):
    if errs:
        print(f"FAIL {name}")
        for e in errs:
            print(f"     - {e}")
    else:
        print(f"OK   {name}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("schema", help="validate records/manifest/proposals against schemas")
    ps.add_argument("package", help="path to projection package directory")
    ps.add_argument("--schemas-dir", default=None)
    ps.set_defaults(func=cmd_schema)

    pm = sub.add_parser("merge", help="validate protected-region merge for a note")
    pm.add_argument("note", help="path to a generated .md note")
    pm.add_argument("--new-generated", default=None, help="replacement generated body")
    pm.add_argument("--apply-to-tmp", action="store_true",
                    help="write .merged.tmp / .conflict.md (never in place)")
    pm.set_defaults(func=cmd_merge)

    pa = sub.add_parser("all", help="schema over a package + merge dry-run over notes")
    pa.add_argument("package", help="path to projection package directory")
    pa.add_argument("--schemas-dir", default=None)
    pa.set_defaults(func=cmd_all)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
