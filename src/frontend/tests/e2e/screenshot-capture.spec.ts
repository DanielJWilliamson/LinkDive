import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// This spec captures up-to-date UI screenshots into docs/images.
// Run with the frontend + backend running locally.
// Output files:
//  - docs/images/homepage-table.png
//  - docs/images/campaign-header-grid.png
//  - docs/images/coverage-table.png

const screenshotsDir = path.resolve(__dirname, '../../../../docs/images');

function ensureDir() {
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }
}

test.describe('Screenshot capture', () => {
  test('capture homepage table, campaign header, and coverage table', async ({ page }) => {
    ensureDir();

    // Homepage → Table view
    await page.goto('/');
    await page.getByTestId('view-toggle-table').click();
    const table = page.locator('table#campaigns-table');
    await expect(table).toBeVisible();
    await table.screenshot({ path: path.join(screenshotsDir, 'homepage-table.png') });

    // Open first campaign from table
    const firstRow = page.getByTestId('campaigns-table-row').first();
    await firstRow.click();

    // Campaign header grid
    const headerContainer = page.locator('[aria-labelledby="campaign-details-heading"]');
    await expect(headerContainer).toBeVisible();
    await headerContainer.screenshot({ path: path.join(screenshotsDir, 'campaign-header-grid.png') });

    // Coverage table section (Campaign Results tab is default active)
    // Wait for the section to appear; handle both loading and empty states gracefully
    const coverageHeading = page.getByRole('heading', { name: 'Campaign Coverage Results' });
    await coverageHeading.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});

    // Try to grab the first table following the coverage heading
    const coverageTable = page.locator('xpath=//h3[normalize-space(.)="Campaign Coverage Results"]/following::table[1]');
    if (await coverageTable.count() > 0) {
      await coverageTable.first().screenshot({ path: path.join(screenshotsDir, 'coverage-table.png') });
    } else {
      // Fallback: capture the whole visible area of the tab content
      const tabContent = page.locator('div.p-6');
      await tabContent.first().screenshot({ path: path.join(screenshotsDir, 'coverage-table.png') });
    }
  });
});
