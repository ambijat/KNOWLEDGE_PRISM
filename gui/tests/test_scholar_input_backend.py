from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gui.knowledge_prism_app import KnowledgePrismApp
from gui.services import scholar_input_backend as backend
from gui.services import scholar_input_schema as schema


class ScholarInputBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db = self.root / "test.db"
        shutil.copy2(backend.db_access.DB_PATH, self.db)
        with sqlite3.connect(self.db) as con:
            con.execute("DELETE FROM scholar_input")
            con.commit()
        self.valid_path = self.root / "valid.json"
        self.valid_record = {
            "schema_version": "0.2", "record_type": "scholar_input_not_evidence",
            "source": "desktop_import", "captured_ts": "2026-07-10T10:00:00+05:30",
            "idea": "A disposable scholar-input fixture.", "raw_notes": "test only",
            "voice_transcript": "", "draft_organ": "Unassigned", "status": "raw_captured",
        }
        self.valid_record["content_sha256"] = schema.compute_content_sha256(self.valid_record)
        self.valid_path.write_text(json.dumps(self.valid_record), encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_empty_persistent_view_and_taxonomy(self) -> None:
        self.assertEqual(backend.persistent_rows(self.db), [])
        self.assertEqual(
            set(backend.taxonomy_statuses(self.db)),
            {"raw_captured", "imported_not_evidence", "under_review", "approved_to_question", "rejected_archived"},
        )

    def test_local_valid_and_invalid_fixtures(self) -> None:
        self.assertTrue(schema.is_valid(schema.validate_record(self.valid_record)))
        invalid = dict(self.valid_record, idea="")
        self.assertFalse(schema.is_valid(schema.validate_record(invalid)))

    def test_dry_run_commit_duplicate_refresh_and_table_isolation(self) -> None:
        before = self._table_counts()
        dry = backend.run_importer(self.valid_path, self.db)
        self.assertTrue(dry.can_commit)
        self.assertEqual(self._scholar_count(), 0)
        committed = backend.run_importer(self.valid_path, self.db, commit=True)
        self.assertEqual(committed.exit_code, 0)
        self.assertEqual(committed.transaction_outcome, "COMMITTED")
        self.assertEqual(len(backend.persistent_rows(self.db)), 1)
        duplicate = backend.run_importer(self.valid_path, self.db)
        self.assertEqual(duplicate.counts["records duplicate"], 1)
        self.assertIn("duplicate_skipped", backend.readable_report(duplicate))
        after = self._table_counts()
        for table, count in before.items():
            if table != "scholar_input":
                self.assertEqual(after[table], count, table)

    def test_invalid_backend_report_and_commit_gate(self) -> None:
        invalid_path = self.root / "invalid.json"
        invalid_path.write_text("{}", encoding="utf-8")
        report = backend.run_importer(invalid_path, self.db)
        self.assertFalse(report.can_commit)
        self.assertGreater(report.counts["records invalid"], 0)
        self.assertIn("validation errors", backend.readable_report(report))

    def test_subprocess_is_argument_array_without_shell(self) -> None:
        report = backend.run_importer(self.valid_path, self.db)
        self.assertIsInstance(report.command, tuple)
        self.assertIn("--input", report.command)
        self.assertIn("--db", report.command)

    def test_filtering_persistent_rows(self) -> None:
        backend.run_importer(self.valid_path, self.db, commit=True)
        rows = backend.persistent_rows(self.db)
        self.assertEqual(len(backend.filter_persistent_rows(rows, status="imported_not_evidence")), 1)
        self.assertEqual(len(backend.filter_persistent_rows(rows, source="android_app")), 0)
        self.assertEqual(len(backend.filter_persistent_rows(rows, search="disposable")), 1)

    def test_consistency_validator_after_disposable_commit(self) -> None:
        backend.run_importer(self.valid_path, self.db, commit=True)
        isolated = self.root / "isolated_project"
        (isolated / "scripts").mkdir(parents=True)
        (isolated / "db").mkdir()
        shutil.copy2(backend.CONSISTENCY_VALIDATOR, isolated / "scripts")
        shutil.copy2(backend.db_access.ROOT / "db" / "prism_ledger.py", isolated / "db")
        shutil.copy2(self.db, isolated / "db" / "knowledge_prism.db")
        result = subprocess.run(
            [sys.executable, str(isolated / "scripts" / backend.CONSISTENCY_VALIDATOR.name)],
            cwd=isolated, text=True, capture_output=True, shell=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_commit_is_gated_before_dry_run(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.scholar_selected_import_path = self.valid_path
        app.scholar_dry_run_report = None
        app.scholar_commit_button = SimpleNamespace(config=MagicMock())
        with patch("gui.knowledge_prism_app.messagebox.showinfo") as notice, patch.object(
            backend, "run_importer"
        ) as run:
            app.commit_scholar_import()
        notice.assert_called_once()
        run.assert_not_called()

    def test_user_cancellation_performs_no_commit(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.scholar_selected_import_path = self.valid_path
        app.scholar_dry_run_report = backend.ImportReport(
            command=(), exit_code=0, stdout="", stderr="",
            counts={"records eligible": 1, "records invalid": 0},
        )
        app.scholar_commit_button = SimpleNamespace(config=MagicMock())
        app.scholar_input_status = SimpleNamespace(config=MagicMock())
        with patch("gui.knowledge_prism_app.messagebox.askyesno", return_value=False), patch.object(
            backend, "run_importer"
        ) as run:
            app.commit_scholar_import()
        run.assert_not_called()

    def test_start_review_dry_run_then_commit(self) -> None:
        sid = self._import_fixture()
        dry = backend.run_transition(sid, "start-review", "acceptance-reviewer", self.db)
        self.assertTrue(dry.accepted)
        self.assertFalse(dry.data["committed"])
        self.assertEqual(self._scholar_status(sid), "imported_not_evidence")
        committed = backend.run_transition(sid, "start-review", "acceptance-reviewer", self.db, commit=True)
        self.assertTrue(committed.data["committed"])
        self.assertEqual(self._scholar_status(sid), "under_review")

    def test_approval_and_linked_question_for_both_lens_types(self) -> None:
        for lens_type in ("research_question", "retrieval_lens"):
            with self.subTest(lens_type=lens_type):
                self._clear_transition_rows()
                sid = self._import_fixture()
                backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
                result = backend.run_transition(
                    sid, "approve-to-question", "reviewer", self.db,
                    question_text=f"Final approved {lens_type} text?", lens_type=lens_type, commit=True,
                )
                self.assertTrue(result.data["committed"])
                linked = backend.research_question(result.data["question_id"], self.db)
                self.assertEqual(linked["origin_scholar_id"], sid)
                self.assertEqual(linked["lens_type"], lens_type)
                self.assertEqual(self._scholar_status(sid), "approved_to_question")

    def test_rejection_reason_and_terminal_refusals(self) -> None:
        sid = self._import_fixture()
        backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        rejected = backend.run_transition(
            sid, "reject", "reviewer", self.db, rejection_reason="Outside the approved scope.", commit=True,
        )
        self.assertTrue(rejected.data["committed"])
        row = next(row for row in backend.persistent_rows(self.db) if row["scholar_id"] == sid)
        self.assertEqual(row["status"], "rejected_archived")
        self.assertEqual(row["rejection_reason"], "Outside the approved scope.")
        refused = backend.run_transition(
            sid, "approve-to-question", "reviewer", self.db,
            question_text="Must not be created", lens_type="research_question", commit=True,
        )
        self.assertTrue(refused.refused)
        self.assertEqual(self._question_count(), 0)

    def test_direct_approval_blocked_and_repeated_approval_idempotent(self) -> None:
        sid = self._import_fixture()
        direct = backend.run_transition(
            sid, "approve-to-question", "reviewer", self.db,
            question_text="Direct approval must fail", commit=True,
        )
        self.assertTrue(direct.refused)
        backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        first = backend.run_transition(
            sid, "approve-to-question", "reviewer", self.db, question_text="Approved once?", commit=True,
        )
        repeated = backend.run_transition(
            sid, "approve-to-question", "reviewer", self.db, question_text="Attempted twice?", commit=True,
        )
        self.assertEqual(repeated.data["status"], "already_approved")
        self.assertEqual(repeated.data["question_id"], first.data["question_id"])
        self.assertEqual(self._question_count(), 1)

    def test_blank_transition_fields_are_blocked(self) -> None:
        sid = self._import_fixture()
        blank_actor = backend.run_transition(sid, "start-review", "", self.db)
        self.assertTrue(blank_actor.refused)
        backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        blank_question = backend.run_transition(sid, "approve-to-question", "reviewer", self.db, question_text="")
        blank_reason = backend.run_transition(sid, "reject", "reviewer", self.db, rejection_reason="")
        self.assertTrue(blank_question.refused)
        self.assertTrue(blank_reason.refused)

    def test_transition_uses_argument_array_and_changes_only_governed_tables(self) -> None:
        sid = self._import_fixture()
        before = self._table_counts()
        result = backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        self.assertIsInstance(result.command, tuple)
        self.assertIn("--scholar-id", result.command)
        after = self._table_counts()
        for table, count in before.items():
            if table not in {"scholar_input", "research_question"}:
                self.assertEqual(after[table], count, table)

    def test_consistency_validator_after_approval_and_rejection(self) -> None:
        sid = self._import_fixture()
        backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        backend.run_transition(
            sid, "approve-to-question", "reviewer", self.db,
            question_text="A validator-safe approved question?", commit=True,
        )
        self.assertEqual(self._run_isolated_validator().returncode, 0)
        self._clear_transition_rows()
        sid = self._import_fixture()
        backend.run_transition(sid, "start-review", "reviewer", self.db, commit=True)
        backend.run_transition(sid, "reject", "reviewer", self.db, rejection_reason="Synthetic rejection.", commit=True)
        self.assertEqual(self._run_isolated_validator().returncode, 0)

    def test_status_aware_control_mapping(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.scholar_start_review_button = SimpleNamespace(config=MagicMock())
        app.scholar_approve_button = SimpleNamespace(config=MagicMock())
        app.scholar_reject_button = SimpleNamespace(config=MagicMock())
        for status, expected in [
            ("raw_captured", ("disabled", "disabled", "disabled")),
            ("imported_not_evidence", ("normal", "disabled", "disabled")),
            ("under_review", ("disabled", "normal", "normal")),
            ("approved_to_question", ("disabled", "disabled", "disabled")),
            ("rejected_archived", ("disabled", "disabled", "disabled")),
        ]:
            app._set_scholar_transition_controls(status)
            states = tuple(button.config.call_args.kwargs["state"] for button in (
                app.scholar_start_review_button, app.scholar_approve_button, app.scholar_reject_button
            ))
            self.assertEqual(states, expected)

    def test_cancelled_transition_confirmation_performs_no_commit(self) -> None:
        app = object.__new__(KnowledgePrismApp)
        app.selected_persistent_scholar = {"scholar_id": "KP-SI-000001"}
        app.scholar_review_actor = SimpleNamespace(get=lambda: "reviewer")
        app.scholar_final_question = SimpleNamespace(get=lambda *_: "")
        app.scholar_rejection_reason = SimpleNamespace(get=lambda *_: "")
        app.scholar_review_lens_type = SimpleNamespace(get=lambda: "research_question")
        app.scholar_import_report = SimpleNamespace(delete=MagicMock(), insert=MagicMock())
        app.scholar_input_status = SimpleNamespace(config=MagicMock())
        app.root = SimpleNamespace(update_idletasks=MagicMock())
        preview = backend.TransitionResult((), 0, {
            "status": "ok", "action": "start-review", "from": "imported_not_evidence",
            "to": "under_review", "committed": False,
        }, "", "")
        with patch.object(backend, "run_transition", return_value=preview) as run, patch(
            "gui.knowledge_prism_app.messagebox.askyesno", return_value=False
        ):
            app._run_scholar_transition("start-review")
        self.assertEqual(run.call_count, 1)

    def _import_fixture(self) -> str:
        result = backend.run_importer(self.valid_path, self.db, commit=True)
        return result.assigned_ids[0]

    def _clear_transition_rows(self) -> None:
        with sqlite3.connect(self.db) as con:
            con.execute("DELETE FROM research_question")
            con.execute("DELETE FROM scholar_input")
            con.commit()

    def _scholar_status(self, sid: str) -> str:
        with sqlite3.connect(self.db) as con:
            return con.execute("SELECT status FROM scholar_input WHERE scholar_id=?", (sid,)).fetchone()[0]

    def _question_count(self) -> int:
        with sqlite3.connect(self.db) as con:
            return con.execute("SELECT COUNT(*) FROM research_question").fetchone()[0]

    def _run_isolated_validator(self):
        isolated = self.root / "transition_validator"
        (isolated / "scripts").mkdir(parents=True, exist_ok=True)
        (isolated / "db").mkdir(exist_ok=True)
        shutil.copy2(backend.CONSISTENCY_VALIDATOR, isolated / "scripts")
        shutil.copy2(backend.db_access.ROOT / "db" / "prism_ledger.py", isolated / "db")
        shutil.copy2(self.db, isolated / "db" / "knowledge_prism.db")
        return subprocess.run(
            [sys.executable, str(isolated / "scripts" / backend.CONSISTENCY_VALIDATOR.name)],
            cwd=isolated, text=True, capture_output=True, shell=False,
        )

    def _scholar_count(self) -> int:
        with sqlite3.connect(self.db) as con:
            return con.execute("SELECT COUNT(*) FROM scholar_input").fetchone()[0]

    def _table_counts(self) -> dict[str, int]:
        with sqlite3.connect(self.db) as con:
            tables = [row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )]
            return {table: con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in tables}


if __name__ == "__main__":
    unittest.main()
