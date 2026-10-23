// Exercise the real client module in a VM; no browser, credentials or network.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";

const frontend = path.resolve(process.env.TEST_FRONTEND_DIR || "frontend");
const require = createRequire(path.join(frontend, "package.json"));
const ts = require("typescript");
const source = await fs.readFile(path.join(frontend, "lib/api.ts"), "utf8");
const code = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

async function scenario(status, token) {
  const stored = new Map(token ? [["websec_token", "synthetic-session"]] : []);
  const events = [];
  let sent;
  const result = { exports: {} };
  const context = {
    exports: result.exports,
    module: result,
    process: { env: { NEXT_PUBLIC_API_BASE_URL: "https://fixture.invalid" } },
    Headers,
    Event: class { constructor(type) { this.type = type; } },
    localStorage: {
      getItem: (key) => stored.get(key) || null,
      removeItem: (key) => stored.delete(key),
      setItem: (key, value) => stored.set(key, value),
    },
    window: {
      dispatchEvent: (event) => events.push(event.type),
      addEventListener: () => {},
      removeEventListener: () => {},
    },
    fetch: async (url, options) => {
      sent = { url, options };
      return {
        ok: status >= 200 && status < 300,
        status,
        json: async () => status === 200
          ? { public_registration_enabled: true }
          : { detail: status === 401 ? "Sessão expirada" : "Acesso recusado" },
      };
    },
  };
  vm.runInNewContext(code, context);
  return { api: result.exports, stored, events, sent: () => sent };
}

const expired = await scenario(401, true);
await assert.rejects(expired.api.request("/api/v1/investigations"), /Sessão expirada/);
assert.equal(expired.stored.has("websec_token"), false);
assert.deepEqual(expired.events, ["websec-auth-changed"]);

const nonmember = await scenario(403, true);
await assert.rejects(nonmember.api.request("/api/v1/investigations"), /Acesso recusado/);
assert.equal(nonmember.stored.has("websec_token"), true);
assert.deepEqual(nonmember.events, []);

const anonymous = await scenario(401, false);
await assert.rejects(anonymous.api.request("/api/v1/investigations"), /Sessão expirada/);
assert.deepEqual(anonymous.events, []);

const policy = await scenario(200, false);
const result = await policy.api.api.authConfiguration();
assert.equal(result.public_registration_enabled, true);
assert.equal(policy.sent().url, "https://fixture.invalid/api/v1/auth/configuration");
assert.equal(policy.sent().options.headers.has("Authorization"), false);
console.log(JSON.stringify({
  expired_session_cleared: true,
  auth_change_event: true,
  forbidden_membership_preserves_session: true,
  anonymous_response_does_not_emit_logout: true,
  public_policy_endpoint: true,
  external_requests: 0,
}));
