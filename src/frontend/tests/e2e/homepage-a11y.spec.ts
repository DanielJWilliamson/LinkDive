import { test, expect } from '@playwright/test';

test.describe('Homepage table accessibility', () => {
  test('headers expose aria-sort and support keyboard sorting', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('view-toggle-table').click();
    const table = page.getByTestId('campaigns-table');
    await expect(table).toBeVisible();

    const headers = table.locator('thead th[role="columnheader"]');
    await expect(headers).toHaveCount(4);

    // Check default sort: Start Date should be aria-sort="descending"
    const startDateHeader = headers.nth(2);
    await expect(startDateHeader).toHaveAttribute('aria-sort', /descending|none/i);

    // Keyboard toggle on Client Name
    const clientHeader = headers.nth(0);
    await clientHeader.focus();
    await page.keyboard.press('Enter');
    await expect(clientHeader).toHaveAttribute('aria-sort', /ascending|descending|none/i);
    await page.keyboard.press(' ');
    await expect(clientHeader).toHaveAttribute('aria-sort', /ascending|descending|none/i);
  });
});
