async (page) => {
  await page.getByRole('button', { name: '开始生成', exact: true }).click();
  await page.getByText('请填写知识点或命题要求', { exact: true }).waitFor();
  await page.getByRole('button', { name: '牛顿第二定律', exact: true }).click();
  await page.getByRole('combobox', { name: '高阶思维标签', exact: true }).click({ force: true });
  await page.getByRole('option', { name: 'C1 · 建模与多重表征', exact: true }).click();
  await page.getByRole('option', { name: 'C2 · 科学推理与定量分析', exact: true }).click();
  await page.keyboard.press('Escape');
  await page.getByRole('spinbutton', { name: '生成数量', exact: true }).fill('3');
  await page.getByRole('spinbutton', { name: '生成数量', exact: true }).press('Tab');
  await page.locator('.option-card').filter({ hasText: '物理配图' }).locator('.el-switch').click();
  await page.getByRole('textbox', { name: '补充约束（选填）', exact: true }).fill('验证刷新恢复：保留计算步骤与物理示意图。');
  await page.getByRole('button', { name: '开始生成', exact: true }).click();
  await page.waitForURL(/task_id=/);
  const taskUrl = page.url();
  await page.reload();
  if (page.url() !== taskUrl) throw new Error('任务URL在刷新后丢失');
  if (await page.getByRole('spinbutton', { name: '生成数量', exact: true }).inputValue() !== '3') throw new Error('生成数量未恢复');
  if (await page.getByRole('textbox', { name: '*知识点 / 命题要求', exact: true }).inputValue() !== '牛顿第二定律') throw new Error('命题要求未恢复');
  await page.getByRole('combobox', { name: '高阶思维标签', exact: true }).click({ force: true });
  for (const name of ['C1 · 建模与多重表征', 'C2 · 科学推理与定量分析']) {
    if (await page.getByRole('option', { name, exact: true }).getAttribute('aria-selected') !== 'true') throw new Error('高阶思维标签未恢复：' + name);
  }
  await page.keyboard.press('Escape');
  await page.locator('.task-progress').getByText('任务完成', { exact: true }).waitFor({ timeout: 30000 });
  const itemCount = await page.locator('.task-progress .item-card').count();
  const summary = await page.locator('.summary-grid').innerText();
  if (itemCount !== 3 || !(summary.includes('3\n已暂存草稿') || summary.includes('3\n\n已暂存草稿'))) throw new Error('正常批量结果不正确：' + summary);
  await page.locator('.task-progress').screenshot({ path: 'output/playwright/task-normal.png' });
  return { scenario: 'normal', taskUrl, count: itemCount, summary, refreshRestored: true, thinkingTagsRestored: ['C1', 'C2'], requiredValidation: true };
}
