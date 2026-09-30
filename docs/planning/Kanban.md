# Kanban 使用约定

工作条目以 GitHub Issues 为准；一个 Issue 对应一个可验收任务或一个缺陷。

| 状态 | 进入条件 | 离开条件 |
| --- | --- | --- |
| Backlog | 已记录需求、任务或缺陷 | 明确优先级和验收标准 |
| Ready | 可在本周开始，依赖已明确 | 有负责人并开始处理 |
| In progress | 正在实施，最多同时处理 2 项/人 | 提交 PR 或需要评审 |
| In review | PR、文档或修复等待检查 | 验收通过或退回修改 |
| Done | 验收完成，Issue 关闭 | 复发时重开 |

缺陷使用 `bug` 标签；阻碍使用 `blocked` 标签，并在 Issue 中写明依赖和下一步。优先级使用 `priority:high`、`priority:medium`、`priority:low`。每周计划通过 `week-1` 等标签或 Project 迭代字段跟踪。

## 每周例会

1. 检查 In progress 和 blocked 条目。
2. 验收 In review 条目并关闭已完成的 Issue。
3. 按优先级从 Backlog 补充 Ready 条目。
4. 更新负责人和完成时间；把新增决定写回对应 Issue。

GitHub Project 建议采用 Board 视图，以 `Status` 分组并使用上述五列；另建 Table 视图查看负责人、优先级和迭代。项目建立后将链接补在本文件。
