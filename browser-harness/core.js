export const CONTRACT = Object.freeze({
  schema_version: "0.2",
  record_type: "scholar_input_not_evidence",
  source: "android_app",
  status: "raw_captured",
  exchange_contract_version: "0.1",
  client_app_version: "browser-harness-0.1.0",
  client_platform: "android",
});

export const ORGANS = Object.freeze([
  "Title", "Background", "Statement_of_Problem", "Research_Gap",
  "Research_Questions", "Objectives", "Scope", "Methodology",
  "Conceptual_Framework", "Literature_Clusters", "Evidence_Needs",
  "Case_Region_Time_Period", "Chapterisation", "Supervisor_Questions",
  "Revision_Tasks", "Unassigned",
]);

export const CONTENT_FIELDS = Object.freeze([
  "idea", "draft_organ", "draft_diagnosis", "draft_search_plan",
  "supervisor_brief", "raw_notes", "voice_transcript", "tags",
  "confidence", "project_title", "course_or_context", "device_alias",
]);

export const ACK_SCHEMA_VERSION = "0.1.1";

export const ACK_RESULT_STATES = Object.freeze({
  eligible: "eligible_acknowledged",
  imported: "imported_acknowledged",
  duplicate_skipped: "duplicate_acknowledged",
  invalid: "invalid_acknowledged",
  batch_refused: "batch_refused_acknowledged",
  transport_failed: "transport_failed_acknowledged",
});

const ACK_RECORD_FIELDS = Object.freeze([
  "client_record_id", "result", "backend_scholar_id", "content_sha256",
  "message", "error_code",
]);

export const emptyContent = () => ({
  idea: "",
  draft_organ: "Unassigned",
  draft_diagnosis: "",
  draft_search_plan: "",
  supervisor_brief: "",
  raw_notes: "",
  voice_transcript: "",
  tags: "",
  confidence: "",
  project_title: "",
  course_or_context: "",
  device_alias: "",
});

export function canonicalContent(record) {
  return ["idea", "raw_notes", "voice_transcript"]
    .map((field) => String(record[field] ?? ""))
    .join("\n")
    .normalize("NFC");
}

export async function canonicalHash(record) {
  const bytes = new TextEncoder().encode(canonicalContent(record));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function hasTimezone(value) {
  return typeof value === "string"
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
    && !Number.isNaN(Date.parse(value));
}

export function validateDraft(draft) {
  const errors = {};
  if (!String(draft.idea ?? "").trim()) errors.idea = "Please enter an idea before exporting.";
  if (!hasTimezone(draft.captured_ts)) errors.captured_ts = "Captured time must be ISO-8601 with a timezone.";
  if (!ORGANS.includes(draft.draft_organ)) errors.draft_organ = "Choose a valid section (organ).";
  if (draft.confidence && !["low", "medium", "high"].includes(draft.confidence)) {
    errors.confidence = "Choose low, medium, high, or leave confidence blank.";
  }
  return errors;
}

export function isValidDraft(draft) {
  return Object.keys(validateDraft(draft)).length === 0;
}

export function toExportRecord(draft, batchId) {
  const record = { ...CONTRACT };
  for (const field of CONTENT_FIELDS) record[field] = String(draft[field] ?? "");
  return {
    ...record,
    captured_ts: draft.captured_ts,
    client_record_id: draft.client_record_id,
    client_generated_ts: draft.client_generated_ts,
    client_updated_ts: draft.client_updated_ts,
    export_batch_id: batchId,
  };
}

export function matchesDraft(draft, query, organ, confidence) {
  const haystack = [draft.idea, draft.tags, draft.project_title, draft.course_or_context]
    .map((value) => String(value ?? "").toLocaleLowerCase())
    .join(" ");
  return (!query.trim() || haystack.includes(query.trim().toLocaleLowerCase()))
    && (!organ || draft.draft_organ === organ)
    && (!confidence || draft.confidence === confidence);
}

export function humanOrgan(token) {
  return token.replaceAll("_", " ");
}

function acknowledgementError(message) {
  const error = new Error(message);
  error.name = "AcknowledgementValidationError";
  return error;
}

function nullableString(value) {
  return value === null || typeof value === "string";
}

export function validateAcknowledgement(batch) {
  if (!batch || typeof batch !== "object" || Array.isArray(batch)) {
    throw acknowledgementError("Acknowledgement must be a JSON object.");
  }
  if (batch.ack_schema_version !== ACK_SCHEMA_VERSION) {
    throw acknowledgementError(`Unsupported acknowledgement version: ${String(batch.ack_schema_version ?? "missing")}. Expected ${ACK_SCHEMA_VERSION}.`);
  }
  if (!Array.isArray(batch.acks)) {
    throw acknowledgementError("Malformed acknowledgement: acks must be an array.");
  }
  batch.acks.forEach((ack, index) => {
    if (!ack || typeof ack !== "object" || Array.isArray(ack)) {
      throw acknowledgementError(`Malformed acknowledgement record ${index + 1}: expected an object.`);
    }
    for (const field of ACK_RECORD_FIELDS) {
      if (!Object.hasOwn(ack, field)) {
        throw acknowledgementError(`Malformed acknowledgement record ${index + 1}: missing ${field}.`);
      }
    }
    if (!Object.hasOwn(ACK_RESULT_STATES, ack.result)) {
      throw acknowledgementError(`Malformed acknowledgement record ${index + 1}: unsupported result ${String(ack.result)}.`);
    }
    for (const field of ["client_record_id", "backend_scholar_id", "content_sha256", "message", "error_code"]) {
      if (!nullableString(ack[field])) {
        throw acknowledgementError(`Malformed acknowledgement record ${index + 1}: ${field} must be a string or null.`);
      }
    }
  });
  return batch;
}

export function parseAcknowledgementText(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw acknowledgementError("Malformed acknowledgement JSON. No drafts were changed.");
  }
  return validateAcknowledgement(parsed);
}

function incomingFields(batch, ack) {
  return {
    last_ack_result: ack.result,
    backend_scholar_id: ack.backend_scholar_id,
    backend_content_sha256: ack.content_sha256,
    acknowledgement_message: ack.message,
    acknowledgement_error_code: ack.error_code,
    acknowledgement_batch_id: batch.batch_id ?? null,
    acknowledgement_contract_version: batch.exchange_contract_version ?? null,
  };
}

export function sameAcknowledgement(draft, batch, ack) {
  return Object.entries(incomingFields(batch, ack))
    .every(([field, value]) => (draft[field] ?? null) === value);
}

export function planAcknowledgementImport(batch, drafts) {
  validateAcknowledgement(batch);
  const byClientId = new Map();
  for (const draft of drafts) byClientId.set(draft.client_record_id, draft);
  const groups = new Map();
  const unmatched = [];
  for (const ack of batch.acks) {
    if (!ack.client_record_id || !byClientId.has(ack.client_record_id)) {
      unmatched.push(ack);
      continue;
    }
    const group = groups.get(ack.client_record_id) ?? [];
    group.push(ack);
    groups.set(ack.client_record_id, group);
  }
  const matches = [...groups].map(([clientRecordId, acknowledgements]) => {
    const draft = byClientId.get(clientRecordId);
    const incoming = acknowledgements.at(-1);
    return {
      clientRecordId,
      draft,
      incoming,
      acknowledgements,
      conflict: acknowledgements.length > 1,
      replacement: Boolean(draft.last_ack_result) && !sameAcknowledgement(draft, batch, incoming),
      unchanged: sameAcknowledgement(draft, batch, incoming),
    };
  });
  return {
    batch,
    matches,
    unmatched,
    summary: {
      matched: matches.length,
      unmatched: unmatched.length,
      invalid: batch.acks.filter((ack) => ack.result === "invalid").length,
      unchanged: matches.filter((match) => match.unchanged).length,
    },
  };
}

export function applyAcknowledgement(draft, batch, ack, acknowledgedTs = new Date().toISOString()) {
  validateAcknowledgement(batch);
  if (sameAcknowledgement(draft, batch, ack)) return draft;
  const next = {
    ...draft,
    ...incomingFields(batch, ack),
    acknowledged_ts: acknowledgedTs,
    local_state: ACK_RESULT_STATES[ack.result],
  };
  if (draft.last_ack_result) {
    const previous = {
      ...Object.fromEntries(Object.keys(incomingFields(batch, ack)).map((field) => [field, draft[field] ?? null])),
      acknowledged_ts: draft.acknowledged_ts ?? null,
      replaced_ts: acknowledgedTs,
    };
    next.acknowledgement_history = [...(draft.acknowledgement_history ?? []), previous];
    next.acknowledgement_replaced_ts = acknowledgedTs;
  }
  return next;
}
