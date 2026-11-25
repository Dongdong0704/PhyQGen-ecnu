async (page) => {
  await page.setViewportSize({ width: 1440, height: 1200 })
  await page.reload()
  await page.getByRole('heading', { name: '用户管理', exact: true }).waitFor()
  await page.getByRole('cell', { name: 'teacher', exact: true }).scrollIntoViewIfNeeded()
  await page.getByRole('heading', { name: '用户管理', exact: true }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'output/playwright/admin-users.png', fullPage: true })
  await page.getByRole('menuitem', { name: '系统维护', exact: true }).click()
  await page.getByRole('heading', { name: '系统维护', exact: true }).waitFor()
  await page.getByRole('heading', { name: '系统维护', exact: true }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'output/playwright/admin-settings.png', fullPage: true })
  await page.locator('.audit-card').scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'output/playwright/admin-audit-log.png', fullPage: true })
}
