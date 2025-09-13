import { test, expect } from '@playwright/test';

test.describe('Homepage Cards/Table toggle', () => {
  test('toggle to table and verify default Start Date sort (desc)', async ({ page }) => {
    await page.goto('/');

    // Switch to table view
    await page.getByTestId('view-toggle-table').click();
    await expect(page.getByTestId('campaigns-table')).toBeVisible();

    // Grab first two Start Date cells if available
    const rows = page.locator('[data-testid="campaigns-table"] tbody tr');
    const count = await rows.count();
    test.skip(count < 2, 'Need at least 2 campaigns to verify sorting');

    const firstDateText = (await rows.nth(0).locator('td').nth(2).innerText()).trim();
    const secondDateText = (await rows.nth(1).locator('td').nth(2).innerText()).trim();

    const parse = (t: string) => new Date(t).getTime();
    expect(parse(firstDateText)).toBeGreaterThanOrEqual(parse(secondDateText));
  });
});
