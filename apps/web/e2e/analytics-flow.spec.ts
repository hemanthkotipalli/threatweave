import { test, expect } from "@playwright/test";

test.describe("Interactive Analytics Dashboard Flow", () => {
  test("navigates to analytics studio, verifies priority charts, tabs, and benchmark metrics", async ({
    page,
  }) => {
    // 1. Navigate directly to /analytics
    await page.goto("/analytics");

    // 2. Verify page title and header
    await expect(
      page.getByRole("heading", { name: /Threat Intelligence & Analytics Studio/i })
    ).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("LIVE DASHBOARD")).toBeVisible();
    await expect(page.getByText(/Operational sample window/i)).toBeVisible();

    // 3. Verify Priority Chart 1: Threat Severity Distribution
    await expect(
      page.getByRole("heading", { name: /Threat Severity Distribution/i })
    ).toBeVisible();
    await expect(page.getByText("Threat Ratio", { exact: true })).toBeVisible();

    // 4. Verify Priority Chart 2: Modality-Wise Threat Breakdown
    await expect(
      page.getByRole("heading", { name: /Modality-Wise Threat Breakdown/i })
    ).toBeVisible();
    await expect(page.getByText("Text / SMS", { exact: false })).toBeVisible();
    await expect(page.getByText("URL Sandbox", { exact: false })).toBeVisible();
    await expect(page.getByText("QR Code").first()).toBeVisible();

    // 5. Verify Priority Chart 3: Threat Activity Timeline
    await expect(
      page.getByRole("heading", { name: /Threat Activity Timeline/i })
    ).toBeVisible();

    // 6. Verify Additional Analytics: Specialist Agent Execution Performance & Correlation Heatmap
    await expect(
      page.getByRole("heading", { name: /Specialist Agent Execution Performance/i })
    ).toBeVisible();
    await expect(page.getByText(/Benchmark Ref:/i).first()).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /Cross-Modal Threat Correlation Matrix/i })
    ).toBeVisible();

    // 7. Test Tab Switch to 94-Sample Evaluation Benchmark
    const benchmarkTab = page.getByRole("button", { name: /94-Sample Evaluation Benchmark/i });
    await benchmarkTab.click();

    await expect(
      page.getByRole("heading", { name: /94-Sample Empirical Benchmark & Research Evaluation/i })
    ).toBeVisible();
    await expect(page.getByText("URL Specialist")).toBeVisible();
    await expect(page.getByText("QR Code Specialist")).toBeVisible();
    await expect(page.getByText("Text & SMS Specialist")).toBeVisible();
    await expect(page.getByText("Image & OCR Specialist")).toBeVisible();
    await expect(page.getByText("Voice & Speech Specialist")).toBeVisible();

    // Toggle between Production LLM and Offline Heuristic mode
    const offlineBtn = page.getByRole("button", { name: /Offline Heuristic Fallback/i });
    await offlineBtn.click();
    await expect(page.getByText(/100% local deterministic heuristics/i)).toBeVisible();

    // 8. Test Navigation from Home Page
    await page.goto("/");
    const analyticsNavBtn = page.getByRole("button", { name: /Analytics/i }).first();
    await expect(analyticsNavBtn).toBeVisible();
    await analyticsNavBtn.click();
    await expect(page).toHaveURL(/.*\/analytics/);
  });

  test("renders responsive layouts cleanly across mobile (375px), tablet (768px), and desktop (1440px)", async ({
    page,
  }) => {
    const viewports = [
      { width: 375, height: 667, name: "mobile" },
      { width: 768, height: 1024, name: "tablet" },
      { width: 1440, height: 900, name: "desktop" },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/analytics");

      // Verify header and sample window indicator
      await expect(
        page.getByRole("heading", { name: /Threat Intelligence & Analytics Studio/i })
      ).toBeVisible();
      await expect(page.getByText(/Operational sample window/i)).toBeVisible();

      // Verify charts are visible in viewport
      await expect(
        page.getByRole("heading", { name: /Threat Severity Distribution/i })
      ).toBeVisible();
      await expect(
        page.getByRole("heading", { name: /Modality-Wise Threat Breakdown/i })
      ).toBeVisible();
      await expect(
        page.getByRole("heading", { name: /Specialist Agent Execution Performance/i })
      ).toBeVisible();
      await expect(page.getByText(/Benchmark Ref:/i).first()).toBeVisible();
    }
  });
});
