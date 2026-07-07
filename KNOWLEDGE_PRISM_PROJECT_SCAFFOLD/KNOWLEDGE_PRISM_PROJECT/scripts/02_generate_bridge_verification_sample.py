#!/usr/bin/env python3
from pathlib import Path
import csv
ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / 'data/verification/BRIDGE_CONCEPTS_VERIFICATION_QUEUE.csv'
OUT = ROOT / 'outputs/reports/BRIDGE_VERIFICATION_SAMPLE_50.md'
OUT.parent.mkdir(parents=True, exist_ok=True)
rows=[]
with open(INP, newline='', encoding='utf-8', errors='replace') as f:
    for i,r in enumerate(csv.DictReader(f)):
        if i>=50: break
        rows.append(r)
lines = ['# Bridge Concepts Verification Sample 50', '', 'Each item below is provisional. Mark the evidence actually seen before using it in scholarly argument.', '']
for i,r in enumerate(rows,1):
    title = r.get('title') or r.get('title_candidate') or r.get('file') or f'Item {i}'
    lines += [
        f'## {i}. {title}', '',
        f'- Folder: `{r.get("folder", "")}`',
        f'- File: `{r.get("file", r.get("filename", ""))}`',
        f'- Provisional axis: `{r.get("axis", "")}`',
        f'- Provisional thesis: {r.get("thesis", "")}',
        f'- Provisional concepts: {r.get("concepts", "")}', '',
        '**Verification checklist**', '',
        '- [ ] File located',
        '- [ ] Text extraction works',
        '- [ ] Front matter / abstract / TOC checked',
        '- [ ] At least one chapter or relevant section sampled',
        '- [ ] Thesis supported by text',
        '- [ ] Concepts supported by text',
        '- [ ] Evidence grade assigned',
        '- [ ] Keep / revise / reject decision recorded', '',
    ]
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('Wrote', OUT)
