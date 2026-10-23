import { spawnSync } from "node:child_process";
import path from "node:path";
const endpoint = process.env.NEXT_PUBLIC_API_BASE_URL;
let url;
try { url = new URL(endpoint); } catch { throw new Error("Define NEXT_PUBLIC_API_BASE_URL no ambiente de build."); }
const local = process.env.WEBSECAI_LOCAL_PREVIEW === "1" && ["localhost", "127.0.0.1"].includes(url.hostname);
if ((!local && (url.protocol !== "https:" || ["localhost", "127.0.0.1"].includes(url.hostname))) || url.username || url.password || url.search || url.hash) {
  throw new Error("A API publicada exige URL HTTPS sem credenciais; localhost só em preview explícito.");
}
const cli = path.resolve("node_modules/@opennextjs/cloudflare/dist/cli/index.js");
const result = spawnSync(process.execPath, [cli, "build", ...process.argv.slice(2)], {
  stdio: "inherit",
  // Avoid concurrent directory-copy failures observed with standalone builds on Windows.
  env: { ...process.env, UV_THREADPOOL_SIZE: process.env.UV_THREADPOOL_SIZE || "1" },
});
process.exit(result.status ?? 1);
