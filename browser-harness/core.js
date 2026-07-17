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
