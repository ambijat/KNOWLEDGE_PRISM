import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { chromium } from "playwright-core";

const root = new URL("..", import.meta.url).pathname;
const port = 8769;
const server = spawn("python3", ["-m", "http.server", String(port), "--bind", "127.0.0.1", "--directory", root], { stdio: "ignore" });
const downloadDir = await mkdtemp(path.join(tmpdir(), "kp-harness-download-"));

try {
  await new Promise((resolve) => setTimeout(resolve, 500));
  const browser = await chromium.launch({ executablePath: "/usr/bin/google-chrome", headless: true, args: ["--no-sandbox"] });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
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
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Reset browser data" }).click();
  assert.equal(await page.locator(".draft-card").count(), 0);
  assert.equal(await page.locator("#draft-count").textContent(), "0 of 0 local drafts");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  assert.equal(await page.getByRole("button", { name: "New draft" }).isVisible(), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  assert.deepEqual(pageErrors, []);

  await browser.close();
  console.log("browser acceptance: persistence, search, filters, export, delete, reset, responsive layout — PASS");
} finally {
  server.kill("SIGTERM");
  await rm(downloadDir, { recursive: true, force: true });
}
