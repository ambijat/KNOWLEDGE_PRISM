import {
  CONTENT_FIELDS, ORGANS, canonicalHash, emptyContent, humanOrgan,
  isValidDraft, matchesDraft, toExportRecord, validateDraft,
} from "./core.js";

const STORAGE_KEY = "knowledge-prism.scholar-capture-harness.v0.1";
const $ = (selector) => document.querySelector(selector);
const form = $("#draft-form");
let state = loadState();
let hashSequence = 0;

function loadState() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY));
    if (parsed && Array.isArray(parsed.drafts)) return { drafts: parsed.drafts, selectedId: parsed.selectedId ?? null };
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
  updated.local_state = isValidDraft(updated) ? "ready_to_export" : "draft_local";
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
  renderValidation(draft, false);
  updateHash(draft);
}

function updateEditorHeading(draft) {
  $("#editor-title").textContent = draft.idea.trim() || "Untitled draft";
  $("#record-id").textContent = `client_record_id · ${draft.client_record_id}`;
  $("#local-state").textContent = draft.local_state || "draft_local";
  $("#export-draft").disabled = !isValidDraft(draft);
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
  state = { drafts: [], selectedId: null };
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
  draft.local_state = "exported_unacknowledged";
  persist();
  renderList();
  updateEditorHeading(draft);
  $("#save-status").textContent = "Plaintext JSON exported. Desktop acknowledgement is not part of this harness.";
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
for (const selector of ["#search", "#organ-filter", "#confidence-filter"]) $(selector).addEventListener("input", renderList);

render();
