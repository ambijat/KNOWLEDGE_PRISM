import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { chromium } from "playwright-core";

const root = new URL("..", import.meta.url).pathname;
const ackRoot = new URL("../../docs/protocol/examples/android_exchange_v0.1.1/", import.meta.url).pathname;
const ackFile = (name) => path.join(ackRoot, name);
const port = 8769;
const server = spawn("python3", ["-m", "http.server", String(port), "--bind", "127.0.0.1", "--directory", root], { stdio: "ignore" });
const downloadDir = await mkdtemp(path.join(tmpdir(), "kp-harness-download-"));

try {
  await new Promise((resolve) => setTimeout(resolve, 500));
  const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const waitForText = (selector, expected) => page.waitForFunction(
    ([target, text]) => document.querySelector(target)?.textContent === text,
    [selector, expected],
  );
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  await page.goto(`http://127.0.0.1:${port}`);

  await page.getByRole("button", { name: "New draft" }).click();
  await page.locator('[name="idea"]').fill("Persistence acceptance idea");
  await page.locator('[name="draft_organ"]').selectOption("Research_Questions");
  await page.locator('[name="confidence"]').selectOption("medium");
  await page.locator('[name="tags"]').fill("acceptance;browser");
  await page.getByText("Sensitive source material", { exact: true }).click();
  await page.locator('[name="raw_notes"]').fill("Disposable acceptance note.");
  await page.getByRole("button", { name: "Save locally" }).click();
  await page.reload();
  await page.locator('[name="idea"]').waitFor();
  assert.equal(await page.locator('[name="idea"]').inputValue(), "Persistence acceptance idea");
  assert.equal(await page.locator("#local-state").textContent(), "ready_to_export");

  await page.getByRole("button", { name: "New draft" }).click();
  await page.locator('[name="idea"]').fill("Second filter target");
  await page.locator('[name="draft_organ"]').selectOption("Methodology");
  await page.locator('[name="confidence"]').selectOption("high");
  await page.getByRole("button", { name: "Save locally" }).click();
  await page.locator("#search").fill("Persistence");
  assert.equal(await page.locator(".draft-card").count(), 1);
  await page.locator("#search").fill("");
  await page.locator("#organ-filter").selectOption("Methodology");
  assert.equal(await page.locator(".draft-card").count(), 1);
  await page.locator("#confidence-filter").selectOption("medium");
  assert.equal(await page.locator(".draft-card").count(), 0);
  await page.locator("#organ-filter").selectOption("");
  await page.locator("#confidence-filter").selectOption("");

  await page.getByText("Persistence acceptance idea", { exact: true }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export single-record JSON" }).click();
  const download = await downloadPromise;
  const savedPath = path.join(downloadDir, download.suggestedFilename());
  await download.saveAs(savedPath);
  const exported = JSON.parse(await readFile(savedPath, "utf8"));
  assert.equal(exported.idea, "Persistence acceptance idea");
  assert.equal(exported.status, "raw_captured");
  assert.equal(exported.draft_organ, "Research_Questions");
  assert.equal(Object.hasOwn(exported, "content_sha256"), false);
  assert.match(exported.client_record_id, /^[0-9a-f-]{36}$/i);

  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Delete draft" }).click();
  assert.equal(await page.getByText("Persistence acceptance idea", { exact: true }).count(), 0);

  const clientA = "9f1b6a2e-0000-4000-8000-00000000000A";
  const clientB = "9f1b6a2e-0000-4000-8000-00000000000B";
  const clientDuplicate = "9f1b6a2e-0000-4000-8000-000000000001";
  const clientInvalid = "9f1b6a2e-0000-4000-8000-0000000000FF";
  const protectedIdea = "Synthetic acknowledgement acceptance idea";
  await page.evaluate(({ clientA, clientB, clientDuplicate, clientInvalid, protectedIdea }) => {
    const base = (client_record_id, idea) => ({
      client_record_id, idea, raw_notes: "Must remain unchanged", voice_transcript: "Protected voice",
      draft_organ: "Research_Questions", draft_diagnosis: "", draft_search_plan: "", supervisor_brief: "",
      tags: "synthetic;acceptance", confidence: "medium", project_title: "Ack Lab", course_or_context: "Browser",
      device_alias: "", captured_ts: "2026-07-18T00:00:00.000Z", client_generated_ts: "2026-07-18T00:00:00.000Z",
      client_updated_ts: "2026-07-18T00:00:00.000Z", canonical_export_hash: "immutable-hash", local_state: "exported_unacknowledged",
    });
    localStorage.setItem("knowledge-prism.scholar-capture-harness.v0.1", JSON.stringify({
      drafts: [base(clientA, protectedIdea), base(clientB, "Second fixture client"), base(clientDuplicate, "Duplicate fixture client"), base(clientInvalid, "Invalid fixture client")],
      selectedId: clientA,
    }));
  }, { clientA, clientB, clientDuplicate, clientInvalid, protectedIdea });
  await page.reload();
  assert.equal(await page.getByRole("button", { name: "Import acknowledgement" }).isVisible(), true);
  assert.match(await page.locator(".no-evidence-warning").textContent(), /does not mean approved.*or accepted as evidence/);

  const chooserPromise = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Import acknowledgement" }).click();
  const chooser = await chooserPromise;
  await chooser.setFiles(ackFile("android_ack_eligible_v0.1.1.json"));
  await page.getByText("Acknowledgement summary", { exact: true }).waitFor();
  assert.equal(await page.locator("#draft-ack-result").textContent(), "eligible");
  assert.equal(await page.locator("#local-state").textContent(), "eligible_acknowledged");
  assert.equal(await page.locator('[name="idea"]').inputValue(), protectedIdea);
  assert.equal(await page.locator('[name="raw_notes"]').inputValue(), "Must remain unchanged");
  assert.equal(await page.locator("#ack-counts span").nth(0).textContent(), "2matched");

  await page.reload();
  assert.equal(await page.locator("#draft-ack-result").textContent(), "eligible");
  assert.equal(await page.locator("#ack-panel").isVisible(), true);

  const dialogMessages = [];
  let acceptDialogs = true;
  page.on("dialog", async (dialog) => {
    dialogMessages.push(dialog.message());
    if (acceptDialogs) await dialog.accept(); else await dialog.dismiss();
  });
  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_imported_v0.1.1.json"));
  await page.getByText("KP-SI-000001", { exact: true }).waitFor();
  assert.equal(await page.locator("#draft-ack-result").textContent(), "imported");
  assert.equal(await page.locator("#local-state").textContent(), "imported_acknowledged");
  assert.ok(dialogMessages.some((message) => /Existing: eligible.*Incoming: imported/.test(message)));
  assert.equal(await page.locator('[name="idea"]').inputValue(), protectedIdea);

  await page.getByText("Duplicate fixture client", { exact: true }).click();
  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_duplicate_v0.1.1.json"));
  await page.getByText("KP-SI-000001", { exact: true }).waitFor();
  assert.equal(await page.locator("#draft-ack-result").textContent(), "duplicate_skipped");
  assert.equal(await page.locator("#draft-ack-error-code").textContent(), "DUPLICATE_CONTENT");

  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_unmatched_client_v0.1.1.json"));
  await page.getByText("Unmatched acknowledgement records", { exact: true }).waitFor();
  assert.equal(await page.getByText("Unmatched acknowledgement records", { exact: true }).isVisible(), true);
  assert.match(await page.locator("#ack-unmatched").textContent(), /client ID not supplied/);

  await page.getByText("Invalid fixture client", { exact: true }).click();
  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_invalid_v0.1.1.json"));
  await waitForText("#draft-ack-result", "invalid");
  assert.equal(await page.locator("#draft-ack-result").textContent(), "invalid");
  assert.equal(await page.locator("#draft-ack-error-code").textContent(), "FORBIDDEN_GOVERNANCE_FIELD");

  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_batch_refused_v0.1.1.json"));
  await page.waitForFunction(() => document.querySelector("#ack-counts")?.textContent === "2matched0unmatched1invalid0unchanged");
  await page.getByText("Duplicate fixture client", { exact: true }).click();
  await waitForText("#draft-ack-result", "batch_refused");
  assert.equal(await page.locator("#draft-ack-result").textContent(), "batch_refused");

  await page.getByText("Synthetic acknowledgement acceptance idea", { exact: true }).click();
  const transport = {
    name: "transport.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify({
      ack_schema_version: "0.1.1", exchange_contract_version: "0.1.1", batch_id: "transport-test", acks: [{
        client_record_id: clientA, result: "transport_failed", backend_scholar_id: null, content_sha256: null,
        message: "synthetic local transport failure", error_code: "TRANSPORT_FAILURE",
      }],
    })),
  };
  await page.locator("#ack-file").setInputFiles(transport);
  await waitForText("#draft-ack-result", "transport_failed");
  assert.equal(await page.locator("#draft-ack-result").textContent(), "transport_failed");

  const beforeMalformed = await page.evaluate(() => JSON.parse(localStorage.getItem("knowledge-prism.scholar-capture-harness.v0.1")).drafts);
  await page.locator("#ack-file").setInputFiles({ name: "malformed.json", mimeType: "application/json", buffer: Buffer.from("{bad") });
  await page.waitForFunction(() => document.querySelector("#ack-error")?.textContent.includes("Malformed acknowledgement JSON"));
  assert.match(await page.locator("#ack-error").textContent(), /Malformed acknowledgement JSON/);
  let afterRefusal = await page.evaluate(() => JSON.parse(localStorage.getItem("knowledge-prism.scholar-capture-harness.v0.1")).drafts);
  assert.deepEqual(afterRefusal, beforeMalformed);
  await page.locator("#ack-file").setInputFiles({ name: "unsupported.json", mimeType: "application/json", buffer: Buffer.from('{"ack_schema_version":"0.1.0","acks":[]}') });
  await page.waitForFunction(() => document.querySelector("#ack-error")?.textContent.includes("Unsupported acknowledgement version"));
  assert.match(await page.locator("#ack-error").textContent(), /Unsupported acknowledgement version/);
  await page.locator("#ack-file").setInputFiles({ name: "missing-acks.json", mimeType: "application/json", buffer: Buffer.from('{"ack_schema_version":"0.1.1"}') });
  await page.waitForFunction(() => document.querySelector("#ack-error")?.textContent.includes("acks must be an array"));
  assert.match(await page.locator("#ack-error").textContent(), /acks must be an array/);
  afterRefusal = await page.evaluate(() => JSON.parse(localStorage.getItem("knowledge-prism.scholar-capture-harness.v0.1")).drafts);
  assert.deepEqual(afterRefusal, beforeMalformed);

  const conflictBatch = {
    ack_schema_version: "0.1.1", exchange_contract_version: "0.1.1", batch_id: "conflict-test", acks: [
      { client_record_id: clientA, result: "eligible", backend_scholar_id: null, content_sha256: "hash-one", message: "first", error_code: null },
      { client_record_id: clientA, result: "imported", backend_scholar_id: "KP-SI-009999", content_sha256: "hash-two", message: "second", error_code: null },
    ],
  };
  await page.locator("#ack-file").setInputFiles({ name: "conflict.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(conflictBatch)) });
  await page.waitForFunction(() => document.querySelector("#ack-conflicts")?.textContent.includes("Explicitly confirmed"));
  assert.match(await page.locator("#ack-conflicts").textContent(), /eligible → imported.*Explicitly confirmed/);
  assert.equal(await page.locator("#draft-ack-result").textContent(), "imported");

  acceptDialogs = false;
  const rejectionDialog = page.waitForEvent("dialog");
  await page.locator("#ack-file").setInputFiles(ackFile("android_ack_eligible_v0.1.1.json"));
  await rejectionDialog;
  await waitForText("#ack-batch", "batch · batch-0002");
  assert.equal(await page.locator("#draft-ack-result").textContent(), "imported");
  assert.equal(await page.locator('[name="idea"]').inputValue(), protectedIdea);
  assert.ok(dialogMessages.length >= 4);

  acceptDialogs = true;
  await page.getByRole("button", { name: "Reset browser data" }).click();
  assert.equal(await page.locator(".draft-card").count(), 0);
  assert.equal(await page.locator("#draft-count").textContent(), "0 of 0 local drafts");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  assert.equal(await page.getByRole("button", { name: "New draft" }).isVisible(), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  assert.deepEqual(pageErrors, []);
  assert.deepEqual(consoleErrors, []);

  await browser.close();
  console.log("browser acceptance: capture/export regressions, six acknowledgement fixtures, conflicts, persistence, privacy, and responsive layout — PASS");
} finally {
  server.kill("SIGTERM");
  await rm(downloadDir, { recursive: true, force: true });
}
