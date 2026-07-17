#!/usr/bin/env python3
"""Synchronize the public front-end navigation across public HTML pages."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "index.html": "#sample-brief",
    "interface.html": "index.html#sample-brief",
    "interaction.html": "index.html#sample-brief",
    "dashboard.html": "#exportTitle",
    "case-study-ir.html": "index.html#sample-brief",
    "method.html": "index.html#sample-brief",
}


def nav(export_href: str) -> str:
    return f"""    <nav class="nav" aria-label="Primary">
      <a class="brand" href="index.html"><span class="mark" aria-hidden="true"></span><span>Knowledge Prism</span></a>
      <div class="nav-links">
        <a href="index.html">Home</a>
        <a href="interface.html">Research Console</a>
        <a href="interaction.html">Human Workbench</a>
        <a href="dashboard.html">Expert Dashboard</a>
        <a href="case-study-ir.html">IR Pilot Case Study</a>
        <a href="method.html">Method</a>
        <a href="{export_href}">Export / Sample Brief</a>
      </div>
    </nav>"""


def sync_page(path: Path, export_href: str) -> bool:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"    <nav class=\"nav\" aria-label=\"Primary\">.*?    </nav>",
        nav(export_href),
        text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise SystemExit(f"expected exactly one primary nav in {path}")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed = []
    for page, export_href in PAGES.items():
        path = ROOT / page
        if sync_page(path, export_href):
            changed.append(page)
    if changed:
        print("updated navigation:", ", ".join(changed))
    else:
        print("navigation already synchronized")


if __name__ == "__main__":
    main()
