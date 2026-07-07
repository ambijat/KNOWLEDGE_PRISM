#!/usr/bin/env python3
from pathlib import Path
import csv, json, sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'README.md',
    'PROJECT_STATUS.md',
    'ROADMAP.md',
    'docs/protocol/REVISED_PROJECT_PROTOCOL.md',
    'docs/protocol/MASTER_CORPUS_SCHEMA.md',
    'docs/domain/CORRECTED_DOMAIN_BOUNDARY.md',
    'data/raw/zotero/zotero_inventory.csv',
    'data/raw/recoll/recoll_corpus_manifest.csv',
    'data/raw/solemon/solemon_crawl.csv',
    'data/raw/claude_artifacts/bridge_concepts.csv',
    'data/processed/MASTER_CORPUS_REGISTER_PRELIMINARY.csv',
    'data/verification/BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv',
]

def count_rows(path):
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        return max(sum(1 for _ in f) - 1, 0)

missing = []
summary = {}
for rel in REQUIRED:
    p = ROOT / rel
    if not p.exists():
        missing.append(rel)
    elif p.suffix.lower() == '.csv':
        summary[rel] = {'rows': count_rows(p), 'size_bytes': p.stat().st_size}
    else:
        summary[rel] = {'size_bytes': p.stat().st_size}

out = ROOT / 'outputs/reports/validation_report.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'root': '.', 'missing': missing, 'summary': summary}, indent=2), encoding='utf-8')

if missing:
    print('VALIDATION FAILED')
    for m in missing:
        print('MISSING:', m)
    print('Report:', out)
    sys.exit(1)
print('VALIDATION PASSED')
print('Report:', out)
