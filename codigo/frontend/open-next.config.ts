import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// No extra storage binding: this interface retrieves private data from FastAPI.
export default defineCloudflareConfig();
