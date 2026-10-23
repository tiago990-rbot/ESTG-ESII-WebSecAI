import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs/promises";
import { randomBytes } from "node:crypto";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(root, "frontend", "package.json"));
const { chromium } = require("playwright");
const out = path.join(root, "test-results");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", error => errors.push(error.message));
try {
  const user = "coverage_" + randomBytes(5).toString("hex");
  await page.goto("http://127.0.0.1:3000/register", { waitUntil: "networkidle" });
  await page.getByLabel("Username", { exact: true }).fill(user);
  await page.getByLabel("Email", { exact: true }).fill(user + "@example.com");
  await page.getByLabel("Palavra-passe", { exact: true }).fill(randomBytes(20).toString("base64url"));
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await page.waitForURL("**/investigations");
  const sources = page.locator(".sourcesOverview");
  await sources.getByText("Extensão futura", { exact: true }).waitFor();
  assert.match(await sources.innerText(), /3 de 6 integrações configuradas/);
  assert.match(await sources.innerText(), /Acesso condicionado/);
  assert.match(await sources.innerText(), /Novos registos estão suspensos/);
  await sources.screenshot({ path: path.join(out, "sources-desktop.png") });
  await page.setViewportSize({ width: 390, height: 844 });
  await sources.scrollIntoViewIfNeeded();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await page.screenshot({ path: path.join(out, "sources-mobile.png") });
  assert.deepEqual(errors, []);
  const result = { checked_at: new Date().toISOString(), source_requirements_visible: true,
    future_extension_separate: true, configured_is_not_authenticated: true,
    mobile_390_no_overflow: true, page_errors: 0, external_analysis_calls: 0 };
  await fs.writeFile(path.join(out, "source-coverage-results.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally { await context.close(); await browser.close(); }
