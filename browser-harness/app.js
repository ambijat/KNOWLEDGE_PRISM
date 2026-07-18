import {
  ACK_RESULT_STATES, CONTENT_FIELDS, ORGANS, applyAcknowledgement, canonicalHash,
  emptyContent, humanOrgan, isValidDraft, matchesDraft, parseAcknowledgementText,
  planAcknowledgementImport, toExportRecord, validateDraft,
} from "./core.js";

const STORAGE_KEY = "knowledge-prism.scholar-capture-harness.v0.1";
const $ = (selector) => document.querySelector(selector);
const form = $("#draft-form");
let state = loadState();
let acknowledgementView = state.acknowledgementImport ?? null;
let hashSequence = 0;

function loadState() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (parsed && Array.isArray(parsed.drafts)) {
      return {
        drafts: parsed.drafts,
        selectedId: parsed.selectedId ?? null,
        acknowledgementImport: parsed.acknowledgementImport ?? null,
      };
    }
  } catch { /* Corrupt harness data is treated as empty and never exported. */ }
  return { drafts: [], selectedId: null };
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function utcNow() {
  return new Date().toISOString();
}

function uuid() {
  return crypto.randomUUID();
}

function newDraft() {
  const now = utcNow();
  const draft = {
    ...emptyContent(),
    client_record_id: uuid(),
    captured_ts: now,
    client_generated_ts: now,
    client_updated_ts: now,
    local_state: "draft_local",
  };
  state.drafts.unshift(draft);
  state.selectedId = draft.client_record_id;
  persist();
  render();
  form.elements.idea.focus();
}

function selectedDraft() {
  return state.drafts.find((draft) => draft.client_record_id === state.selectedId) ?? null;
}

function valuesFromForm(draft) {
  const values = { ...draft };
  for (const field of CONTENT_FIELDS) values[field] = form.elements[field].value;
  values.captured_ts = form.elements.captured_ts.value;
  return values;
}

function saveDraft(showStatus = true) {
  const index = state.drafts.findIndex((draft) => draft.client_record_id === state.selectedId);
  if (index < 0) return null;
  const updated = valuesFromForm(state.drafts[index]);
  updated.client_updated_ts = utcNow();
  updated.local_state = updated.last_ack_result
    ? ACK_RESULT_STATES[updated.last_ack_result]
    : (isValidDraft(updated) ? "ready_to_export" : "draft_local");
  state.drafts[index] = updated;
  persist();
  if (showStatus) $("#save-status").textContent = "Saved in this browser.";
  renderList();
  renderValidation(updated, false);
  updateEditorHeading(updated);
  updateHash(updated);
  return updated;
}

function render() {
  populateOptions();
  renderList();
  renderAcknowledgementSummary();
  renderEditor();
}

function populateOptions() {
  const formSelect = form.elements.draft_organ;
  const filterSelect = $("#organ-filter");
  if (formSelect.options.length) return;
  for (const organ of ORGANS) {
    formSelect.add(new Option(humanOrgan(organ), organ));
    filterSelect.add(new Option(humanOrgan(organ), organ));
  }
}

function renderList() {
  const query = $("#search").value;
  const organ = $("#organ-filter").value;
  const confidence = $("#confidence-filter").value;
  const drafts = state.drafts.filter((draft) => matchesDraft(draft, query, organ, confidence));
  const list = $("#draft-list");
  list.replaceChildren(...drafts.map((draft) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `draft-card${draft.client_record_id === state.selectedId ? " active" : ""}`;
    button.dataset.id = draft.client_record_id;
    const title = document.createElement("strong");
    title.textContent = draft.idea.trim() || "Untitled draft";
    const meta = document.createElement("span");
    const organLabel = humanOrgan(draft.draft_organ || "Unassigned");
    meta.textContent = `${organLabel} · ${draft.confidence || "no confidence"}`;
    const local = document.createElement("small");
    local.textContent = draft.local_state || "draft_local";
    button.append(title, meta, local);
    if (draft.last_ack_result) {
      const badge = document.createElement("em");
      badge.className = "ack-badge";
      badge.textContent = `ack · ${draft.last_ack_result}`;
      button.append(badge);
    }
    button.addEventListener("click", () => { state.selectedId = draft.client_record_id; persist(); render(); });
    return button;
  }));
  $("#draft-count").textContent = `${drafts.length} of ${state.drafts.length} local draft${state.drafts.length === 1 ? "" : "s"}`;
  $("#empty-inbox").hidden = drafts.length !== 0;
}

function renderEditor() {
  const draft = selectedDraft();
  $("#welcome").hidden = Boolean(draft);
  form.hidden = !draft;
  if (!draft) return;
  for (const field of CONTENT_FIELDS) form.elements[field].value = draft[field] ?? "";
  form.elements.captured_ts.value = draft.captured_ts ?? "";
  $("#save-status").textContent = "";
  updateEditorHeading(draft);
  renderDraftAcknowledgement(draft);
  renderValidation(draft, false);
  updateHash(draft);
}

function updateEditorHeading(draft) {
  $("#editor-title").textContent = draft.idea.trim() || "Untitled draft";
  $("#record-id").textContent = `client_record_id · ${draft.client_record_id}`;
  $("#local-state").textContent = draft.local_state || "draft_local";
  $("#export-draft").disabled = !isValidDraft(draft);
}

function renderDraftAcknowledgement(draft) {
  const panel = $("#draft-ack");
  panel.hidden = !draft.last_ack_result;
  if (!draft.last_ack_result) return;
  $("#draft-ack-result").textContent = draft.last_ack_result;
  $("#draft-backend-row").hidden = !draft.backend_scholar_id;
  $("#draft-backend-id").textContent = draft.backend_scholar_id ?? "";
  $("#draft-ack-error-row").hidden = !draft.acknowledgement_error_code;
  $("#draft-ack-error-code").textContent = draft.acknowledgement_error_code ?? "";
  $("#draft-ack-batch").textContent = draft.acknowledgement_batch_id ?? "not supplied";
  $("#draft-ack-message").textContent = draft.acknowledgement_message ?? "No message supplied.";
}

function safeAckSummary(ack) {
  return {
    client_record_id: ack.client_record_id,
    result: ack.result,
    content_sha256: ack.content_sha256,
    backend_scholar_id: ack.backend_scholar_id,
    message: ack.message,
    error_code: ack.error_code,
  };
}

function appendAckRecord(container, ack, prefix = "") {
  const card = document.createElement("article");
  card.className = "unmatched-ack";
  const heading = document.createElement("strong");
  heading.textContent = `${prefix}${ack.result}`;
  const details = document.createElement("p");
  details.textContent = [
    ack.client_record_id ? `client ${ack.client_record_id}` : "client ID not supplied",
    ack.backend_scholar_id ? `backend ${ack.backend_scholar_id}` : null,
    ack.content_sha256 ? `hash ${ack.content_sha256}` : null,
    ack.error_code ? `error ${ack.error_code}` : null,
  ].filter(Boolean).join(" · ");
  const message = document.createElement("small");
  message.textContent = ack.message ?? "No message supplied.";
  card.append(heading, details, message);
  container.append(card);
}

function renderAcknowledgementSummary() {
  const panel = $("#ack-panel");
  panel.hidden = !acknowledgementView;
  if (!acknowledgementView) return;
  $("#ack-batch").textContent = acknowledgementView.batchId ? `batch · ${acknowledgementView.batchId}` : "";
  const error = $("#ack-error");
  error.hidden = !acknowledgementView.error;
  error.textContent = acknowledgementView.error ?? "";
  const counts = $("#ack-counts");
  counts.replaceChildren();
  for (const key of ["matched", "unmatched", "invalid", "unchanged"]) {
    const item = document.createElement("span");
    const value = document.createElement("strong");
    value.textContent = String(acknowledgementView.summary?.[key] ?? 0);
    item.append(value, document.createTextNode(key));
    counts.append(item);
  }
  const conflicts = $("#ack-conflicts");
  conflicts.replaceChildren();
  for (const conflict of acknowledgementView.conflicts ?? []) {
    const note = document.createElement("p");
    note.className = "ack-conflict";
    note.textContent = `Conflict for ${conflict.client_record_id}: ${conflict.results.join(" → ")}. ${conflict.applied ? "Explicitly confirmed." : "Left unchanged."}`;
    conflicts.append(note);
  }
  const unmatched = $("#ack-unmatched");
  unmatched.replaceChildren();
  if (acknowledgementView.unmatched?.length) {
    const heading = document.createElement("h3");
    heading.textContent = "Unmatched acknowledgement records";
    unmatched.append(heading);
    for (const ack of acknowledgementView.unmatched) appendAckRecord(unmatched, ack);
  }
}

async function importAcknowledgement(file) {
  let batch;
  try {
    batch = parseAcknowledgementText(await file.text());
  } catch (error) {
    acknowledgementView = { error: error.message, summary: { matched: 0, unmatched: 0, invalid: 0, unchanged: 0 } };
    renderAcknowledgementSummary();
    return;
  }
  const plan = planAcknowledgementImport(batch, state.drafts);
  let unchanged = plan.summary.unchanged;
  const conflicts = [];
  const nextDrafts = [...state.drafts];
  for (const match of plan.matches) {
    if (match.unchanged) continue;
    const needsConfirmation = match.conflict || match.replacement;
    let approved = true;
    if (needsConfirmation) {
      const existing = match.draft.last_ack_result ?? "none";
      const incoming = match.acknowledgements.map((ack) => ack.result).join(" → ");
      approved = confirm(`Acknowledgement conflict for ${match.clientRecordId}. Existing: ${existing}. Incoming: ${incoming}. Apply the final incoming result?`);
    }
    if (match.conflict) {
      conflicts.push({
        client_record_id: match.clientRecordId,
        results: match.acknowledgements.map((ack) => ack.result),
        applied: approved,
      });
    }
    if (!approved) {
      unchanged += 1;
      continue;
    }
    const index = nextDrafts.findIndex((draft) => draft.client_record_id === match.clientRecordId);
    nextDrafts[index] = applyAcknowledgement(nextDrafts[index], batch, match.incoming, utcNow());
  }
  state.drafts = nextDrafts;
  acknowledgementView = {
    error: null,
    batchId: batch.batch_id ?? null,
    contractVersion: batch.exchange_contract_version ?? null,
    summary: { ...plan.summary, unchanged },
    conflicts,
    unmatched: plan.unmatched.map(safeAckSummary),
  };
  state.acknowledgementImport = acknowledgementView;
  persist();
  render();
}

function renderValidation(draft, announce) {
  const errors = validateDraft(draft);
  document.querySelectorAll("[data-error]").forEach((node) => {
    node.textContent = errors[node.dataset.error] ?? "";
  });
  if (announce && Object.keys(errors).length) $("#save-status").textContent = "Draft saved, but export validation needs attention.";
  return errors;
}

async function updateHash(draft) {
  const sequence = ++hashSequence;
  const hash = await canonicalHash(draft);
  if (sequence === hashSequence && draft.client_record_id === state.selectedId) $("#canonical-hash").textContent = hash;
}

function deleteDraft() {
  const draft = selectedDraft();
  if (!draft || !confirm("Delete this local draft? This cannot be undone.")) return;
  state.drafts = state.drafts.filter((item) => item.client_record_id !== draft.client_record_id);
  state.selectedId = state.drafts[0]?.client_record_id ?? null;
  persist();
  render();
}

function resetData() {
  if (!confirm("Reset all Scholar Capture browser data? Every local draft will be deleted.")) return;
  localStorage.removeItem(STORAGE_KEY);
  state = { drafts: [], selectedId: null, acknowledgementImport: null };
  acknowledgementView = null;
  render();
}

function exportDraft() {
  const draft = saveDraft(false);
  const errors = renderValidation(draft, true);
  if (Object.keys(errors).length) return;
  const batchId = `browser-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${draft.client_record_id.slice(0, 8)}`;
  const record = toExportRecord(draft, batchId);
  const blob = new Blob([`${JSON.stringify(record, null, 2)}\n`], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `kp_scholar_export_${batchId}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
  if (!draft.last_ack_result) draft.local_state = "exported_unacknowledged";
  persist();
  renderList();
  updateEditorHeading(draft);
  $("#save-status").textContent = "Plaintext JSON exported. Import a desktop acknowledgement explicitly when available.";
}

$("#new-draft").addEventListener("click", newDraft);
form.addEventListener("submit", (event) => { event.preventDefault(); const draft = saveDraft(); renderValidation(draft, true); });
form.addEventListener("input", () => {
  const draft = selectedDraft();
  if (!draft) return;
  const preview = valuesFromForm(draft);
  $("#save-status").textContent = "Unsaved local changes.";
  updateEditorHeading(preview);
  updateHash(preview);
});
$("#delete-draft").addEventListener("click", deleteDraft);
$("#reset-data").addEventListener("click", resetData);
$("#export-draft").addEventListener("click", exportDraft);
$("#import-ack").addEventListener("click", () => { $("#ack-file").value = ""; $("#ack-file").click(); });
$("#ack-file").addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) importAcknowledgement(file);
});
for (const selector of ["#search", "#organ-filter", "#confidence-filter"]) $(selector).addEventListener("input", renderList);

render();
