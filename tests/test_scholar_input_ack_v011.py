from __future__ import annotations

"""Acknowledgement contract v0.1.1 tests for scripts/06_import_scholar_input.py.

Every test runs against a DISPOSABLE copy of the live DB (never the real file).
Covers the supervisor's required checks 1-13 (behavioural); the environment-level
checks 14-18 (project/consistency validators, ledger chain, live-DB emptiness,
research-state invariance) are exercised by the project validators and the seal
guard, not duplicated here.
"""

import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMP = ROOT / "scripts/06_import_scholar_input.py"
SRC_DB = ROOT / "db/knowledge_prism.db"
DEX = ROOT / "docs/protocol/examples/android_exchange_v0.1"

SINGLE = DEX / "android_single_valid_v0.1.json"
BATCH = DEX / "android_batch_valid_v0.1.json"
INVALID = DEX / "android_invalid_forbidden_field_v0.1.json"

CANON_SINGLE_HASH = "cd8efcea37f46999718d9e1ed1c8b57599a635bc15c7c6ef0254871d3eab5a4b"


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def load_importer():
    spec = importlib.util.spec_from_file_location("imp06", IMP)
    m = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(m)
    return m


class AckV011(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = Path(tempfile.mkdtemp(prefix="kp_ack_test_"))
        cls.imp = load_importer()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def fresh_db(self):
        p = self.work / f"db_{os.urandom(4).hex()}.db"
        shutil.copy(SRC_DB, p)
        return str(p)

    def run_json(self, db, inp, *extra):
        r = subprocess.run(
            ["python3", str(IMP), "--input", str(inp), "--db", db,
             "--output-format", "json", *extra],
            capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 2, 3), r.stderr)
        return json.loads(r.stdout), r          # stdout must be JSON only

    def run_text(self, db, inp, *extra):
        return subprocess.run(
            ["python3", str(IMP), "--input", str(inp), "--db", db, *extra],
            capture_output=True, text=True)

    def rows(self, db):
        return sqlite3.connect(db).execute(
            "SELECT COUNT(*) FROM scholar_input").fetchone()[0]

    # 1 + 2
    def test_01_dryrun_eligible_no_row(self):
        db = self.fresh_db()
        a, _ = self.run_json(db, BATCH)
        self.assertEqual(a["transaction_result"], "DRY_RUN")
        self.assertFalse(a["committed"])
        self.assertTrue(all(e["result"] == "eligible" for e in a["acks"]))
        self.assertEqual(self.rows(db), 0)

    # 3
    def test_03_commit_imported_id(self):
        db = self.fresh_db()
        a, _ = self.run_json(db, BATCH, "--commit")
        for e in a["acks"]:
            self.assertEqual(e["result"], "imported")
            self.assertTrue(e["backend_scholar_id"].startswith("KP-SI-"))

    # 4 + 5
    def test_04_duplicate_echoes_existing_id_no_new_row(self):
        db = self.fresh_db()
        self.run_json(db, SINGLE, "--commit")
        existing = sqlite3.connect(db).execute(
            "SELECT scholar_id FROM scholar_input").fetchone()[0]
        n_before = self.rows(db)
        a, _ = self.run_json(db, SINGLE)          # re-submit same content
        e = a["acks"][0]
        self.assertEqual(e["result"], "duplicate_skipped")
        self.assertEqual(e["backend_scholar_id"], existing)
        self.assertEqual(self.rows(db), n_before)  # no new row

    # 6
    def test_06_client_record_id_round_trip(self):
        db = self.fresh_db()
        a, _ = self.run_json(db, BATCH)
        got = [e["client_record_id"] for e in a["acks"]]
        want = [r["client_record_id"] for r in read_json(BATCH)]
        self.assertEqual(got, want)

    # 7
    def test_07_invalid_ack(self):
        db = self.fresh_db()
        a, _ = self.run_json(db, INVALID)
        e = a["acks"][0]
        self.assertEqual(e["result"], "invalid")
        self.assertEqual(e["error_code"], "FORBIDDEN_GOVERNANCE_FIELD")
        self.assertIsNone(e["backend_scholar_id"])

    # 8
    def test_08_mixed_batch_refusal(self):
        db = self.fresh_db()
        sv = read_json(SINGLE); iv = read_json(INVALID)
        mixed = self.work / "mixed.json"; write_json(mixed, [sv, iv])
        a, r = self.run_json(db, mixed, "--commit")
        self.assertEqual(a["transaction_result"], "REFUSED_INVALID_IN_BATCH")
        self.assertFalse(a["committed"])
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.rows(db), 0)
        self.assertEqual(sorted(e["result"] for e in a["acks"]),
                         ["batch_refused", "invalid"])

    # 9
    def test_09_missing_client_record_id(self):
        db = self.fresh_db()
        noid = read_json(SINGLE); noid.pop("client_record_id", None)
        f = self.work / "noid.json"; write_json(f, noid)
        a, _ = self.run_json(db, f)
        e = a["acks"][0]
        self.assertIsNone(e["client_record_id"])
        self.assertEqual(e["result"], "eligible")

    # 10
    def test_10_ack_file_output(self):
        db = self.fresh_db()
        af = self.work / "out_ack.json"
        r = self.run_text(db, SINGLE, "--ack-file", str(af))
        self.assertTrue(af.exists())
        read_json(af)                             # valid JSON
        self.assertIn("=== SCHOLAR-INPUT IMPORT REPORT ===", r.stdout)

    # 11
    def test_11_text_output_byte_identical_to_committed_baseline(self):
        base = self.work / "06_before.py"
        base.write_text(subprocess.run(
            ["git", "show", "HEAD:scripts/06_import_scholar_input.py"],
            cwd=ROOT, capture_output=True, text=True).stdout)
        for f in (SINGLE, BATCH, INVALID):
            a = subprocess.run(["python3", str(base), "--input", str(f),
                                "--db", self.fresh_db()],
                               capture_output=True, text=True).stdout
            b = self.run_text(self.fresh_db(), f).stdout
            self.assertEqual(a, b, f"text diff on {f.name}")
        # commit path modulo the imported_ts line
        la = [l for l in subprocess.run(
            ["python3", str(base), "--input", str(BATCH), "--db",
             self.fresh_db(), "--commit"], capture_output=True, text=True
        ).stdout.splitlines() if not l.startswith("imported_ts:")]
        lb = [l for l in self.run_text(self.fresh_db(), BATCH, "--commit"
              ).stdout.splitlines() if not l.startswith("imported_ts:")]
        self.assertEqual(la, lb)

    # 12
    def test_12_canonical_hash_unchanged(self):
        rec = read_json(SINGLE)
        self.assertEqual(self.imp.content_sha256(rec), CANON_SINGLE_HASH)

    # 13
    def test_13_v01_input_still_accepted(self):
        db = self.fresh_db()
        a, r = self.run_json(db, SINGLE)          # fixture declares v0.1
        self.assertEqual(r.returncode, 0)
        self.assertEqual(a["acks"][0]["result"], "eligible")

    def test_14_versions_frozen_at_011(self):
        self.assertEqual(self.imp.ACK_SCHEMA_VERSION, "0.1.1")
        self.assertEqual(self.imp.EXCHANGE_CONTRACT_VERSION, "0.1.1")

    def test_15_json_mode_stdout_is_json_only(self):
        # --output-format json must put NOTHING but the ack object on stdout,
        # so a client can json.loads(stdout) directly.
        db = self.fresh_db()
        r = subprocess.run(["python3", str(IMP), "--input", str(BATCH),
                            "--db", db, "--output-format", "json"],
                           capture_output=True, text=True)
        obj = json.loads(r.stdout)                 # raises if any non-JSON leaked
        self.assertEqual(obj["ack_schema_version"], "0.1.1")
        self.assertEqual(obj["transaction_result"], "DRY_RUN")
        # commit path too
        r2 = subprocess.run(["python3", str(IMP), "--input", str(BATCH),
                             "--db", self.fresh_db(), "--output-format", "json",
                             "--commit"], capture_output=True, text=True)
        obj2 = json.loads(r2.stdout)
        self.assertEqual(obj2["transaction_result"], "COMMITTED")
        self.assertEqual([a["result"] for a in obj2["acks"]],
                         ["imported", "imported"])


if __name__ == "__main__":
    unittest.main(verbosity=2)