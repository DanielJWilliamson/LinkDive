import { test, expect } from '@playwright/test';

// Verifies aria-sort and keyboard sorting behavior on the homepage CampaignTable
// Assumes there are at least two campaigns with different Start Dates

test.describe('Homepage CampaignTable accessibility', () => {
  test('aria-sort reflects default and toggles via keyboard', async ({ page }) => {
    await page.goto('/');

    // Switch to table view
    await page.getByTestId('view-toggle-table').click();
    await expect(page.getByTestId('campaigns-table')).toBeVisible();

    const headerStartDate = page.getByTestId('header-start-date');

    // Default should be Start Date sorted desc
    await expect(headerStartDate).toHaveAttribute('aria-sort', 'descending');

    // Press Enter to toggle to ascending
    await headerStartDate.focus();
    await page.keyboard.press('Enter');
    await expect(headerStartDate).toHaveAttribute('aria-sort', 'ascending');

    // Press Space to toggle back to descending
    await page.keyboard.press(' ');
    await expect(headerStartDate).toHaveAttribute('aria-sort', 'descending');
  });
});
