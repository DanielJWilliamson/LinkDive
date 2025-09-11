import { test, expect } from '@playwright/test';

// Basic E2E covering Phase A/B: create campaign, trigger analyze (backend auto-analysis), view list

test.describe('Campaign lifecycle', () => {
  test('create campaign and list appears', async ({ page }) => {
    await page.goto('/');
    // Open create campaign modal (assumes button text)
    await page.getByRole('button', { name: /create campaign/i }).click();

    // Step 1 inputs
    await page.getByPlaceholder('e.g., Acme Corporation').fill('Acme Corp');
    await page.getByPlaceholder('e.g., Q1 2025 Product Launch').fill('Launch Alpha');
    await page.getByPlaceholder('example.com').fill('acme.com');
    await page.getByRole('button', { name: /next/i }).click();

    // Step 2 add a SERP keyword
    const serpInput = page.getByPlaceholder('e.g., best project management software');
    await serpInput.fill('acme software');
    await page.getByRole('button', { name: /next/i }).click();

    // Step 3 summary -> create
    await page.getByRole('button', { name: /create campaign/i }).click();

    // Expect modal to close and campaign to appear in list (contains Launch Alpha)
    await expect(page.getByText('Launch Alpha')).toBeVisible({ timeout: 10000 });
  });
});
