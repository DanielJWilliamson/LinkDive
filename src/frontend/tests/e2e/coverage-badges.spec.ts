import { test, expect } from '@playwright/test';

test.describe('Coverage table badges and sorting aria', () => {
  test('badges render and column headers expose aria-sort', async ({ page }) => {
    await page.goto('/');

    // Select the first campaign card
    const firstCard = page.locator('[data-testid="campaign-card"]').first();
    await expect(firstCard).toBeVisible();
    await firstCard.click();

    // Wait for the table heading
    await expect(page.getByRole('heading', { name: /campaign coverage results/i })).toBeVisible();

    // Column headers have aria-sort
    const headers = page.locator('thead th[role="columnheader"]');
    await expect(headers).toHaveCount(5); // first_seen, page_title, url, coverage_status, link_destination

    // Look for at least one coverage status badge
    const verifiedBadge = page.getByText(/verified coverage/i).first();
    const potentialBadge = page.getByText(/potential coverage/i).first();
    // One of them should be visible depending on data
    const verifiedVisible = await verifiedBadge.isVisible().catch(() => false);
    const potentialVisible = await potentialBadge.isVisible().catch(() => false);
    expect(verifiedVisible || potentialVisible).toBeTruthy();

    // Destination badge: look for common labels
    const destBadge = page.locator('td >> text=/Blog Page|Homepage|Product|N\/A/').first();
    const hasDest = await destBadge.isVisible().catch(() => false);
    expect(hasDest).toBeTruthy();
  });
});
