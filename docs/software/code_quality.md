# PhyQGen 系统代码质量检查

检查日期：2026-11-25。本次我们对 PhyQGen 重构后的代码进行质量检查，范围包括 `code/backend` 后端服务和 `code/frontend` 前端应用。检查结合重构前后的 Pylint 报告、自动化测试和代码自查，重点总结重构成效、验证结果与后续优化安排。

## 一 检查结论

本轮检查后，项目 Pylint 评分由重构前的 **8.4963 提升至 8.6275**，扫描诊断由 222 条减少至 210 条，Error 类诊断已清零。项目已通过五项回归测试、启动与概览检查，以及前端类型检查和生产构建。现有结果体现了本轮重构和检查修正的阶段性成效。

本轮主要完善了公开字段筛选和变量命名：将字段名显式转换为集合，消除 Pydantic 动态属性对应的 E1135 静态告警；调整题目查询变量和应用生命周期参数名称，消除三条 W0621 告警。修正保持了既有接口和权限规则，相关测试均通过。修改详见 [补丁](quality/evidence/minimal-fixes.patch)。

剩余诊断以文档字符串、行长度等代码规范提示为主，另有少量结构优化建议。后续将结合开发计划逐步完善；按 CodeQualitySkill strict 标准，完整质量验收仍有待完成的检查与改进项。

## 二 重构前后对比

本次对比采用三个阶段的数据：重构前、第一轮重构后，以及本轮检查修正后。其中，`pylint-after.json2` 对应重构前报告，`pylint-refactored.json` 对应第一轮重构后报告。

| 阶段 | 分数 | 总问题数 | Error | Warning | Refactor | Convention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 重构前 | 8.4963 | 222 | 1 | 4 | 6 | 211 |
| 第一轮重构后 | 8.5752 | 214 | 1 | 4 | 4 | 205 |
| 本轮检查修正后 | 8.6275 | 210 | 0 | 1 | 4 | 205 |

前两份报告均记录 23 个模块，但未记录工具版本和运行命令。为保证比较口径一致，我们使用 Pylint 4.1.4、Astroid 4.3.4 对重构后的源码执行 `python -m pylint --output-format=json2 code/backend`，完整复现重构后统计（8.57516339869281、214 条）。据此，本轮修正前后的扫描结果可以直接比较。23 为工具统计的模块数；实际有 20 个业务 Python 文件及 1 个测试文件。

第一轮重构后，缺失函数说明由 116 减为 114，超长行由 66 减为 62，too-many-locals 和 too-many-boolean-expressions 各减少一条。重构后的 `_unpack_question` 与 `_valid_endpoint` 将选项解析、答案验证和地址验证拆分为独立职责，降低了单个函数的处理负担。重构前后的量化比较以保留的扫描报告为依据；由于本次检查未包含重构前完整源码，完整行为一致性仍需结合版本差异和更全面的回归测试验证。

## 三 扫描报告截图

以下截图展示三个阶段的 Pylint 扫描结果。截图由对应 JSON 报告生成，包含评分、规则分布和主要诊断信息，原始报告保存在 `quality/evidence/` 中。

![重构前扫描](quality/scans/pylint-before.png)

![第一轮重构后扫描](quality/scans/pylint-refactored.png)

![本轮检查修正后扫描](quality/scans/pylint-reviewed.png)

## 四 自动检查和证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| Python 语法编译 | 通过 | `python -m compileall -q .`，[日志](quality/evidence/compile.log) |
| 前端类型和生产构建 | 通过 | `npm ci --ignore-scripts --no-audit --no-fund`；`npm run build`，[构建日志](quality/evidence/frontend-build.log)；两个 JS 包约 1.12 MB 与 1.43 MB，触发 500 kB 提示 |
| 原有回归测试 | 5/5 通过 | [修正前](quality/evidence/tests-before.log)、[修正后](quality/evidence/tests-after.log)；覆盖公开字段过滤、旧版确认撤回、回复隔离与分页 |
| 启动与概览冒烟 | 通过 | [日志](quality/evidence/lifespan-smoke.log)：生命周期启动退出、健康检查、注册与空题库概览 |
| 覆盖率 | 整体 33.99%；业务源码 26.93%（383/1422） | [Coverage JSON](quality/evidence/coverage.json)；整体数值包含测试文件，业务数值排除 `tests/`。这是已有测试的覆盖率，不是新增代码覆盖率 |
| Pylint | Error(0) / Warning(1)，另有 4 项重构及 205 项约定提示 | [修正后报告](quality/evidence/pylint-local-after.json)；剩余诊断以规范提示和局部结构建议为主，退出码为 28 |
| 圈复杂度 | 当前 Radon 扫描没有函数超过 10 | [Radon JSON](quality/evidence/complexity.json)；本次未测量认知复杂度 |
| Bandit | 4 条 Medium、4 条 Low、0 条 High | [扫描 JSON](quality/evidence/bandit.json)；逐项解释见下文 |
| 依赖漏洞、重复率、Python 严格类型检查 | 未验证 | 未执行 pip-audit、npm audit、jscpd、mypy；列入后续检查计划 |
| 版本控制 | 本地检查副本不含 Git 历史 | 本次未检查正式仓库的提交状态，修正内容需与项目仓库同步 |

Bandit 的四项 B608 均在 community.py，涉及服务端常量条件、排序白名单或按主题数量生成的占位符；用户数据仍用 SQL 参数绑定。我们检查了相关 SQL 的参数绑定及排序白名单，暂未发现用户输入直接拼接到 SQL 结构中的情况，后续仍需复核。B105 命中 `token_type='bearer'` 和错误字段标签等字符串，目前按候选误报记录。本次安全扫描未发现 High 级告警，但完整安全验证还需补充依赖审计和接口测试。

## 五 后续优化安排

结合本轮检查，我们将后续工作归纳为三个方向：

1. **拓展测试场景。** 在现有社区模块回归测试的基础上，逐步增加生成、认证、任务恢复和模型调用等场景，提升关键流程的验证覆盖。
2. **持续完善工程规范。** 统一文档字符串与排版，适度拆分局部函数，完善依赖版本记录、日志配置和架构说明，使代码与文档更便于维护。具体位置见评审表。
3. **按使用规模优化。** 当前任务机制面向单实例运行；随着题库规模和部署需求增长，再完善摘要分页、任务归属及生成过程记录。真实生成质量与教学适配性结合后续教师试评验证。

对于 `tasks.py:133` 的宽泛异常捕获，经检查，其承担逐题隔离与失败状态记录的职责。本轮保留该机制，并将异常分类及日志细化纳入后续维护计划。

## 六 检查方法与复现步骤

我们参考 [CodeQualitySkill](https://github.com/bettermorn/ACMWDevHubPPT/blob/master/Methodology/CodeQualitySkill.md) 及其[使用说明](https://github.com/bettermorn/ACMWDevHubPPT/blob/master/Methodology/CodeQualitySkill-%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E.md)，按“静态扫描、测试验证、问题定位、修正复查”的流程开展检查，并使用[配套模板](https://github.com/bettermorn/ACMWDevHubPPT/blob/master/Methodology/CodeReviewTemplate.md)整理评审结果。Skill 和模板副本保存在 `quality/` 目录，便于后续沿用同一检查标准。

检查环境为 Python 3.12 与 Node 24.22.1。工具版本见 [版本记录](quality/evidence/tool-versions.json)。可在已有依赖环境从项目根执行：

```sh
python -m pylint --output-format=json2 code/backend > pylint-current.json
python -m radon cc code/backend -j > complexity.json
python -m bandit -r code/backend -f json -o bandit.json
cd code/backend
python -m coverage run --source=. -m unittest discover -s tests -v
python -m coverage report
python -m compileall -q .
```

前端从 `code/frontend` 执行 `npm ci` 和 `npm run build`。质量检查工具与业务依赖分别管理，工具依赖见 `quality/requirements-tools.txt`。完整检查项与整改状态见 [代码评审](code_review.md)。真实模型调用效果、生产压力和安全渗透测试将在后续专项验证中开展。
