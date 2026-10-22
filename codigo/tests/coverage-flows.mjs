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
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
const errors = [], external = [];
page.on("pageerror", e => errors.push(e.message));
page.on("request", r => { if (!["127.0.0.1", "localhost"].includes(new URL(r.url()).hostname)) external.push(r.url()); });
const id = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa";
const fixture = {
  id, target: "https://target.example/", domain: "target.example", kind: "domain", organization: "Entidade fictícia",
  status: "partial", is_demo: true, created_at: "2026-10-22T00:00:00Z", finished_at: "2026-10-22T00:00:01Z",
  technical: null, message_analysis: null, runs: [{ provider: "osint", status: "no_results", message: "Resposta controlada sem correspondências", results_count: 0, observed_at: "2026-10-22T00:00:00Z" }],
  evidence: [], previous_evidence: [], reports: [], retryable_providers: [],
  coverage_summary: { origin: "local_rules", has_target_evidence: false, target_evidence_count: 0, notes: ["Não há evidências atuais diretamente associadas ao alvo nesta recolha."] },
  incident_grouping: { origin: "local_rules", groups: [], ungrouped_evidence_ids: [], limitation: "Datas de publicação não são datas de incidente." },
};
try {
  const user = "flows_" + randomBytes(5).toString("hex");
  await page.goto("http://127.0.0.1:3000/register", { waitUntil: "networkidle" });
  await page.getByLabel("Username", { exact: true }).fill(user);
  await page.getByLabel("Email", { exact: true }).fill(user + "@example.com");
  await page.getByLabel("Palavra-passe", { exact: true }).fill(randomBytes(20).toString("base64url"));
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await page.waitForURL("**/investigations");
  await page.route("**/api/v1/investigations/" + id, route => route.fulfill({ json: fixture }));
  await page.route("**/api/v1/investigations/" + id + "/comparison", route => route.fulfill({ json: { previous_id: null, added: [], removed: [], message: "Resposta controlada" } }));
  await page.goto("http://127.0.0.1:3000/investigations/" + id, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "O que a cobertura permite concluir", exact: true }).waitFor();
  assert.match(await page.locator(".investigationDetail").innerText(), /regras locais/);
  assert.equal(await page.locator(".summaryText").count(), 0);
  assert.equal(await page.locator("#question").count(), 0);
  await page.locator('section[aria-labelledby="coverage-notes-heading"]').screenshot({ path: path.join(out, "coverage-controlled-desktop.png") });
  const evidence = ["one", "two"].map((eid, index) => ({ id: eid, provider: "osint", category: "incident_report", title: "Ransomware fictício " + index, description: "Fixture de interface, não descreve um incidente real.", source_url: "https://news.example/" + eid, confirmation: "reported", published_at: "2026-01-01", event_at: "2025-12-20", observed_at: "2026-10-22T00:00:00Z", meta: {} }));
  fixture.evidence = evidence;
  fixture.coverage_summary = { ...fixture.coverage_summary, has_target_evidence: true, target_evidence_count: 2 };
  fixture.incident_grouping.groups = [{ id: "candidate", reason: "shared_event_date_and_type", status: "candidate_requires_review", event_at: "2025-12-20", kind: "ransomware", evidence_ids: ["one", "two"], source_urls: [], note: "Podem descrever incidentes diferentes; requer revisão." }];
  await page.reload({ waitUntil: "networkidle" });
  await page.getByText("2 referências candidatas", { exact: false }).click();
  assert.match(await page.locator("details[open]").innerText(), /requer revisão/);
  await page.locator('section[aria-labelledby="groups-heading"]').screenshot({ path: path.join(out, "groups-controlled-desktop.png") });
  await page.locator("details[open] a").first().click();
  assert.match(page.url(), /#evidence-one$/);
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
  await page.locator('section[aria-labelledby="groups-heading"]').screenshot({ path: path.join(out, "groups-controlled-mobile.png") });
  assert.deepEqual(errors, []); assert.deepEqual(external, []);
  const result = { checked_at: new Date().toISOString(), mode: "controlled_browser_fixtures", no_llm_summary_in_empty_case: true, coverage_separate_from_ai: true, candidate_group_links: true, mobile_390_no_overflow: true, page_errors: 0, external_requests: 0 };
  await fs.writeFile(path.join(out, "coverage-flow-results.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally { await context.close(); await browser.close(); }
