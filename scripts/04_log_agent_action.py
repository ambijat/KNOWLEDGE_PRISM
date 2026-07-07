#!/usr/bin/env python3
"""Append and verify hash-linked agent action records.

This is the granular transparency layer for Knowledge Prism. It complements the
milestone-level provenance blocks in db/prism_ledger.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "logs/agent_actions.jsonl"
GENESIS_HASH = "0" * 64


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_record(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "record_hash"}
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def read_records() -> list[dict[str, Any]]:
    if not LOG.exists():
        return []
    records = []
    with LOG.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"invalid JSON at {LOG}:{line_no}: {exc}") from exc
    return records


def last_hash(records: list[dict[str, Any]]) -> str:
    return records[-1].get("record_hash", GENESIS_HASH) if records else GENESIS_HASH


def parse_csv(values: list[str] | None) -> list[str]:
    return [value for value in (values or []) if value]


def log_action(args: argparse.Namespace) -> None:
    records = read_records()
    record = {
        "ts": now(),
        "actor": args.actor,
        "task_id": args.task_id,
        "action_type": args.action_type,
        "intent": args.intent,
        "scope": parse_csv(args.scope),
        "inputs": parse_csv(args.input),
        "outputs": parse_csv(args.output),
        "commands": parse_csv(args.command),
        "evidence_grade": args.evidence_grade,
        "hidden_io": args.hidden_io,
        "notes": args.notes or "",
        "prev_record_hash": last_hash(records),
    }
    record["record_hash"] = hash_record(record)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(canonical(record) + "\n")
    print(f"logged {record['task_id']} {record['action_type']}")
    print(f"record_hash={record['record_hash']}")


def verify(_: argparse.Namespace) -> None:
    records = read_records()
    expected_prev = GENESIS_HASH
    problems: list[str] = []
    for index, record in enumerate(records, start=1):
        if record.get("prev_record_hash") != expected_prev:
            problems.append(f"record {index}: broken prev hash")
        recomputed = hash_record(record)
        if record.get("record_hash") != recomputed:
            problems.append(f"record {index}: record hash mismatch")
        expected_prev = record.get("record_hash", "")
    if problems:
        print("ACTION LOG: BROKEN")
        for problem in problems:
            print("!", problem)
        raise SystemExit(1)
    print(f"ACTION LOG: OK ({len(records)} records)")


def report(_: argparse.Namespace) -> None:
    records = read_records()
    print(f"log: {LOG}")
    print(f"records: {len(records)}")
    if records:
        print(f"first: {records[0]['ts']} {records[0]['task_id']}")
        print(f"latest: {records[-1]['ts']} {records[-1]['task_id']}")
        print(f"latest_hash: {records[-1]['record_hash']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hash-linked Knowledge Prism agent action log.")
    sub = parser.add_subparsers(required=True)

    log = sub.add_parser("log", help="append an action record")
    log.add_argument("--actor", default="codex")
    log.add_argument("--task-id", required=True)
    log.add_argument("--action-type", required=True, choices=[
        "inspect", "edit", "generate", "verify", "seal", "decide", "promote", "reject"
    ])
    log.add_argument("--intent", required=True)
    log.add_argument("--scope", action="append", default=[])
    log.add_argument("--input", action="append", default=[])
    log.add_argument("--output", action="append", default=[])
    log.add_argument("--command", action="append", default=[])
    log.add_argument("--evidence-grade", required=True, choices=[
        "infrastructure",
        "metadata_only",
        "metadata_manifest",
        "hypothesis_only",
        "frontmatter_seen",
        "sampled_text",
        "analysis",
        "concept_verified",
    ])
    log.add_argument("--hidden-io", choices=["false", "true"], default="false")
    log.add_argument("--notes", default="")
    log.set_defaults(func=log_action)

    verify_cmd = sub.add_parser("verify", help="verify action-log hash chain")
    verify_cmd.set_defaults(func=verify)

    report_cmd = sub.add_parser("report", help="print action-log summary")
    report_cmd.set_defaults(func=report)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
