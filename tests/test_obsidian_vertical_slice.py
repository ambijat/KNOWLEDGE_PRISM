from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/protocol/examples/obsidian_vertical_slice"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


generator = load_module("obsidian_generator", ROOT / "scripts/09_generate_obsidian_workspace.py")
validator = load_module("obsidian_validator", ROOT / "scripts/08_validate_obsidian_projection.py")


class ObsidianVerticalSliceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name) / "vault"
        generator.apply_sync(FIXTURE, self.vault, True)

    def tearDown(self):
        self.temp.cleanup()

    def test_fixture_researcher_text_is_seeded_and_survives_regeneration(self):
        note = self.vault / "01_concepts/CON-000003 eurasian-integration-working-synthesis.md"
        before = generator.researcher_block(note.read_text(encoding="utf-8"))
        self.assertIn("MUST survive regeneration untouched", before)
        generator.apply_sync(FIXTURE, self.vault, True)
        after = generator.researcher_block(note.read_text(encoding="utf-8"))
        self.assertEqual(before.encode(), after.encode())

    def test_malformed_markers_report_conflict_and_do_not_overwrite(self):
        note = self.vault / "01_concepts/CON-000001 heartland-theory.md"
        malformed = note.read_text(encoding="utf-8").replace(generator.RES_END, "")
        note.write_text(malformed, encoding="utf-8")
        _count, conflicts = generator.apply_sync(FIXTURE, self.vault, True)
        self.assertEqual(1, conflicts)
        self.assertEqual(malformed, note.read_text(encoding="utf-8"))
        reports = list((self.vault / "99_sync_conflicts").glob("*.conflict.md"))
        self.assertEqual(1, len(reports))
        self.assertIn("original file left untouched", reports[0].read_text(encoding="utf-8"))

    def test_invalid_predicate_and_ids_fail_frontend_validation(self):
        payload = {
            "proposal_version": "1.0", "record_id": "PROP-bad",
            "proposal_type": "relationship_proposal", "status": "proposed",
            "rationale": "test", "created_by": "researcher", "created_ts": "now",
            "source_id": "CON-bad", "target_id": "ENT-000001", "predicate": "invented_by_frontend",
        }
        errors = generator.validate_proposal(payload)
        self.assertTrue(any("record_id" in error for error in errors))
        self.assertTrue(any("source_id" in error for error in errors))
        self.assertTrue(any("predicate" in error for error in errors))

    def test_proposal_canonical_self_promotion_fails_backend_schema(self):
        schema = json.loads((ROOT / "docs/protocol/obsidian/schemas/proposal.schema.json").read_text())
        proposal = json.loads((FIXTURE / "proposals/inbox/PROP-000001.json").read_text())
        proposal["status"] = "canonical"
        errors = validator.validate(proposal, schema)
        self.assertTrue(any("expected const 'proposed'" in error for error in errors))

    def test_fixture_proposal_and_synthetic_receipt_conform(self):
        proposal_schema = json.loads((ROOT / "docs/protocol/obsidian/schemas/proposal.schema.json").read_text())
        receipt_schema = json.loads((ROOT / "docs/protocol/obsidian/schemas/decision_receipt.schema.json").read_text())
        proposal = json.loads((self.vault / "proposals/inbox/PROP-000001.json").read_text())
        receipt = json.loads((self.vault / "proposals/receipts/PROP-000001.receipt.json").read_text())
        self.assertEqual([], validator.validate(proposal, proposal_schema))
        self.assertEqual([], validator.validate(receipt, receipt_schema))
        self.assertIsNone(receipt["resulting_record_id"])

    def test_canvas_nodes_reference_real_files(self):
        canvas = json.loads((self.vault / "08_canvases/Knowledge Prism Vertical Slice.canvas").read_text())
        for node in canvas["nodes"]:
            if node.get("type") != "file":
                continue
            path = node["file"]
            self.assertNotIn('"', path)
            self.assertNotIn("'", path)
            self.assertFalse(Path(path).is_absolute())
            resolved = (self.vault / path).resolve()
            self.assertTrue(resolved.is_relative_to(self.vault.resolve()))
            self.assertTrue(resolved.is_file(), path)


if __name__ == "__main__":
    unittest.main()
