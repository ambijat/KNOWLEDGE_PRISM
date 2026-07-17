import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { webcrypto } from "node:crypto";
import test from "node:test";
import {
  CONTRACT, ORGANS, canonicalHash, matchesDraft, toExportRecord, validateDraft,
} from "../core.js";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const fixturePath = new URL("../../docs/protocol/examples/android_exchange_v0.1/android_single_valid_v0.1.json", import.meta.url);
const fixture = JSON.parse(await readFile(fixturePath, "utf8"));

test("frozen contract values and vocabulary are exact", () => {
  assert.deepEqual(CONTRACT, {
    schema_version: "0.2",
    record_type: "scholar_input_not_evidence",
    source: "android_app",
    status: "raw_captured",
    exchange_contract_version: "0.1",
    client_app_version: "browser-harness-0.1.0",
    client_platform: "android",
  });
  assert.equal(ORGANS.length, 16);
  assert.ok(ORGANS.includes("Statement_of_Problem"));
  assert.ok(ORGANS.includes("Unassigned"));
});

test("reference fixture validates and export remains importer-compatible", () => {
  assert.deepEqual(validateDraft(fixture), {});
  const exported = toExportRecord(fixture, "test-batch");
  for (const key of ["schema_version", "record_type", "source", "status"]) assert.equal(exported[key], fixture[key]);
  assert.equal(exported.tags, "fixture;example");
  for (const forbidden of ["scholar_id", "imported_ts", "content_sha256", "became_question", "became_queue_id", "decided_by", "decided_ts", "rejection_reason", "block_no"]) {
    assert.equal(Object.hasOwn(exported, forbidden), false);
  }
});

test("canonical advisory hash matches backend algorithm including NFC", async () => {
  assert.equal(await canonicalHash(fixture), "cd8efcea37f46999718d9e1ed1c8b57599a635bc15c7c6ef0254871d3eab5a4b");
  assert.equal(await canonicalHash({ idea: "e\u0301", raw_notes: null }), await canonicalHash({ idea: "é", raw_notes: "", voice_transcript: "" }));
});

test("validation rejects empty idea, timezone-free timestamp, organ and confidence drift", () => {
  const errors = validateDraft({ idea: " ", captured_ts: "2026-07-10T09:15:00", draft_organ: "Research Questions", confidence: "certain" });
  assert.deepEqual(Object.keys(errors).sort(), ["captured_ts", "confidence", "draft_organ", "idea"]);
});

test("search and filters inspect only the intended local fields", () => {
  assert.equal(matchesDraft(fixture, "BUFFER", "Research_Questions", "medium"), true);
  assert.equal(matchesDraft(fixture, "fixture-context", "", ""), true);
  assert.equal(matchesDraft(fixture, "missing", "", ""), false);
  assert.equal(matchesDraft(fixture, "", "Title", ""), false);
});
