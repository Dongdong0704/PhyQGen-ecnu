async (page) => {
  const cases = [
    { key: 'partial_failure', label: '批量部分失败', count: 3, drafts: 2, failed: 1 },
    { key: 'all_failure', label: '全部生成失败', count: 1, drafts: 0, failed: 1 },
    { key: 'image_failure', label: '配图生成异常', count: 1, drafts: 1, failed: 0, image: true, text: '配图生成失败' },
    { key: 'kb_miss', label: '知识库未命中', count: 1, drafts: 1, failed: 0, text: '未命中匹配资料' },
    { key: 'kb_error', label: '知识检索异常', count: 1, drafts: 1, failed: 0, text: '检索服务异常' },
    { key: 'save_failure', label: '草稿保存失败', count: 1, drafts: 0, failed: 1, text: '未入库内容已保留' },
    { key: 'timeout', label: '模型调用超时', count: 1, drafts: 0, failed: 1, text: '模型调用超时' },
    { key: 'kb_disabled', label: '正常生成', count: 1, drafts: 1, failed: 0, disableKb: true, text: '已关闭知识库增强' },
  ];
  for (const item of cases) {
    await page.goto('http://127.0.0.1:5180/question-gen');
    await page.getByRole('button', { name: '牛顿第二定律', exact: true }).click();
    await page.getByRole('spinbutton', { name: '生成数量', exact: true }).fill(String(item.count));
    await page.getByRole('spinbutton', { name: '生成数量', exact: true }).press('Tab');
    if (item.image) await page.locator('.option-card').filter({ hasText: '物理配图' }).locator('.el-switch').click();
    if (item.disableKb) await page.locator('.option-card').filter({ hasText: '知识库增强' }).locator('.el-switch').click();
    await page.getByRole('button', { name: '流程演示选项', exact: true }).click();
    await page.getByRole('combobox', { name: '流程演示场景', exact: true }).locator('xpath=ancestor::div[contains(@class, "el-select__wrapper")]').click();
    await page.getByRole('option', { name: item.label, exact: true }).click();
    await page.getByRole('button', { name: '开始生成', exact: true }).click();
    await page.waitForURL(/task_id=/);
    item.url = page.url();
  }
  const results = [];
  for (const item of cases) {
    await page.goto(item.url);
    const panel = page.locator('.task-progress');
    await panel.getByText(item.drafts ? '任务完成' : '任务失败', { exact: true }).waitFor({ timeout: 30000 });
    const summary = await panel.locator('.summary-grid > div').allTextContents();
    const values = summary.map(value => Number(value.match(/\d+/)?.[0]));
    if (values[0] !== item.count || values[1] !== item.drafts || values[2] !== item.failed || values[3] !== 0) throw new Error(item.key + ' 汇总不符：' + summary.join(' / '));
    if (await panel.locator('.item-card').count() !== item.count) throw new Error(item.key + ' 逐题结果数量不符');
    if (item.text && !(await panel.innerText()).includes(item.text)) throw new Error(item.key + ' 缺少具体异常/降级说明');
    if (item.key === 'save_failure') {
      await panel.getByRole('button', { name: '查看保留的答案与解析', exact: true }).click();
      await panel.getByRole('button', { name: '复制当前内容', exact: true }).waitFor();
      await panel.locator('.recovery-content').last().waitFor();
      if (await panel.getByRole('button', { name: '打开草稿，人工审核', exact: true }).count() !== 0) throw new Error('保存失败内容错误地提供入库入口');
    }
    if (['kb_disabled', 'kb_miss', 'kb_error'].includes(item.key)) {
      await panel.getByRole('button', { name: '打开草稿，人工审核', exact: true }).click();
      const detail = page.getByRole('dialog');
      await detail.getByRole('tab', { name: '引用来源', exact: true }).click();
      await detail.locator('.el-empty__description').waitFor();
      if (!(await detail.locator('.el-empty__description').innerText()).includes(item.text)) throw new Error(item.key + ' 引用页未说明知识库降级原因');
      if (await detail.locator('.evidence-card').count() !== 0) throw new Error(item.key + ' 错误地保留了引用来源');
      await page.goto(item.url);
    }
    await page.locator('.task-progress').screenshot({ path: 'output/playwright/task-' + item.key + '.png' });
    results.push({ scenario: item.key, requested: values[0], savedDrafts: values[1], failed: values[2], teacherConfirmed: values[3], persisted: true, url: item.url });
  }
  return results;
}
