// Test actual frontend data transformations, with no UI, keys or network.
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";

const frontend = path.resolve(process.env.TEST_FRONTEND_DIR || "frontend");
const require = createRequire(path.join(frontend, "package.json"));
const ts = require("typescript");
const source = await fs.readFile(path.join(frontend, "lib/evidence-view.ts"), "utf8");
const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const result = { exports: {} };
vm.runInNewContext(code, { exports: result.exports, module: result });
const { relationOf, filterEvidence, timelineEvidence, dateTimestamp, evidenceGraph, emptyFilters } = result.exports;
const entry = (id, overrides = {}) => ({ id, provider: "osint", category: "public_reference", title: "Exposição alegada", description: "Referência de teste", source_url: "https://source.invalid/report", confirmation: "allegation", published_at: "2026-10-21", event_at: null, observed_at: "2026-10-23T00:00:00Z", meta: {}, ...overrides });
const candidate = entry("candidate", { provider: "kev", category: "kev_candidate", confirmation: "known_exploited", meta: { relevance: "product_candidate_version_unconfirmed", catalog_added_at: "2026-10-22" } });
const general = entry("general", { provider: "kev", category: "kev_general", confirmation: "known_exploited", meta: { relevance: "general_alert_not_associated_with_target" } });
const homonym = entry("homonym", { meta: { matched_by: "organization_name", relevance: "candidate_match" } });
assert.equal(relationOf(candidate), "product");
assert.equal(relationOf(general), "general");
assert.equal(relationOf(homonym), "review");
assert.equal(relationOf(entry("review", { meta: { relevance: "needs_review" } })), "review");
assert.equal(relationOf(entry("signal", { category: "message_signal" })), "signal");

const input = [entry("unknown"), candidate, general, homonym, entry("known", { event_at: "2026-10-20" }), entry("invalid", { event_at: "2026-02-31" })];
const originalOrder = input.map((e) => e.id).join(",");
const incident = timelineEvidence(input, "event_at");
assert.equal(incident.dated.length, 1);
assert.equal(incident.dated[0].entry.id, "known");
assert.equal(incident.undated.length, 5, "publication, observation and catalog dates must never fill an unknown incident date");
assert.equal(dateTimestamp("2026-02-31"), null);
assert.equal(dateTimestamp("2025-02-29"), null);
assert.notEqual(dateTimestamp("2024-02-29"), null);
assert.equal(dateTimestamp("nonsense"), null);
assert.equal(dateTimestamp(null), null);
assert.equal(timelineEvidence([entry("old", { published_at: "2020-01-01" }), entry("new")], "published_at").dated[0].entry.id, "new");

assert.equal(filterEvidence(input, { ...emptyFilters, query: "EXPOSICAO" }).length, input.length, "search must ignore accents and case");
assert.equal(filterEvidence(input, { ...emptyFilters, provider: "kev", relation: "general" }).length, 1);
assert.equal(filterEvidence(input, { ...emptyFilters, query: "no-match" }).length, 0);
assert.equal(filterEvidence(input, { ...emptyFilters, relation: "review" })[0].id, "homonym");
assert.equal(filterEvidence([], emptyFilters).length, 0);

const graph = evidenceGraph([...input, input[0]], 4);
assert.equal(graph.entries.length, 4);
assert.equal(graph.omitted, 2, "duplicate IDs must not inflate omitted count");
assert.equal(graph.edges.length, 4);
assert.equal(graph.edges.find((edge) => edge.evidenceId === "homonym").relation, "review");
assert.equal(graph.edges.find((edge) => edge.evidenceId === "general").relation, "general");
for (const edge of graph.edges) {
  assert.equal(edge.kind, "collected_by");
  const evidence = input.find((e) => e.id === edge.evidenceId);
  assert.ok(evidence, "every edge must point to actual evidence");
  assert.equal(edge.provider, evidence.provider);
}
assert.equal(evidenceGraph(input, -1).entries.length, 0);
assert.equal(evidenceGraph(Array.from({ length: 90 }, (_, i) => entry(String(i))), 999).entries.length, 48);
assert.equal(input.map((e) => e.id).join(","), originalOrder, "sorting and filtering must not mutate API data or citation numbering");
console.log(JSON.stringify({ assertions: "passed", safeguards: ["no_invented_incident_dates", "homonyms_remain_unverified", "KEV_is_not_target_exploitation", "collection_edges_with_provenance", "stable_citations", "bounded_graph", "accent_insensitive_filters"], external_requests: 0 }));
