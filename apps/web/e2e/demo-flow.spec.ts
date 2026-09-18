import { test, expect } from "@playwright/test";

test.describe("Demo Mode Flow", () => {
  test("loads all 6 scenarios, runs cross_modal scenario, and verifies investigation workspace", async ({
    page,
  }) => {
    // 1. Navigate to /demo
    await page.goto("/demo");
    await expect(
      page.getByRole("heading", { name: /ThreatWeave Live Demonstration Lab/i })
    ).toBeVisible({ timeout: 15_000 });

    // 2. Confirm all 6 scenario cards render with their titles and descriptions
    const expectedScenarios = [
      {
        title: "Urgent Banking Credentials Lure",
        description: "Realistic banking phishing message utilizing coercive urgency language",
      },
      {
        title: "Typosquatted Banking Phishing Portal",
        description: "A deceptive lookalike domain hosted on a suspicious free TLD",
      },
      {
        title: "Mismatched Electricity Bill UPI QR",
        description: "A deceptive UPI QR code deep-link",
      },
      {
        title: "Fake Payment Confirmation Screenshot",
        description: "A forged instant payment confirmation graphic",
      },
      {
        title: "Automated Bank Compromise Vishing Call",
        description: "An automated telephone vishing audio script",
      },
      {
        title: "Coordinated Multi-Channel KYC Phishing Campaign",
        description: "A multi-channel banking attack combining an SMS security lure",
      },
    ];

    for (const scenario of expectedScenarios) {
      const heading = page.getByRole("heading", { name: scenario.title, exact: true });
      await expect(heading).toBeVisible({ timeout: 15_000 });
      await expect(page.getByText(scenario.description, { exact: false })).toBeVisible();
    }

    // 3. Locate the cross_modal scenario card specifically ("Thesis Proof")
    const crossModalTitle = page.getByRole("heading", {
      name: "Coordinated Multi-Channel KYC Phishing Campaign",
      exact: true,
    });
    const crossModalCard = page.locator("div").filter({ has: crossModalTitle }).filter({
      has: page.getByRole("button", { name: /Run Scenario/i }),
    }).last();

    await expect(crossModalCard).toBeVisible();

    // Click "Run Scenario"
    const runBtn = crossModalCard.getByRole("button", { name: /Run Scenario/i });
    await runBtn.click();

    // 4. Wait for and confirm navigation to the resulting investigation workspace
    // (Live swarm execution across 3 modalities with OCR & LLM can take 30-70s)
    await page.waitForURL(/\/investigations\/[a-f0-9-]+/, { timeout: 120_000 });
    expect(page.url()).toMatch(/\/investigations\/[a-f0-9-]+$/);

    // 5. Confirm status badge is "completed"
    const statusBadge = page.locator("header").getByText("completed", { exact: true });
    await expect(statusBadge).toBeVisible({ timeout: 30_000 });

    // 6. Confirm AgentActivityStrip shows expected agents as completed
    const activityStrip = page.getByRole("region", { name: "Agent Activity Strip" });
    await expect(activityStrip).toBeVisible();

    // The cross_modal scenario includes text, url, and image modalities
    const expectedAgents = ["Text Specialist", "URL Specialist", "Image Specialist"];
    for (const agentName of expectedAgents) {
      const agentCard = activityStrip.locator(".grid > div").filter({ hasText: agentName });
      await expect(agentCard).toBeVisible();
      await expect(agentCard).toContainText("Completed");
    }

    // 7. Confirm RiskGauge/score renders with a non-null value
    const riskSection = page.getByRole("region", { name: "Risk Scoring Assessment" });
    await expect(riskSection).toBeVisible();
    await expect(riskSection.getByText(/Resulting Score:\s*\d+\.\d+/i)).toBeVisible();

    // 8. Confirm RiskBreakdownPanel shows all 4 deterministic components
    const breakdownComponents = [
      "Base Finding Risk",
      "Cross-Modal Corroboration",
      "RAG Intel Grounding",
      "Contradiction Penalty",
    ];
    for (const comp of breakdownComponents) {
      await expect(riskSection.getByText(comp, { exact: true })).toBeVisible();
    }

    // 9. Confirm at least one EvidenceCard renders with real finding content
    const findingsSection = page.getByRole("region", { name: "Agent Findings" });
    await expect(findingsSection).toBeVisible();

    const firstFindingParagraph = findingsSection.locator("p.text-sm").first();
    await expect(firstFindingParagraph).toBeVisible({ timeout: 15_000 });
    const findingContent = await firstFindingParagraph.textContent();
    expect(findingContent).toBeTruthy();
    expect(findingContent!.trim().length).toBeGreaterThan(15);
  });
});
