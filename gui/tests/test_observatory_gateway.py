from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gui.knowledge_prism_app import KnowledgePrismApp, TAB_NAMES
from gui.services import observatory


class ObservatoryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.db = self.root / "knowledge_prism.db"
        with sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE block (block_no INTEGER PRIMARY KEY)")
            connection.executemany("INSERT INTO block VALUES (?)", [(0,), (1,), (2,)])
        self.ledger_file = self.root / "ledger" / "block.json"
        self.ledger_file.parent.mkdir()
        self.ledger_file.write_text('{"block_no": 2}\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    @staticmethod
    def _runner(returncode: int = 0, stdout: str = "schema: 1 file(s) checked, 0 failed.\n"):
        return MagicMock(return_value=subprocess.CompletedProcess([], returncode, stdout, ""))

    def _write_manifest(self, *, head: int = 0, path: str = "synthetic fixture", counts: dict | None = None) -> None:
        payload = {
            "manifest_version": "1.0",
            "generated_ts": "2026-07-16T12:00:00+00:00",
            "projection_version": "1.0",
            "source_db": {"path": path, "head_block_no": head, "chain_ok": True},
            "counts": counts or {"concept": 3, "entity": 3, "source": 2, "claim": 4},
            "records": [],
            "id_crosswalk": [],
        }
        (self.vault / observatory.MANIFEST_NAME).write_text(json.dumps(payload), encoding="utf-8")

    def test_current_vault_detected_and_synthetic_fixture_labelled(self) -> None:
        snapshot = observatory.inspect_projection(runner=self._runner())
        self.assertTrue(snapshot.manifest_available)
        self.assertEqual(observatory.SYNTHETIC_FIXTURE, snapshot.status)
        self.assertTrue(snapshot.synthetic_fixture)

    def test_missing_vault_is_not_generated(self) -> None:
        snapshot = observatory.inspect_projection(self.root / "missing", runner=self._runner())
        self.assertEqual(observatory.NOT_GENERATED, snapshot.status)

    def test_missing_manifest_is_not_generated(self) -> None:
        snapshot = observatory.inspect_projection(self.vault, runner=self._runner())
        self.assertEqual(observatory.NOT_GENERATED, snapshot.status)

    def test_malformed_manifest_is_handled_safely(self) -> None:
        (self.vault / observatory.MANIFEST_NAME).write_text("{bad", encoding="utf-8")
        snapshot = observatory.inspect_projection(self.vault, runner=self._runner())
        self.assertEqual(observatory.VALIDATION_FAILED, snapshot.status)
        self.assertIn("could not be read safely", snapshot.message)

    def test_valid_manifest_fields_and_counts_are_displayed(self) -> None:
        self._write_manifest()
        snapshot = observatory.inspect_projection(self.vault, runner=self._runner())
        rendered = observatory.display_text(snapshot)
        for expected in (
            "Projection name: Knowledge Observatory",
            "Manifest version: 1.0",
            "Generated timestamp: 2026-07-16T12:00:00+00:00",
            "Source head block number: 0",
            "Chain status: OK",
            "concept: 3",
            "Synthetic fixture designation: YES",
            "Direct Obsidian availability: OBSIDIAN_NOT_AVAILABLE",
        ):
            self.assertIn(expected, rendered)

    def test_validator_success_uses_frozen_all_interface(self) -> None:
        self._write_manifest()
        runner = self._runner()
        snapshot = observatory.inspect_projection(self.vault, runner=runner)
        self.assertTrue(snapshot.validation_ok)
        command = runner.call_args.args[0]
        self.assertEqual("python3", command[0])
        self.assertEqual("all", command[-2])
        self.assertEqual(str(self.vault), command[-1])
        self.assertFalse(runner.call_args.kwargs["shell"])

    def test_validator_failure_sets_validation_failed(self) -> None:
        self._write_manifest()
        runner = self._runner(1, "FAIL export_manifest.json\n")
        snapshot = observatory.inspect_projection(self.vault, runner=runner)
        self.assertEqual(observatory.VALIDATION_FAILED, snapshot.status)
        self.assertFalse(snapshot.validation_ok)

    def test_current_and_stale_compare_against_read_only_ledger_head(self) -> None:
        self._write_manifest(head=2, path="db/knowledge_prism.db")
        current = observatory.inspect_projection(self.vault, db_path=self.db, runner=self._runner())
        self.assertEqual(observatory.CURRENT, current.status)
        self._write_manifest(head=1, path="db/knowledge_prism.db")
        stale = observatory.inspect_projection(self.vault, db_path=self.db, runner=self._runner())
        self.assertEqual(observatory.STALE, stale.status)

    def test_folder_open_uses_vault_uri(self) -> None:
        opener = MagicMock(return_value=True)
        opened, _message = observatory.open_vault_folder(self.vault, opener=opener)
        self.assertTrue(opened)
        opener.assert_called_once_with(self.vault.as_uri())

    def test_missing_folder_prevents_opening(self) -> None:
        opener = MagicMock(return_value=True)
        opened, _message = observatory.open_vault_folder(self.root / "missing", opener=opener)
        self.assertFalse(opened)
        opener.assert_not_called()

    def test_status_checks_do_not_write_database_or_ledger(self) -> None:
        self._write_manifest(head=2, path="db/knowledge_prism.db")
        before_db = self.db.read_bytes()
        before_ledger = self.ledger_file.read_bytes()
        observatory.inspect_projection(self.vault, db_path=self.db, runner=self._runner())
        self.assertEqual(before_db, self.db.read_bytes())
        self.assertEqual(before_ledger, self.ledger_file.read_bytes())


class ObservatoryGatewayTests(unittest.TestCase):
    def test_gateway_is_a_permanent_top_level_tab(self) -> None:
        self.assertIn("Knowledge Observatory", TAB_NAMES)

    def test_controls_warnings_and_disabled_states_are_built(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.tabs = {"Knowledge Observatory": MagicMock()}
        button_calls: list[dict] = []

        def button_factory(*_args, **kwargs):
            button_calls.append(kwargs)
            return MagicMock()

        with patch("gui.knowledge_prism_app.ttk.Label") as label, patch(
            "gui.knowledge_prism_app.ttk.Frame", return_value=MagicMock()
        ), patch("gui.knowledge_prism_app.ttk.Button", side_effect=button_factory), patch(
            "gui.knowledge_prism_app.ScrolledText", return_value=MagicMock()
        ):
            app._tab_observatory()

        by_text = {call["text"]: call for call in button_calls}
        self.assertEqual("disabled", by_text["Regenerate Observatory"]["state"])
        self.assertEqual("disabled", by_text["Open in Obsidian"]["state"])
        label_texts = [call.kwargs.get("text") for call in label.call_args_list]
        self.assertIn(observatory.AUTHORITY_WARNING, label_texts)
        self.assertIn(observatory.SYNTHETIC_WARNING, label_texts)
        self.assertIn(observatory.REGENERATION_DISABLED_REASON, label_texts)
        self.assertIn(observatory.OBSIDIAN_DISABLED_REASON, label_texts)

    def test_missing_folder_action_reports_error_without_crashing(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.observatory_action_status = MagicMock()
        with patch.object(observatory, "open_vault_folder", return_value=(False, "missing")), patch(
            "gui.knowledge_prism_app.messagebox.showerror"
        ) as error:
            app.open_observatory_vault()
        error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
