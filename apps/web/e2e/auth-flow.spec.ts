import { test, expect } from "@playwright/test";

test.describe("Authentication Flow & Route Protection", () => {
  test("completes registration, login, logout, and verifies route guard on /investigations/new", async ({
    page,
  }) => {
    const uniqueEmail = `analyst_${Date.now()}@threatweave.test`;
    const password = "SecOpsPassword123!";

    // -------------------------------------------------------------
    // 1. Unauthenticated Check: /investigations/new redirects to /login
    // -------------------------------------------------------------
    await page.goto("/investigations/new");
    await page.waitForURL(/\/login/, { timeout: 15_000 });
    expect(page.url()).toContain("/login");
    await expect(page.getByRole("heading", { name: /ThreatWeave SOC/i })).toBeVisible();

    // -------------------------------------------------------------
    // 2. Register a new test user through the UI
    // -------------------------------------------------------------
    await page.goto("/register");
    await expect(page.getByRole("heading", { name: /Register SOC Analyst/i })).toBeVisible();

    await page.locator("#register-email").fill(uniqueEmail);
    await page.locator("#register-password").fill(password);
    await page.locator("#register-confirm-password").fill(password);

    // Submit registration
    await page.locator("#register-submit-btn").click();

    // Confirm redirect and authenticated state change on dashboard
    await page.waitForURL("/", { timeout: 20_000 });
    await expect(page.getByRole("button", { name: /Sign Out/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(uniqueEmail)).toBeVisible();

    // -------------------------------------------------------------
    // 3. Log out
    // -------------------------------------------------------------
    const signOutBtn = page.getByRole("button", { name: /Sign Out/i });
    await signOutBtn.click();

    // Confirm redirect to /login upon logout
    await page.waitForURL(/\/login/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: /ThreatWeave SOC/i })).toBeVisible();

    // Confirm visiting dashboard shows unauthenticated state (Sign In & Register buttons)
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Sign In/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: /Register/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Sign Out/i })).not.toBeVisible();

    // -------------------------------------------------------------
    // 4. Log back in with the same credentials
    // -------------------------------------------------------------
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: /ThreatWeave SOC/i })).toBeVisible();

    await page.locator("#login-email").fill(uniqueEmail);
    await page.locator("#login-password").fill(password);
    await page.locator("#login-submit-btn").click();

    // Confirm redirect to dashboard and authenticated state
    await page.waitForURL("/", { timeout: 20_000 });
    await expect(page.getByRole("button", { name: /Sign Out/i })).toBeVisible({ timeout: 10_000 });

    // -------------------------------------------------------------
    // 5. Authenticated Check: /investigations/new is reachable
    // -------------------------------------------------------------
    await page.goto("/investigations/new");
    await expect(page.getByRole("heading", { name: /New Multimodal Threat Investigation/i })).toBeVisible({
      timeout: 15_000,
    });
    expect(page.url()).toContain("/investigations/new");
  });
});
