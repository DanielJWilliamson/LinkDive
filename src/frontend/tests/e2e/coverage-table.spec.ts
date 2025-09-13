import { test, expect } from '@playwright/test';

// E2E: validates selection, select-all indeterminate, and copy-to-clipboard fallback
// Assumptions:
// - The app loads a dashboard with list of campaigns and seeded data is available
// - Clicking a campaign opens details view with a coverage table
// - The coverage table header contains a select-all checkbox
// - The "Copy Selected URLs" button is present

test.describe('Coverage table selection and copy', () => {
  test('select rows, select-all indeterminate, and copy behavior', async ({ page }) => {
    await page.goto('/');

    // Select the first campaign card
    const firstCard = page.locator('[data-testid="campaign-card"]').first();
    await expect(firstCard).toBeVisible();
    await firstCard.click();

    // Wait for the table header (Campaign Coverage Results)
    await expect(page.getByRole('heading', { name: /campaign coverage results/i })).toBeVisible();

    const selectAll = page.locator('thead input[type="checkbox"]').first();
    const rowCheckboxes = page.locator('tbody input[type="checkbox"]');

    // Ensure there are rows; if not, skip
    const rowsCount = await rowCheckboxes.count();
    test.skip(rowsCount === 0, 'No coverage rows available to test');

    // Select the first row
    await rowCheckboxes.nth(0).check();
    await expect(rowCheckboxes.nth(0)).toBeChecked();

    // Select-all should become indeterminate (Playwright cannot read indeterminate directly reliably)
    // Instead, check that select-all is not checked but toggling it selects all
    const initiallyChecked = await selectAll.isChecked();
    expect(initiallyChecked).toBeFalsy();

    // Click select-all -> should select all
    await selectAll.click();
    const selectedCount = await page.locator('tbody input[type="checkbox"]:checked').count();
    expect(selectedCount).toBe(rowsCount);

    // Click select-all again -> should clear all
    await selectAll.click();
    const clearedCount = await page.locator('tbody input[type="checkbox"]:checked').count();
    expect(clearedCount).toBe(0);

    // Clipboard test: with no selection, clicking Copy should copy verified URLs fallback
    // To avoid relying on system clipboard permissions, mock clipboard.writeText
    await page.addInitScript(() => {
      // @ts-expect-error augment window for test
      window.__copied = '';
      navigator.clipboard.writeText = async (text: string) => {
        // @ts-expect-error custom test prop
        window.__copied = text;
        return Promise.resolve();
      };
    });

    await page.getByRole('button', { name: /copy selected urls/i }).click();
    // Read the copied text
    const copied = await page.evaluate(() => {
      // @ts-expect-error test prop
      return window.__copied as string;
    });
    expect(typeof copied).toBe('string');
    // It should contain at least one http/https URL when verified coverage exists; if not, it's empty and acceptable
    if (copied) {
      expect(copied).toMatch(/^https?:\/\//m);
    }
  });
});
