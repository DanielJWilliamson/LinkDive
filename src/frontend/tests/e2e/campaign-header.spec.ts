import { test, expect } from '@playwright/test';

test.describe('Campaign header details', () => {
  test('shows labeled fields and values when a campaign is selected', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('[data-testid="campaign-card"]').first();
    await expect(firstCard).toBeVisible();
    await firstCard.click();

    await expect(page.getByRole('heading', { name: /campaign view/i })).toBeVisible();

    // Labels
    const labels = ['Client Name', 'Campaign Name', 'Start Date', 'Monitoring Status', 'Client Domain'];
    for (const label of labels) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }

    // Values exist (non-empty text in the corresponding test ids)
    await expect(page.getByTestId('campaign-client-name')).toHaveText(/\S/);
    await expect(page.getByTestId('campaign-name')).toHaveText(/\S/);
    await expect(page.getByTestId('campaign-start-date')).toHaveText(/\S|—/);
    await expect(page.getByTestId('campaign-monitoring-status')).toHaveText(/\S/);
    await expect(page.getByTestId('campaign-client-domain')).toHaveText(/\S/);

    // Status pill visible
    await expect(page.getByTestId('campaign-status-pill')).toBeVisible();
  });
});
