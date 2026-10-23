// Local offline API only; all users, passwords and links are synthetic.
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
const require = createRequire(path.resolve(process.env.TEST_FRONTEND_DIR, "package.json"));
const { chromium } = require("playwright");
const backend = process.env.TEST_BACKEND_DIR;
if (!backend || !process.env.DATABASE_URL?.includes("@127.0.0.1:") || !process.env.DATABASE_URL?.includes("/websecai_test_")) throw new Error("Local isolated PostgreSQL required");
function issue(email, purpose, username) {
  const result = spawnSync(process.env.TEST_BACKEND_PYTHON, ["-c", [
    "import dotenv; dotenv.load_dotenv=lambda *a,**k: False",
    "from app.db.session import SessionLocal",
    "from app.models import scan, finding, investigation",
    "from app.services.account_access import issue_account_link",
    "import sys",
    "with SessionLocal() as db: print(issue_account_link(db, sys.argv[1], sys.argv[2], sys.argv[3]))",
  ].join("\n"), email, purpose, username], { cwd: backend, env: process.env, encoding: "utf8" });
  if (result.status !== 0) throw new Error("Synthetic link generation failed");
  const value = result.stdout.trim();
  assert.match(value, /^[A-Za-z0-9_-]{43}$/);
  return value;
}
const browser = await chromium.launch({ channel: "chrome", headless: true });
const errors = [], outside = [];
const out = process.env.TEST_OUTPUT_DIR;
const base = "http://127.0.0.1:3000";
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.route("**/*", async route => {
    const url = new URL(route.request().url());
    if (url.hostname === "websecaiapi.onrender.com") {
      const response = await route.fetch({ url: "http://127.0.0.1:8000" + url.pathname });
      return route.fulfill({ response });
    }
    if (!["127.0.0.1", "localhost"].includes(url.hostname)) { outside.push(url.hostname); return route.abort(); }
    return route.continue();
  });
  const page = await context.newPage();
  page.on("pageerror", error => errors.push(error.message));
  const name = "invite_" + randomBytes(5).toString("hex");
  const email = name + "@example.com";
  const first = randomBytes(24).toString("base64url");
  const second = randomBytes(24).toString("base64url");
  const third = randomBytes(24).toString("base64url");
  const invitation = issue(email, "invite", name);
  await page.goto(base + "/reset-password#token=" + invitation);
  await page.getByLabel("Nova palavra-passe", { exact: true }).waitFor();
  assert.equal(new URL(page.url()).hash, "");
  assert.equal(await page.locator('meta[name="referrer"]').getAttribute("content"), "no-referrer");
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await page.screenshot({ path: path.join(out, "password-invite-form-mobile.png"), fullPage: true });
  await page.getByLabel("Nova palavra-passe", { exact: true }).fill(first);
  await page.getByLabel("Repetir nova palavra-passe", { exact: true }).fill(first);
  await page.getByRole("button", { name: "Definir a minha palavra-passe", exact: true }).click();
  await page.getByText("A tua palavra-passe foi definida.", { exact: false }).waitFor();
  assert.equal(await page.evaluate(() => localStorage.getItem("websec_token")), null);
  await page.getByRole("link", { name: "Ir para o login", exact: true }).click();
  async function login(password) {
    await page.getByLabel("Username ou email", { exact: true }).fill(email);
    await page.getByLabel("Palavra-passe", { exact: true }).fill(password);
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await page.waitForURL("**/investigations");
  }
  await login(first);
  const previousToken = await page.evaluate(() => localStorage.getItem("websec_token"));
  await page.getByRole("link", { name: "Perfil", exact: true }).click();
  await page.getByLabel("Palavra-passe atual", { exact: true }).fill(first);
  await page.getByLabel("Nova palavra-passe", { exact: true }).fill(second);
  await page.getByLabel("Repetir nova palavra-passe", { exact: true }).fill(second);
  await page.getByRole("button", { name: "Guardar nova palavra-passe", exact: true }).click();
  await page.getByText("A palavra-passe foi alterada", { exact: false }).waitFor();
  assert.equal((await context.request.get("http://127.0.0.1:8000/api/v1/users/me", { headers: { Authorization: "Bearer " + previousToken } })).status(), 401);
  await page.getByRole("button", { name: "Voltar a entrar", exact: true }).click();
  await page.waitForURL("**/login");
  await login(second);
  const reset = issue(email, "reset", "");
  await page.goto(base + "/reset-password#token=" + reset);
  await page.getByLabel("Nova palavra-passe", { exact: true }).fill(third);
  await page.getByLabel("Repetir nova palavra-passe", { exact: true }).fill(third);
  await page.getByRole("button", { name: "Definir a minha palavra-passe", exact: true }).click();
  await page.getByText("A tua palavra-passe foi definida.", { exact: false }).waitFor();
  await page.screenshot({ path: path.join(out, "password-reset-success-mobile.png"), fullPage: true });
  await page.goto(base + "/reset-password#token=" + reset);
  await page.getByLabel("Nova palavra-passe", { exact: true }).fill(first);
  await page.getByLabel("Repetir nova palavra-passe", { exact: true }).fill(first);
  await page.getByRole("button", { name: "Definir a minha palavra-passe", exact: true }).click();
  await page.getByRole("alert").filter({ hasText: "Link inválido, expirado ou já utilizado" }).waitFor();
  await page.goto(base + "/login");
  await login(third);
  assert.deepEqual(errors, []);
  assert.deepEqual(outside, []);
  const result = { checked_at: new Date().toISOString(), runtime: process.env.TEST_RUNTIME,
    invite: true, own_change: true, private_reset: true, replay_rejected: true,
    old_session_revoked: true, token_removed_from_address: true, mobile_width: 390,
    provider_calls: 0, outside_requests: 0, javascript_errors: 0 };
  await fs.writeFile(path.join(out, "account-access-browser.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally { await browser.close(); }
