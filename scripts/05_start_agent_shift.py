#!/usr/bin/env python3
"""Required start ritual for every Knowledge Prism agent shift.

Run this before doing project work. It restores project state, verifies both
provenance chains, and logs the task intent in the hash-linked action log.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start a Knowledge Prism agent shift transparently.")
    parser.add_argument("--task-id", required=True, help="Short stable id for this shift/task.")
    parser.add_argument("--intent", required=True, help="Why this shift is being started.")
    parser.add_argument("--actor", default="codex", help="Agent or human actor label.")
    parser.add_argument("--scope", action="append", default=[], help="Expected files/areas of work. Repeatable.")
    parser.add_argument("--input", action="append", default=[], help="Expected input files/sources. Repeatable.")
    parser.add_argument("--hidden-io", choices=["false", "true"], default="false")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run(["python3", "db/prism.py", "boot"])
    run(["python3", "scripts/04_log_agent_action.py", "verify"])
    run(["python3", "db/prism.py", "verify"])

    log_cmd = [
        "python3",
        "scripts/04_log_agent_action.py",
        "log",
        "--actor",
        args.actor,
        "--task-id",
        args.task_id,
        "--action-type",
        "inspect",
        "--intent",
        args.intent,
        "--evidence-grade",
        "infrastructure",
        "--hidden-io",
        args.hidden_io,
        "--command",
        "python3 db/prism.py boot",
        "--command",
        "python3 scripts/04_log_agent_action.py verify",
        "--command",
        "python3 db/prism.py verify",
    ]
    for value in args.scope:
        log_cmd.extend(["--scope", value])
    for value in args.input:
        log_cmd.extend(["--input", value])
    if args.notes:
        log_cmd.extend(["--notes", args.notes])

    run(log_cmd)
    run(["python3", "scripts/04_log_agent_action.py", "verify"])
    print("\nAgent shift start ritual complete. Proceed only within the logged intent and scope.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"\nStart ritual failed at: {' '.join(exc.cmd)}", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc
