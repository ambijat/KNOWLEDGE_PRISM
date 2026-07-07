#!/usr/bin/env python3
from pathlib import Path
import csv, json
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data/processed/MASTER_CORPUS_REGISTER_PRELIMINARY.csv'
REPORT = ROOT / 'outputs/reports/PROJECT_STATUS_REPORT.md'
SUMMARY_JSON = ROOT / 'outputs/reports/project_status_counts.json'

def read_counts(path):
    counts = Counter(); evidence = Counter(); dup = 0; rows = 0
    if not path.exists(): return rows, counts, evidence, dup
    with open(path, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            rows += 1
            counts[r.get('corpus_class_preliminary','Unknown')] += 1
            evidence[r.get('evidence_grade','unknown')] += 1
            if str(r.get('is_duplicate_candidate','')).lower() == 'true': dup += 1
    return rows, counts, evidence, dup
rows, counts, evidence, dup = read_counts(MASTER)
lines = ['# KNOWLEDGE PRISM STATUS REPORT', '', f'- Master register rows: **{rows}**', f'- Duplicate-candidate rows: **{dup}**', '', '## Preliminary corpus classes', '']
for k,v in counts.most_common(): lines.append(f'- {k}: {v}')
lines += ['', '## Evidence grades', '']
for k,v in evidence.most_common(): lines.append(f'- {k}: {v}')
lines += ['', '## Warning', '', 'These are preliminary metadata-level counts. They are not a final scholarly ontology.']
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text('\n'.join(lines), encoding='utf-8')
SUMMARY_JSON.write_text(json.dumps({'rows': rows, 'duplicates': dup, 'classes': counts, 'evidence': evidence}, indent=2), encoding='utf-8')
print('Wrote', REPORT)
print('Wrote', SUMMARY_JSON)
