import { test, expect } from "@playwright/test";

test.describe("Multimodal Investigation Ingestion & Analysis Flow", () => {
  test("authenticates, creates multimodal investigation (text + url), runs analysis, and verifies RAG panel", async ({
    page,
  }) => {
    const analystEmail = `investigator_${Date.now()}@threatweave.test`;
    const password = "SecOpsPassword123!";

    // -------------------------------------------------------------
    // 1. Authenticate analyst
    // -------------------------------------------------------------
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /Register SOC Analyst/i })).toBeVisible();

    await page.locator("#register-email").fill(analystEmail);
    await page.locator("#register-password").fill(password);
    await page.locator("#register-confirm-password").fill(password);
    await page.locator("#register-submit-btn").click();
    await page.waitForURL("/", { timeout: 20_000 });

    // -------------------------------------------------------------
    // 2. Navigate to /investigations/new
    // -------------------------------------------------------------
    await page.goto("/investigations/new");
    await expect(
      page.getByRole("heading", { name: /New Multimodal Threat Investigation/i })
    ).toBeVisible({ timeout: 15_000 });

    // -------------------------------------------------------------
    // 3. Populate multimodal evidence (text + URL)
    // -------------------------------------------------------------
    const invTitle = `E2E Live Phishing Ingestion - ${Date.now()}`;
    await page.locator("#inv-title").fill(invTitle);

    await page.locator("#inv-text").fill(
      "URGENT: Your SBI net banking account has been temporarily restricted due to unauthorized login attempts. " +
      "Immediate Action Required: Verify your security credentials within 24 hours at http://192.168.1.100/sbi-verify/login.php."
    );

    await page.locator("#inv-url").fill("http://192.168.1.100/sbi-verify/login.php");

    // Submit the investigation form
    const createBtn = page.getByRole("button", { name: /Create Investigation/i });
    await createBtn.click();

    // -------------------------------------------------------------
    // 4. Confirm navigation to the investigation workspace
    // -------------------------------------------------------------
    await page.waitForURL(/\/investigations\/[a-f0-9-]+/, { timeout: 30_000 });
    expect(page.url()).toMatch(/\/investigations\/[a-f0-9-]+$/);

    // -------------------------------------------------------------
    // 5. Trigger swarm analysis
    // -------------------------------------------------------------
    const runAnalysisBtn = page.getByRole("button", { name: /Run Swarm Analysis/i });
    await expect(runAnalysisBtn).toBeVisible({ timeout: 15_000 });
    await runAnalysisBtn.click();

    // -------------------------------------------------------------
    // 6. Confirm the investigation reaches "completed" status
    // -------------------------------------------------------------
    const completedBadge = page.locator("header").getByText("completed", { exact: true });
    await expect(completedBadge).toBeVisible({ timeout: 90_000 });

    // -------------------------------------------------------------
    // 7. Verify AgentActivityStrip shows executed agents as completed
    // -------------------------------------------------------------
    const activityStrip = page.getByRole("region", { name: "Agent Activity Strip" });
    await expect(activityStrip).toBeVisible();

    // Text Specialist and URL Specialist were the ingested modalities
    const expectedAgents = ["Text Specialist", "URL Specialist"];
    for (const agentName of expectedAgents) {
      const agentCard = activityStrip.locator(".grid > div").filter({ hasText: agentName });
      await expect(agentCard).toBeVisible();
      await expect(agentCard).toContainText("Completed");
    }

    // -------------------------------------------------------------
    // 8. Confirm RAG citation panel renders correctly
    // -------------------------------------------------------------
    const ragSection = page.getByRole("region", { name: "External Advisory Citations" });
    await expect(ragSection).toBeVisible();

    await expect(
      ragSection.getByRole("heading", { name: /RAG-Grounded Threat Intelligence Citations/i })
    ).toBeVisible();

    // Verify it renders either verified citations or the honest empty state gracefully without crash
    const hasCitations = await ragSection.getByText(/Verified Grounding Matches/i).isVisible();
    const hasEmptyState = await ragSection.getByText(/No matching threat advisory found/i).isVisible();
    expect(hasCitations || hasEmptyState).toBe(true);
  });
});
