#!/usr/bin/env python3
"""Regenerate a preliminary master corpus register from raw SOLEMON and Recoll CSVs.

This script intentionally uses conservative metadata-level rules only. It does not claim full-text reading.
"""
from pathlib import Path
import csv, hashlib, re
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
SOLEMON = ROOT / 'data/raw/solemon/solemon_crawl.csv'
RECOLL = ROOT / 'data/raw/recoll/recoll_corpus_manifest.csv'
OUT = ROOT / 'data/processed/MASTER_CORPUS_REGISTER_REGENERATED.csv'

CORE_TERMS = re.compile(r'afghan|afghanistan|taliban|central asia|eurasia|geopolit|international relations|\bir\b|security|regional|china|russia|india|pakistan|bri|cpec|silk|systems theory|semiotic|network|ontology|grounded theory|constructiv|realism', re.I)
NOISE_TERMS = re.compile(r'bijli|paani|electric|bill|receipt|invoice|aadhaar|kyc|passport|bank|personal|photo|scan', re.I)

def norm_path(s): return (s or '').strip()
def filename(path): return Path(path).name if path else ''
def title_from_filename(fn): return re.sub(r'[_\-]+', ' ', Path(fn).stem).strip()
def item_id(path): return 'DOC_' + hashlib.sha1(path.encode('utf-8', errors='ignore')).hexdigest()[:12]
def dedupe_key(fn, size): return f"{fn.lower()}|{size or ''}"
def topdir_folder(path):
    parts = Path(path).parts
    top = ''
    folder = ''
    if 'SOLEMON' in parts:
        i = parts.index('SOLEMON')
        if len(parts) > i+1: top = parts[i+1]
        if len(parts) > i+2: folder = parts[i+2]
    return top, folder

def classify(text):
    if NOISE_TERMS.search(text): return 'Noise'
    if CORE_TERMS.search(text): return 'Core'
    return 'Unknown'

records = {}
if SOLEMON.exists():
    with open(SOLEMON, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            path = norm_path(r.get('path'))
            if not path: continue
            fn = filename(path)
            size = r.get('size') or ''
            top, folder = topdir_folder(path)
            records[path] = {
                'corpus_item_id': item_id(path),
                'title_candidate': title_from_filename(fn),
                'author_candidate': '',
                'filename': fn,
                'path_norm': path,
                'ext': (r.get('ext') or Path(fn).suffix).lower(),
                'mime_or_ext': (r.get('ext') or Path(fn).suffix).lower(),
                'size_bytes': size,
                'size_mb': round(int(size)/1024/1024, 2) if str(size).isdigit() else '',
                'topdir': top,
                'folder': folder or top,
                'source_solemon_crawl': 'True',
                'source_recoll_manifest': 'False',
            }
if RECOLL.exists():
    with open(RECOLL, newline='', encoding='utf-8', errors='replace') as f:
        for r in csv.DictReader(f):
            path = norm_path(r.get('path'))
            if not path: continue
            fn = filename(path)
            size_mb = r.get('size_mb') or ''
            size_bytes = ''
            try: size_bytes = str(int(float(size_mb)*1024*1024))
            except Exception: pass
            top, folder = topdir_folder(path)
            if path not in records:
                records[path] = {
                    'corpus_item_id': item_id(path),
                    'title_candidate': r.get('title') or title_from_filename(fn),
                    'author_candidate': r.get('author') or '',
                    'filename': fn,
                    'path_norm': path,
                    'ext': Path(fn).suffix.lower(),
                    'mime_or_ext': r.get('mtype') or Path(fn).suffix.lower(),
                    'size_bytes': size_bytes,
                    'size_mb': size_mb,
                    'topdir': r.get('topdir') or top,
                    'folder': r.get('folder') or folder or top,
                    'source_solemon_crawl': 'False',
                    'source_recoll_manifest': 'True',
                }
            else:
                records[path]['source_recoll_manifest'] = 'True'
                if r.get('title') and not records[path].get('title_candidate'):
                    records[path]['title_candidate'] = r.get('title')
                if r.get('author') and not records[path].get('author_candidate'):
                    records[path]['author_candidate'] = r.get('author')

# duplicate groups
for rec in records.values():
    rec['dedupe_key'] = dedupe_key(rec.get('filename',''), rec.get('size_bytes',''))
groups = defaultdict(list)
for rec in records.values(): groups[rec['dedupe_key']].append(rec)
for rec in records.values():
    gsize = len(groups[rec['dedupe_key']])
    text = ' '.join([rec.get('title_candidate',''), rec.get('filename',''), rec.get('folder',''), rec.get('topdir','')])
    rec['duplicate_group_size'] = gsize
    rec['is_duplicate_candidate'] = str(gsize > 1)
    rec['corpus_class_preliminary'] = classify(text)
    rec['evidence_grade'] = 'metadata_only'
    rec['verification_status'] = 'unverified'
    rec['claim_use_allowed'] = 'inventory_only_until_verified'
    rec['notes'] = 'Regenerated by scripts/01_build_master_register.py from raw inherited artifacts.'

fields = ['corpus_item_id','title_candidate','author_candidate','filename','path_norm','ext','mime_or_ext','size_bytes','size_mb','topdir','folder','source_solemon_crawl','source_recoll_manifest','dedupe_key','duplicate_group_size','is_duplicate_candidate','corpus_class_preliminary','evidence_grade','verification_status','claim_use_allowed','notes']
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(records.values())
print(f'Wrote {len(records)} rows to {OUT}')
