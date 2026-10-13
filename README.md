# 🧑‍🏫 PhyQGen

> 面向高中物理教师的习题生成、智能体自动校验与人工审核辅助工具

**当前状态：** 已整理问题定义、功能规格草案、课标原始资料及研究解读；系统尚未开发完成，暂无可运行版本或正式发布日期。

| 快速入口 | 内容 |
| --- | --- |
| [5W1H 报告与产品描述](docs/requirements/problem_definition.md) | 问题边界、目标用户、拟议方案和验证指标 |
| [功能规格说明书](docs/requirements/functional%2Bnonfunctional_spec.md) | 系统角色、功能需求、业务流程与验收标准 |
| [课标资料与研究解读](#课标资料与研究解读) | 全国课程标准、地方教学文件及对应分析报告 |

## 项目要解决什么

高中物理习题需要同时满足**物理规律正确、条件与答案一致、难度合适**等要求；涉及受力图、电路图等图示时，还要保证图文一致。教师自行编题和逐题核验耗时，而直接使用通用生成工具仍需仔细检查推理、单位、图示与解析。

PhyQGen 计划让教师输入知识点、题型、难度等要求，获得可检查、可修改的习题草稿。智能体在生成过程中进行内部校验并自动修订；教师收到习题后直接进行人工审核和修改，完成后确认定稿，不再触发智能体自动校验。详细边界见[问题定义与产品描述](docs/requirements/problem_definition.md)。

## 预期使用流程

`教师设定要求 → 知识库检索 → 文本与配图生成 → 智能体自动校验与修订 → 教师人工审核、修改与确认 → 保存和导出`

项目需要完成上述环节，并支持单题及批量生成；逐题展示生成进度、习题草稿或生成异常及教师确认状态，校验意见用于系统内部修订。教师可按任务要求选择是否配图、是否启用知识库及生成数量。具体需求与验收标准见[功能规格说明书](docs/requirements/functional%2Bnonfunctional_spec.md)。

## 课标资料与研究解读

已收录全国课程标准及上海、江苏、浙江的教学文件与解读，分析知识范围、考查深度、思维要求和知识形成过程，为后续出题约束、知识库建设与习题质量评价提供参考。

| 范围 | 原始资料 | 研究解读 |
| --- | --- | --- |
| 全国 | [普通高中物理课程标准（2025 年修订）](docs/requirements/Curriculum%20Standard/Official%20Documents/全国.pdf) | [全国课程标准分析报告](docs/requirements/Curriculum%20Standard/Interpretations/全国.md) |
| 上海 | [高中物理教学基本要求（试验本）](docs/requirements/Curriculum%20Standard/Official%20Documents/上海.pdf) | [上海教学基本要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/上海.md) |
| 江苏 | [普通高中物理课程标准教学要求（修订版）](docs/requirements/Curriculum%20Standard/Official%20Documents/江苏.pdf) | [江苏教学要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/江苏.md) |
| 浙江 | [普通高中新课程实验物理学科教学指导意见](docs/requirements/Curriculum%20Standard/Official%20Documents/浙江.pdf) | [浙江教学要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/浙江.md) |

各报告按原始文件的课程体系与版本解读；思维要求和知识来源分类属于研究归纳。

## 仓库导航

```text
PhyQGen/
├─ README.md
├─ .github/                                # GitHub 协作配置
│  ├─ ISSUE_TEMPLATE/                       # 任务与缺陷模板
│  ├─ pull_request_template.md             # PR 模板
│  └─ workflows/                           # 自动化流程预留
├─ docs/
│  ├─ requirements/                        # 需求文档与课标研究
│  │  ├─ problem_definition.md             # 5W1H 与产品描述
│  │  ├─ functional+nonfunctional_spec.md   # 功能与非功能规格说明书
│  │  ├─ images/                           # 用例图、活动图与领域模型图
│  │  └─ Curriculum Standard/              # 课标资料与研究解读
│  │     ├─ Official Documents/            # 全国、上海、江苏、浙江原始 PDF
│  │     └─ Interpretations/               # 四份对应的 Markdown 分析报告
│  ├─ algorithm/                           # 算法研究
│  │  └─ research.md                       # 技术调研，待编写
│  ├─ software/                            # 软件设计
│  │  ├─ prototype/                        # 原型设计预留
│  │  └─ architecture.md                   # 系统架构，待编写
│  ├─ mgmt/                                # 项目管理
│  │  ├─ communication_mgmt_plan.md         # 沟通管理计划，待编写
│  │  └─ risk_mgmt_plan.md                  # 风险管理计划，待编写
│  └─ retrospection/                       # 复盘总结预留
├─ code/
│  ├─ backend/                             # 后端服务预留，尚未实现
│  ├─ frontend/                            # 前端应用预留，尚未实现
│  └─ core_engine/                         # 核心引擎预留，尚未实现
└─ tests/
   ├─ unit/                                # 单元测试预留
   └─ integration/                         # 集成测试预留
```

预留空目录通过 `.gitkeep` 保留在 Git 中；标注“待编写”的 Markdown 文件目前为空。
