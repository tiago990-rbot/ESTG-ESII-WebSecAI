// Synthetic session only, supplied by the local test orchestrator. Never print it.
import { createRequire } from "node:module";
import path from "node:path";
import fs from "node:fs/promises";
import assert from "node:assert/strict";
const require = createRequire(path.resolve(process.env.TEST_FRONTEND_DIR, "package.json"));
const { chromium } = require("playwright");
const browser = await chromium.launch({ channel: "chrome", headless: true });
try {
  const context = await browser.newContext();
  await context.addInitScript(token => localStorage.setItem("websec_token", token), process.env.TEST_SESSION_TOKEN);
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:3000/investigations", { waitUntil: "networkidle" });
  assert.equal(await page.locator(".investigationRow").count(), 1);
  await page.locator(".investigationRow").click();
  await page.waitForURL(/\/investigations\/[a-f0-9-]+$/);
  await page.locator(".evidenceItem").first().waitFor();
  await page.getByText("Concluída", { exact: true }).waitFor();
  assert.equal(await page.locator(".evidenceItem").count(), 4);
  await fs.writeFile(path.join(process.env.TEST_OUTPUT_DIR, "restart-browser.json"), JSON.stringify({ utc: new Date().toISOString(), local_api_and_postgresql_restart: true, existing_session_and_history: true }));
  console.log("Browser after local API + PostgreSQL restart: PASS (synthetic session)");
} finally { await browser.close(); }
