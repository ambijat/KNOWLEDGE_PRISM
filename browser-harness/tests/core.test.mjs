import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { webcrypto } from "node:crypto";
import test from "node:test";
import {
  ACK_RESULT_STATES, CONTRACT, ORGANS, applyAcknowledgement, canonicalHash,
  matchesDraft, parseAcknowledgementText, planAcknowledgementImport,
  toExportRecord, validateDraft,
} from "../core.js";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const fixturePath = new URL("../../docs/protocol/examples/android_exchange_v0.1/android_single_valid_v0.1.json", import.meta.url);
const fixture = JSON.parse(await readFile(fixturePath, "utf8"));
const ackDirectory = new URL("../../docs/protocol/examples/android_exchange_v0.1.1/", import.meta.url);
const readAck = async (name) => JSON.parse(await readFile(new URL(name, ackDirectory), "utf8"));
const acks = {
  eligible: await readAck("android_ack_eligible_v0.1.1.json"),
  imported: await readAck("android_ack_imported_v0.1.1.json"),
  duplicate: await readAck("android_ack_duplicate_v0.1.1.json"),
  invalid: await readAck("android_ack_invalid_v0.1.1.json"),
  refused: await readAck("android_ack_batch_refused_v0.1.1.json"),
  unmatched: await readAck("android_ack_unmatched_client_v0.1.1.json"),
};

const draftFor = (client_record_id) => ({
  ...fixture,
  client_record_id,
  local_state: "exported_unacknowledged",
});

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

test("all frozen acknowledgement results map only to browser-local presentation states", () => {
  assert.deepEqual(ACK_RESULT_STATES, {
    eligible: "eligible_acknowledged",
    imported: "imported_acknowledged",
    duplicate_skipped: "duplicate_acknowledged",
    invalid: "invalid_acknowledged",
    batch_refused: "batch_refused_acknowledged",
    transport_failed: "transport_failed_acknowledged",
  });
  for (const state of Object.values(ACK_RESULT_STATES)) {
    assert.doesNotMatch(state, /under_review|approved|evidence|verified|ontology/);
  }
});

test("eligible and imported acknowledgements match by client ID", () => {
  for (const [batch, expected] of [[acks.eligible, "eligible_acknowledged"], [acks.imported, "imported_acknowledged"]]) {
    const draft = draftFor(batch.acks[0].client_record_id);
    const plan = planAcknowledgementImport(batch, [draft]);
    assert.deepEqual(plan.summary, { matched: 1, unmatched: 1, invalid: 0, unchanged: 0 });
    const updated = applyAcknowledgement(draft, batch, plan.matches[0].incoming, "2026-07-18T00:00:00.000Z");
    assert.equal(updated.local_state, expected);
    assert.equal(updated.backend_scholar_id, batch.acks[0].backend_scholar_id);
  }
});

test("duplicate, invalid, batch-refused and synthetic transport-failed results are retained", () => {
  const cases = [
    [acks.duplicate, "duplicate_acknowledged"],
    [acks.invalid, "invalid_acknowledged"],
    [acks.refused, "batch_refused_acknowledged"],
  ];
  for (const [batch, expected] of cases) {
    const draft = draftFor(batch.acks[0].client_record_id);
    const plan = planAcknowledgementImport(batch, [draft]);
    assert.equal(applyAcknowledgement(draft, batch, plan.matches[0].incoming).local_state, expected);
  }
  const transport = structuredClone(acks.eligible);
  transport.acks = [{ ...transport.acks[0], result: "transport_failed", message: "local transfer failed", error_code: "TRANSPORT_FAILURE" }];
  const draft = draftFor(transport.acks[0].client_record_id);
  assert.equal(applyAcknowledgement(draft, transport, transport.acks[0]).local_state, "transport_failed_acknowledged");
});

test("malformed JSON, unsupported versions and missing acks are refused", () => {
  assert.throws(() => parseAcknowledgementText("{broken"), /Malformed acknowledgement JSON/);
  assert.throws(() => parseAcknowledgementText('{"ack_schema_version":"0.1.0","acks":[]}'), /Unsupported acknowledgement version/);
  assert.throws(() => parseAcknowledgementText('{"ack_schema_version":"0.1.1"}'), /acks must be an array/);
});

test("null and unknown client IDs remain unmatched without content reconstruction", () => {
  const draft = draftFor("known-client");
  const nullPlan = planAcknowledgementImport(acks.unmatched, [draft]);
  assert.equal(nullPlan.summary.unmatched, 1);
  assert.equal(nullPlan.matches.length, 0);
  const unknown = structuredClone(acks.duplicate);
  unknown.acks[0].client_record_id = "unknown-client";
  const unknownPlan = planAcknowledgementImport(unknown, [draft]);
  assert.equal(unknownPlan.unmatched[0].message, unknown.acks[0].message);
  assert.equal(Object.hasOwn(unknownPlan.unmatched[0], "idea"), false);
});

test("multiple acknowledgements for one client are surfaced as a conflict", () => {
  const batch = structuredClone(acks.eligible);
  const clientId = batch.acks[0].client_record_id;
  batch.acks = [batch.acks[0], { ...batch.acks[0], result: "imported", backend_scholar_id: "KP-SI-009999" }];
  const plan = planAcknowledgementImport(batch, [draftFor(clientId)]);
  assert.equal(plan.matches[0].conflict, true);
  assert.equal(plan.matches[0].acknowledgements.length, 2);
  assert.equal(plan.matches[0].incoming.result, "imported");
});

test("replacement keeps history and never changes capture/export content", () => {
  const clientId = acks.eligible.acks[0].client_record_id;
  const original = draftFor(clientId);
  original.canonical_export_hash = "frozen-export-hash";
  const eligible = applyAcknowledgement(original, acks.eligible, acks.eligible.acks[0], "2026-07-18T01:00:00.000Z");
  const imported = applyAcknowledgement(eligible, acks.imported, acks.imported.acks[0], "2026-07-18T02:00:00.000Z");
  for (const field of ["client_record_id", "idea", "raw_notes", "voice_transcript", "draft_organ", "tags", "project_title", "course_or_context", "captured_ts", "canonical_export_hash"]) {
    assert.equal(imported[field], original[field]);
  }
  assert.equal(imported.acknowledgement_history.length, 1);
  assert.equal(imported.acknowledgement_history[0].last_ack_result, "eligible");
  assert.equal(imported.last_ack_result, "imported");
  assert.equal(imported.acknowledgement_replaced_ts, "2026-07-18T02:00:00.000Z");
  assert.equal(planAcknowledgementImport(acks.imported, [imported]).summary.unchanged, 1);
});
