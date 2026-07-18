# Scholar Capture browser acceptance harness

This self-contained browser UI exercises the frozen Android Scholar Capture exchange contract and acknowledgement contract v0.1.1 without calling a backend or touching the Knowledge Prism database. Drafts and acknowledgement presentation state persist only in browser `localStorage`; export and acknowledgement import happen only after explicit user actions.

## Launch locally

From the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory browser-harness
```

Open `http://127.0.0.1:8765`. This serves only the harness directory on localhost. Do not open `index.html` as a `file://` URL because browser module loading is restricted there.

The exported JSON is plaintext and can contain sensitive notes. Delete it after successful desktop import. Browser drafts can be removed individually or erased with **Reset browser data**.

## Acceptance tests

Prerequisites: Node.js 18+, npm, Python 3, and Google Chrome at `/usr/bin/google-chrome`.

```bash
cd browser-harness
npm install
npm test
```

The suite checks the exact fixed fields and 16-organ vocabulary, canonical SHA-256 parity, capture/export compatibility, all six canonical v0.1.1 acknowledgement fixtures, malformed and unsupported-file refusal, matching, conflicts, replacement confirmation and history, unmatched records, content preservation, refresh persistence, responsive layout, and browser-data reset.

## Disposable desktop-import dry run

From the repository root, copy the live database to a temporary directory and run the unchanged importer against an exported file:

```bash
tmpdir="$(mktemp -d)"
cp db/knowledge_prism.db "$tmpdir/knowledge_prism.db"
python3 scripts/06_import_scholar_input.py \
  --input /path/to/kp_scholar_export_....json \
  --dry-run \
  --db "$tmpdir/knowledge_prism.db"
```

Remove that explicitly created temporary directory when finished. Never use `--commit` against the live database for harness acceptance.

## Contract boundary

The harness exports `schema_version=0.2`, `record_type=scholar_input_not_evidence`, `source=android_app`, and `status=raw_captured`. It can read a desktop-generated acknowledgement v0.1.1 and store its result, backend ID, hash, message, error code, batch metadata, and replacement history as browser-local presentation state. It never assigns backend IDs, changes captured content from an acknowledgement, offers approval controls, performs network sync, or touches evidence, research-state, ontology, or ledger operations.
