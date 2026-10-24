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
    await context.route("**/*", async route => {
      const host = new URL(route.request().url()).hostname;
      // Test the production-built bundle against the isolated offline API.
      // No request is sent to the remote production service.
      if (host === "websecaiapi.onrender.com") {
        const source = new URL(route.request().url());
        const response = await route.fetch({ url: "http://127.0.0.1:8000" + source.pathname + source.search });
        return route.fulfill({ response });
      }
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
    await page.getByRole("button", { name: "Explorar demonstração", exact: true }).waitFor();
    if (i > 0) {
      assert.equal(await page.locator(".investigationRow").count(), 0);
      const status = await page.evaluate(async id => {
        const r = await fetch("http://127.0.0.1:8000/api/v1/investigations/" + id, { headers: { Authorization: "Bearer " + localStorage.getItem("websec_token") } });
        return r.status;
      }, demoId);
      assert.equal(status, 404);
    }
    await page.getByRole("button", { name: "Explorar demonstração", exact: true }).click();
    await page.waitForURL(/\/investigations\/[a-f0-9-]+$/);
    await page.getByText("Concluída", { exact: true }).waitFor();
    await page.getByRole("tab", { name: /^Evidências/ }).click();
    assert.equal(await page.locator(".evidenceItem").count(), 6);
    await page.getByRole("tab", { name: "Contexto global", exact: true }).click();
    assert.equal(await page.locator(".evidenceItem").count(), 1);
    await page.getByRole("heading", { name: "Contexto global sem associação demonstrada ao alvo" }).waitFor();
    await page.getByRole("tab", { name: /^Evidências/ }).click();
    await page.locator(".demoBanner").waitFor();
    if (i === 0) demoId = new URL(page.url()).pathname.split("/").at(-1);
    const downloading = page.waitForEvent("download");
    await page.getByRole("button", { name: /PDF completo/ }).click();
    const download = await downloading;
    const pdf = path.join(out, "demo-" + i + ".pdf");
    await download.saveAs(pdf);
    assert.equal((await fs.readFile(pdf)).subarray(0, 4).toString(), "%PDF");
    await page.reload({ waitUntil: "networkidle" });
    await page.getByText("Concluída", { exact: true }).waitFor();
    await page.getByRole("tab", { name: "Cronologia", exact: true }).click();
    await page.getByLabel("Ordenar por", { exact: true }).selectOption("event_at");
    await page.getByRole("heading", { name: "Cada data no seu contexto.", exact: true }).waitFor();
    await page.getByRole("tab", { name: "Mapa de relações", exact: true }).click();
    await page.getByRole("heading", { name: "Segue o caminho até à fonte.", exact: true }).waitFor();
    await page.getByRole("button", { name: /^Selecionar E2:/ }).press("Enter");
    await page.getByRole("button", { name: /Examinar E2/ }).click();
    await page.waitForURL(/#evidence-/);
    assert.equal(await page.getByRole("tab", { name: /^Evidências/ }).getAttribute("aria-selected"), "true");
    await page.getByRole("tab", { name: "Assistente IA", exact: true }).click();
    await page.getByRole("heading", { name: "Perguntas essenciais", exact: true }).waitFor();
    assert.equal(await page.locator(".wb-answer").count(), 6);
    await page.locator(".wb-answer summary").filter({ hasText: "O histórico e a configuração atual estão relacionados?" }).click();
    assert.equal(await page.locator(".wb-answer[open]").count(), 1);
    await page.getByRole("tab", { name: /^Evidências/ }).click();
    if (i === 0) {
      const card = page.locator(".evidenceItem").first();
      await card.getByText("Revisão humana · Por rever", { exact: true }).click();
      await card.getByLabel("Estado da revisão", { exact: true }).selectOption("reviewed");
      await card.getByLabel("Relação com a organização", { exact: true }).selectOption("uncertain");
      await card.getByLabel("Notas e fundamento", { exact: true }).fill("Revisão sintética; não confirma intrusão.");
      await card.getByRole("button", { name: "Guardar revisão", exact: true }).click();
      await card.getByText("Revisão guardada no histórico.", { exact: false }).waitFor();
      await card.getByText("Histórico de revisões (1)", { exact: true }).waitFor();
    }
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
    mobile_390: true, timeline_graph_keyboard_and_evidence_navigation: true,
    production_api_redirected_to_offline_fixture: true, structured_intelligence_demo: true,
    dynamic_investigation_and_history_routes: true, browser_errors: 0, external_browser_requests: 0 };
  await fs.writeFile(path.join(out, "deployment-browser.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally {
  await Promise.all(contexts.map(c => c.close()));
  await browser.close();
}
