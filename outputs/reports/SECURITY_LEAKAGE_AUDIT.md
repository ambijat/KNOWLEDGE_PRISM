# Security Leakage Audit

Date: 2026-07-07

## Scope

This audit checked the Knowledge Prism workspace for likely leakage points:

- local credential files,
- hidden network or browser IO,
- unsafe preview serving,
- packaged artifacts,
- file permissions,
- project ignore rules,
- provenance and action-log integrity.

Secret values were not intentionally copied into this report.

## Executive Summary

The project is structurally transparent, but it had three practical leakage
risks:

1. Local credential and runtime-dump files existed under `secrets/`.
2. Those files were group-readable before this audit.
3. A previous GUI preview server served the project root, which could expose
   local-only files if reachable on the network.

Immediate plugs were applied:

- stopped the broad project-root preview server,
- changed `secrets/` permissions to owner-only,
- added `.gitignore` rules for secrets and credential-like files,
- added `scripts/06_serve_gui.py`, which serves only `/` and `/index.html`,
- verified the GUI has no `fetch`, `XMLHttpRequest`, `WebSocket`, or
  `sendBeacon` calls,
- verified the granular action log and milestone ledger.

## Findings

### Finding 1: Local Credential Files Present

Status: **plugged locally, rotate recommended**

The workspace contains local credential-like files under:

```text
secrets/deepseek_apikey.txt
secrets/open_alex_api_key.txt
```

The values are not reproduced here.

Risk:

- accidental serving,
- accidental commit if a git repo is initialised later,
- accidental inclusion in zip exports,
- accidental disclosure to future tools or agents.

Action taken:

- `secrets/` is now ignored by `.gitignore`,
- files under `secrets/` are now owner-readable only.

Recommended:

- rotate these keys if there is any chance they were served, copied, or exposed,
- keep future credentials outside the project tree when possible,
- use environment variables or a local ignored config file instead.

### Finding 2: Runtime Dump Files In Secrets Folder

Status: **plugged locally, still sensitive**

The `secrets/` folder also contains runtime dump material:

```text
secrets/behindthescene.txt
secrets/claudescinec domain.txt
secrets/cs_dump.txt
```

Risk:

- local paths,
- daemon/log details,
- temporary login or nonce material,
- tool output traces,
- model/runtime metadata.

Action taken:

- permissions tightened to owner-only,
- `secrets/` added to `.gitignore`.

Recommended:

- keep these files local-only,
- do not serve them,
- do not include them in future artifacts,
- redact or delete them after extracting any needed non-sensitive lesson.

### Finding 3: Unsafe Project-Root Preview Server

Status: **plugged**

A previous local preview command served the project root:

```text
python3 -m http.server 8787
```

Risk:

- every file under the project root could be requested by URL,
- this includes local secrets, database files, logs, and raw corpus metadata.

Action taken:

- stopped the server,
- confirmed no listener remains on the prior preview port,
- added a safe preview server:

```bash
python3 scripts/06_serve_gui.py
```

This server binds to `127.0.0.1` by default and serves only:

```text
/
/index.html
```

Recommended:

- do not use `python3 -m http.server` from this project root,
- use `scripts/06_serve_gui.py` for GUI preview,
- if public hosting is needed, build a separate publish folder containing only
  intended public assets.

### Finding 4: GUI External IO

Status: **clean**

The `index.html` GUI was checked for obvious outbound browser mechanisms:

- `fetch`
- `XMLHttpRequest`
- `WebSocket`
- `navigator.sendBeacon`

No such calls were found.

Current browser-side persistence:

- `localStorage`,
- clipboard copy on explicit user button click,
- JSON download on explicit user button click.

Risk:

- low, assuming the file is served through the safe GUI server.

Recommended:

- keep future network features opt-in and visibly labelled,
- log any external API integration in the action log,
- never embed API keys in `index.html`.

### Finding 5: Packaged Zip Artifacts

Status: **no flagged secret filenames found**

Zip files under `assets/` were inspected by filename for credential-like names.
No entries with names containing key, secret, token, password, or `.env` were
found.

Risk:

- filename scan cannot prove there are no secrets inside arbitrary text files,
  but no obvious secret-bearing filenames were present.

Recommended:

- do not publish inherited zips without a deeper content scan,
- prefer regenerating clean publish artifacts.

### Finding 6: Absolute Local Paths In Corpus Registers

Status: **accepted local metadata risk**

The corpus registers previously contained absolute local source paths.

Risk:

- reveals local machine/user/storage structure if published,
- can expose names of private folders or historical file organisation.

Recommended:

- keep raw registers local unless intentionally sharing,
- create redacted public registers before publication,
- replace absolute roots with symbolic roots such as `${SOLEMON_ROOT}` in public
  exports.

### Finding 7: Provenance Logs

Status: **healthy**

The new granular action log verifies:

```bash
python3 scripts/04_log_agent_action.py verify
```

The project milestone ledger verifies:

```bash
python3 db/prism.py verify
```

Risk:

- action logs can themselves leak sensitive paths or command text if agents log
  too much.

Recommended:

- keep action-log entries factual but compact,
- do not log credential values,
- log secret usage as `hidden_io=true` with explanation, not by copying the
  secret.

## Plugs Applied During This Audit

1. Stopped the broad root preview server.
2. Changed `secrets/` directory permissions to owner-only.
3. Changed files under `secrets/` to owner-read/write only.
4. Added secret and credential patterns to `.gitignore`.
5. Added `scripts/06_serve_gui.py` for safe GUI-only preview.
6. Verified no obvious outbound browser IO in `index.html`.
7. Verified action-log and ledger integrity.

## Operating Rules Going Forward

1. Never serve the project root.
2. Never embed API keys in HTML, JavaScript, Markdown, CSV, or reports.
3. Treat `secrets/` as local-only and ignored.
4. Use `scripts/06_serve_gui.py` for local GUI previews.
5. Log any external API call or hidden input in `logs/agent_actions.jsonl`.
6. Before publishing, create a clean `public/` or `release/` folder.
7. Redact absolute paths in any public data export.
8. Rotate credentials after any suspected exposure.
9. Keep ontology claims separate from external operational/security claims.
10. Verify both chains after non-trivial work:

```bash
python3 scripts/04_log_agent_action.py verify
python3 db/prism.py verify
```

## Current Risk Rating

After the plugs applied in this audit:

- GUI leakage risk: **low**
- credential-at-rest risk: **medium, because local secrets still exist**
- accidental-publication risk: **medium**
- ontology contamination risk: **low**
- provenance integrity risk: **low**

The highest remaining recommendation is to rotate the local API keys if they may
have been exposed, and to publish only from a clean public export folder.
