// Against tests.e2e_backend only: no real provider calls, no credential output.
import { createRequire } from "node:module";
import { randomBytes } from "node:crypto";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
const require = createRequire(path.resolve(process.env.TEST_FRONTEND_DIR || "frontend", "package.json"));
const { chromium } = require("playwright");
const browser = await chromium.launch({ channel: "chrome", headless: true });
const base = process.env.WEBSECAI_WEB_URL || "http://127.0.0.1:3000";
const contexts = [];
const errors = [], outside = [];
const out = path.resolve(process.env.TEST_OUTPUT_DIR || "test-results");
await fs.mkdir(out, { recursive: true });
try {
  let demoId;
  for (let i = 0; i < 3; i++) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
    contexts.push(context);
    const page = await context.newPage();
    page.on("pageerror", e => errors.push(e.message));
    await context.route("**/*", route => {
      const host = new URL(route.request().url()).hostname;
      if (!["127.0.0.1", "localhost"].includes(host)) { outside.push(host); return route.abort(); }
      return route.continue();
    });
    const name = "deploy_" + randomBytes(5).toString("hex");
    await page.goto(base + "/register", { waitUntil: "networkidle" });
    await page.getByLabel("Username", { exact: true }).fill(name);
    await page.getByLabel("Email", { exact: true }).fill(name + "@example.com");
    await page.getByLabel("Palavra-passe", { exact: true }).fill(randomBytes(24).toString("base64url"));
    await page.getByRole("button", { name: "Criar conta", exact: true }).click();
    await page.waitForURL("**/investigations");
    await page.getByRole("button", { name: "Experimentar demonstração", exact: true }).waitFor();
    if (i > 0) {
      assert.equal(await page.locator(".investigationRow").count(), 0);
      const status = await page.evaluate(async id => {
        const r = await fetch("http://127.0.0.1:8000/api/v1/investigations/" + id, { headers: { Authorization: "Bearer " + localStorage.getItem("websec_token") } });
        return r.status;
      }, demoId);
      assert.equal(status, 404);
    }
    await page.getByRole("button", { name: "Experimentar demonstração", exact: true }).click();
    await page.waitForURL(/\/investigations\/[a-f0-9-]+$/);
    await page.getByText("Concluída", { exact: true }).waitFor();
    assert.equal(await page.locator(".evidenceItem").count(), 4);
    await page.locator(".demoBanner").waitFor();
    if (i === 0) demoId = new URL(page.url()).pathname.split("/").at(-1);
    const downloading = page.waitForEvent("download");
    await page.getByRole("button", { name: "Exportar PDF", exact: true }).click();
    const download = await downloading;
    const pdf = path.join(out, "demo-" + i + ".pdf");
    await download.saveAs(pdf);
    assert.equal((await fs.readFile(pdf)).subarray(0, 4).toString(), "%PDF");
    await page.reload({ waitUntil: "networkidle" });
    await page.getByText("Concluída", { exact: true }).waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: path.join(out, "demo-mobile-" + i + ".png") });
    await page.goto(base + "/history/123456", { waitUntil: "networkidle" });
    await page.getByText("Scan não encontrado", { exact: false }).waitFor();
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(outside, []);
  const result = { utc: new Date().toISOString(), mode: process.env.TEST_RUNTIME || "local_next_api_postgresql", synthetic_accounts: 3,
    demo_evidence_and_pdf: true, individual_authorization: true, reload_persistence: true,
    mobile_390: true, dynamic_investigation_and_history_routes: true, browser_errors: 0, external_browser_requests: 0 };
  await fs.writeFile(path.join(out, "deployment-browser.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally {
  await Promise.all(contexts.map(c => c.close()));
  await browser.close();
}
