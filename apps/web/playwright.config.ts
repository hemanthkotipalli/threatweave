import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for ThreatWeave web application.
 * Configured for Phase C QA automation.
 */
export default defineConfig({
  testDir: "./e2e",
  /* Maximum time one test can run for. Extended to 120s for live multimodal swarm pipeline */
  timeout: 120_000,
  expect: {
    timeout: 30_000,
  },
  /* Run tests in files in series to prevent concurrency contention on SQLite/Groq */
  fullyParallel: false,
  workers: 1,
  /* Reporter to use */
  reporter: [["list"], ["html", { open: "never" }]],
  /* Shared settings for all the projects below */
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  /* Run local dev server if not already running */
  webServer: [
    {
      command: "..\\api\\venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: "../api",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev",
      cwd: ".",
      url: "http://localhost:3000",
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
});
