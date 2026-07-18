"""Read-only status gateway for the generated Knowledge Observatory vault."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
PROJECTION_NAME = "Knowledge Observatory"
VAULT_DIR = ROOT / "outputs" / "obsidian" / "vertical_slice_vault"
MANIFEST_NAME = "export_manifest.json"
VALIDATOR = ROOT / "scripts" / "08_validate_obsidian_projection.py"
DB_PATH = ROOT / "db" / "knowledge_prism.db"

SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
CURRENT = "CURRENT"
STALE = "STALE"
NOT_GENERATED = "NOT_GENERATED"
VALIDATION_FAILED = "VALIDATION_FAILED"
OBSIDIAN_NOT_AVAILABLE = "OBSIDIAN_NOT_AVAILABLE"
STATUS_VOCABULARY = (
    SYNTHETIC_FIXTURE,
    CURRENT,
    STALE,
    NOT_GENERATED,
    VALIDATION_FAILED,
    OBSIDIAN_NOT_AVAILABLE,
)

AUTHORITY_WARNING = (
    "This Observatory is a generated projection. It does not constitute the authoritative database, "
    "evidence register, ontology, research state, or ledger. Editing generated notes does not modify "
    "governed KNOWLEDGE_PRISM state."
)
SYNTHETIC_WARNING = "Current projection is a synthetic vertical-slice fixture, not a live database projection."
REGENERATION_DISABLED_REASON = "Regeneration is not enabled in this bounded cycle."
OBSIDIAN_DISABLED_REASON = "Direct Obsidian launch is not yet configured. Use Open Vault Folder."


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str


@dataclass(frozen=True)
class ObservatorySnapshot:
    projection_name: str = PROJECTION_NAME
    vault_dir: Path = VAULT_DIR
    status: str = NOT_GENERATED
    manifest_available: bool = False
    manifest_version: str | None = None
    generated_ts: str | None = None
    source_head_block_no: int | None = None
    live_head_block_no: int | None = None
    chain_ok: bool | None = None
    counts: Mapping[str, int] = field(default_factory=dict)
    synthetic_fixture: bool = False
    validation_ok: bool | None = None
    obsidian_status: str = OBSIDIAN_NOT_AVAILABLE
    message: str = ""


def live_ledger_head(db_path: Path = DB_PATH) -> int | None:
    """Read the ledger head through a SQLite read-only connection."""
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        row = connection.execute("SELECT MAX(block_no) FROM block").fetchone()
    return None if row is None or row[0] is None else int(row[0])


def run_validator(
    vault_dir: Path = VAULT_DIR,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> ValidationResult:
    """Run the frozen validator without modifying the projection package."""
    command: Sequence[str] = (
        "python3",
        str(VALIDATOR),
        "all",
        str(vault_dir),
    )
    try:
        result = runner(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except OSError as exc:
        return ValidationResult(False, f"Validator could not run: {exc}")
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
    if result.returncode == 0:
        return ValidationResult(True, _concise_output(output, "Projection validation passed."))
    return ValidationResult(False, _concise_output(output, f"Validator exited with code {result.returncode}."))


def inspect_projection(
    vault_dir: Path = VAULT_DIR,
    *,
    db_path: Path = DB_PATH,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    head_reader: Callable[[Path], int | None] = live_ledger_head,
) -> ObservatorySnapshot:
    """Inspect manifest, validation, and ledger-head state without writing anywhere."""
    manifest_path = vault_dir / MANIFEST_NAME
    if not vault_dir.is_dir():
        return ObservatorySnapshot(vault_dir=vault_dir, message="Vault folder has not been generated.")
    if not manifest_path.is_file():
        return ObservatorySnapshot(vault_dir=vault_dir, message="export_manifest.json is not available.")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest root must be a JSON object")
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return ObservatorySnapshot(
            vault_dir=vault_dir,
            status=VALIDATION_FAILED,
            manifest_available=True,
            validation_ok=False,
            message=f"Manifest could not be read safely: {exc}",
        )

    source = manifest.get("source_db") if isinstance(manifest.get("source_db"), dict) else {}
    raw_head = source.get("head_block_no")
    source_head = raw_head if isinstance(raw_head, int) and not isinstance(raw_head, bool) else None
    raw_chain = source.get("chain_ok")
    chain_ok = raw_chain if isinstance(raw_chain, bool) else None
    raw_counts = manifest.get("counts")
    counts = {
        str(key): int(value)
        for key, value in (raw_counts.items() if isinstance(raw_counts, dict) else [])
        if isinstance(value, int) and not isinstance(value, bool)
    }
    synthetic = "synthetic fixture" in str(source.get("path", "")).lower() or source_head == 0
    validation = run_validator(vault_dir, runner=runner)
    common = dict(
        vault_dir=vault_dir,
        manifest_available=True,
        manifest_version=_optional_text(manifest.get("manifest_version")),
        generated_ts=_optional_text(manifest.get("generated_ts")),
        source_head_block_no=source_head,
        chain_ok=chain_ok,
        counts=counts,
        synthetic_fixture=synthetic,
        validation_ok=validation.ok,
    )
    if not validation.ok:
        return ObservatorySnapshot(status=VALIDATION_FAILED, message=validation.message, **common)
    if synthetic:
        return ObservatorySnapshot(status=SYNTHETIC_FIXTURE, message=validation.message, **common)

    try:
        live_head = head_reader(db_path)
    except (OSError, sqlite3.Error, ValueError) as exc:
        return ObservatorySnapshot(
            status=VALIDATION_FAILED,
            message=f"Live ledger head could not be read safely: {exc}",
            **common,
        )
    if source_head == live_head:
        status = CURRENT
        message = validation.message
    elif source_head is not None and live_head is not None and source_head < live_head:
        status = STALE
        message = f"Projection head {source_head} is behind live ledger head {live_head}."
    else:
        status = VALIDATION_FAILED
        message = "Manifest source head cannot be reconciled with the live ledger head."
    return ObservatorySnapshot(status=status, live_head_block_no=live_head, message=message, **common)


def open_vault_folder(
    vault_dir: Path = VAULT_DIR,
    *,
    opener: Callable[[str], bool] | None = None,
) -> tuple[bool, str]:
    """Open an existing vault folder; never create a missing directory."""
    if not vault_dir.is_dir():
        return False, "Vault folder is missing; nothing was opened or created."
    uri = vault_dir.as_uri()
    opened = bool(opener(uri) if opener is not None else webbrowser.open(vault_dir.as_uri()))
    if opened:
        return True, f"Opened vault folder: {uri}"
    return False, f"The system did not open the vault folder: {uri}"


def display_text(snapshot: ObservatorySnapshot) -> str:
    """Format all required gateway fields for the GUI."""
    try:
        vault_path = snapshot.vault_dir.relative_to(ROOT).as_posix()
    except ValueError:
        vault_path = str(snapshot.vault_dir)
    chain = "OK" if snapshot.chain_ok is True else "BROKEN" if snapshot.chain_ok is False else "Unavailable"
    counts = ", ".join(f"{key}: {value}" for key, value in sorted(snapshot.counts.items())) or "Unavailable"
    return "\n".join(
        [
            f"Projection name: {snapshot.projection_name}",
            f"Current vault path: {vault_path}",
            f"Projection status: {snapshot.status}",
            f"Manifest availability: {'Available' if snapshot.manifest_available else 'Not available'}",
            f"Manifest version: {snapshot.manifest_version or 'Unavailable'}",
            f"Generated timestamp: {snapshot.generated_ts or 'Unavailable'}",
            f"Source head block number: {_shown(snapshot.source_head_block_no)}",
            f"Live ledger head block number: {_shown(snapshot.live_head_block_no)}",
            f"Chain status: {chain}",
            f"Available entity/count information: {counts}",
            f"Synthetic fixture designation: {'YES' if snapshot.synthetic_fixture else 'NO'}",
            f"Direct Obsidian availability: {snapshot.obsidian_status}",
            "",
            f"Status detail: {snapshot.message or 'No additional detail.'}",
        ]
    )


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _shown(value: object) -> str:
    return "Unavailable" if value is None else str(value)


def _concise_output(output: str, fallback: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return fallback
    significant = [line for line in lines if line.startswith(("FAIL", "CONFLICT", "schema:", "merge:"))]
    chosen = significant[-2:] if significant else lines[-2:]
    return " ".join(chosen)[:500]
