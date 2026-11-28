# 🧑‍🏫 PhyQGen

> 面向高中物理教师的习题生成、智能体自动校验与人工审核辅助工具

当前版本可在本地运行，支持习题生成、自动校验、教师审核定稿和 TXT 导出。应用代码位于 `code/`，采用 Vue 3、FastAPI 和 SQLite。历史交互原型位于 `docs/software/prototype/`。

## 快速启动

以下命令以 Windows PowerShell 为例，使用 Python 3.11 和 Node.js 20。请从仓库根目录分别打开两个终端。

**后端（终端一）**

```powershell
cd code/backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**前端（终端二）**

```powershell
cd code/frontend
npm.cmd ci
npm.cmd run dev
```

前端开发服务器将 `/api` 转发到 `127.0.0.1:8000`。在两个终端分别按 `Ctrl+C` 可停止服务。[打开 PhyQGen](http://127.0.0.1:5173/) · [API 文档](http://127.0.0.1:8000/docs) · [后端健康检查](http://127.0.0.1:8000/api/v1/health)

首次使用可在登录页注册教师账号。在「个人中心」为命题和文本审核智能体分别填写 OpenAI 兼容接口的 API 地址、模型名称和服务商要求的密钥，并测试连接。启用配图时，还需配置配图生成模型和支持图片输入的图文核验模型。

本地数据默认存放在 `code/backend/data/`。可在启动后端前通过 `PHYQGEN_DATA_DIR` 指定其他目录。迁移已有数据时，请一并保留 SQLite 数据库和数据目录内的 `model-settings.key`，以便继续读取加密的模型配置。

## 项目要解决什么

高中物理习题需要同时满足**物理规律正确、条件与答案一致、难度合适**等要求。涉及受力图、电路图等图示时，还要检查图文一致性。教师自行编题和逐题核验耗时，通用生成工具给出的推理、单位、图示与解析也需要仔细检查。

PhyQGen 让教师输入年级、知识点、题型、认知目标和目标难度等要求，获得可检查、可修改的习题草稿。智能体在生成阶段校验和修订草稿，教师随后在题库审核、修改并确认定稿。[问题定义与产品描述](docs/requirements/problem_definition.md)

## 使用流程

`教师设定要求 → 内容粗筛 → 按需检索知识库 → 命题与文本审核 → 按需配图与图文核验 → 教师审核确认 → TXT 导出`

- **习题生成**支持每批 1～5 道，逐题展示进度、草稿和异常。开启「知识库增强」后，可检索带来源的课标和例题片段，并参考本人题库中相关的历史题目。
- **我的题库**支持关键词搜索、条件筛选、版本记录和教师确认。编辑会生成一个待确认的新版本。当前版本经教师确认后，可单题或批量导出 TXT。
- **优秀习题**向已登录用户展示当前版本已确认且评分至少为 4 分的题目，支持讨论和回复。
- **管理员**可管理账号、查看系统状态和操作记录。如需初始化管理员，可在启动后端前将 `PHYQGEN_ADMIN_PASSWORD` 设为至少 12 个字符的密码。系统启动时若还没有管理员账号，会创建 `admin`。

### 内容粗筛与智能体记忆

提交时，后端先检查「知识点 / 命题要求」和「补充约束」，拦截明确不适合高中课堂的输入。命题智能体还会判断课堂适宜性，并在文本审核和配图前复查草稿及绘图说明。物理事故分析、触电防护等正常教学情境可以继续生成。

| 记忆类型 | 当前用途 |
| --- | --- |
| 工作记忆 | 在单题的 LangGraph 状态中传递命题要求、草稿、审核反馈和重绘反馈。 |
| 情景记忆 | 参考同一教师、同年级、同知识点的近期题目，优先读取本批次已入库的题目，帮助改变情境或设问。 |
| 长期记忆 | 参考教师本人已确认的当前版本，借鉴同类题的命题和解题思路。编辑后需重新确认才会重新纳入参考。 |

关闭「知识库增强」时，历史题目检索只读取本批次已保存的题目。[命题粗筛与记忆说明](code/backend/README.md)

## 开发验证

安装依赖后，从仓库根目录运行以下命令。后端测试覆盖优秀习题与讨论、内容粗筛及历史记忆，模型相关用例使用模拟响应。

```powershell
cd code/backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

cd ../frontend
npm.cmd run typecheck
```

## 项目文档

| 快速入口 | 内容 |
| --- | --- |
| [5W1H 报告与产品描述](docs/requirements/problem_definition.md) | 问题边界、目标用户、拟议方案和验证指标 |
| [功能规格说明书](docs/requirements/functional%2Bnonfunctional_spec.md) | 系统角色、功能需求、业务流程与验收标准 |
| [用户故事与验收标准](docs/requirements/user_stories.md) | 教师与管理员的使用目标、正常流程及异常场景 |
| [系统设计技术方案](docs/software/architecture.md) | 技术选型、分层架构、智能体编排与开发计划 |
| [后端实现说明](code/backend/README.md) | 当前出题状态图、内容粗筛与三类记忆的实现 |
| [代码质量检查](docs/software/code_quality.md) · [代码评审](docs/software/code_review.md) | 阶段性工程检查与评审记录 |
| [沟通管理计划](docs/mgmt/communication_mgmt_plan.md) | 协作职责、沟通安排与变更流程 |
| [风险管理计划](docs/mgmt/risk_mgmt_plan.md) | 风险识别、优先级评估、应对与跟踪 |
| [课标资料与研究解读](#课标资料与研究解读) | 全国课程标准、地方教学文件及对应分析报告 |
| [高中物理高阶思维能力调研](docs/requirements/Curriculum%20Standard/Higher-Order%20Thinking%20Skills%20in%20High%20School%20Physics.md) | 六项能力标签、成立判据、命题示例与审核边界 |
| [SWE-agent 文献调研报告](docs/algorithm/research.md) | 核心方法、实验结果、研究局限及对 PhyQGen 的设计启发 |

## 课标资料与研究解读

已收录全国课程标准及上海、江苏、浙江的教学文件与解读，分析知识范围、考查深度、思维要求和知识形成过程，为后续出题约束、知识库建设与习题质量评价提供参考。

| 范围 | 原始资料 | 研究解读 |
| --- | --- | --- |
| 全国 | [普通高中物理课程标准（2025 年修订）](docs/requirements/Curriculum%20Standard/Official%20Documents/全国.pdf) | [全国课程标准分析报告](docs/requirements/Curriculum%20Standard/Interpretations/全国.md) |
| 上海 | [高中物理教学基本要求（试验本）](docs/requirements/Curriculum%20Standard/Official%20Documents/上海.pdf) | [上海教学基本要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/上海.md) |
| 江苏 | [普通高中物理课程标准教学要求（修订版）](docs/requirements/Curriculum%20Standard/Official%20Documents/江苏.pdf) | [江苏教学要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/江苏.md) |
| 浙江 | [普通高中新课程实验物理学科教学指导意见](docs/requirements/Curriculum%20Standard/Official%20Documents/浙江.pdf) | [浙江教学要求分析报告](docs/requirements/Curriculum%20Standard/Interpretations/浙江.md) |

各报告按原始文件的课程体系与版本解读。思维要求和知识来源分类属于研究归纳。

## 高阶思维能力研究

[高中物理高阶思维能力调研](docs/requirements/Curriculum%20Standard/Higher-Order%20Thinking%20Skills%20in%20High%20School%20Physics.md)结合课标、教学研究与高中命题评析，归纳六项习题能力标签，为命题设计、标签标注和质量评价提供参考。

| 标签 | 能力 |
| --- | --- |
| C1 | 建模与多重表征 |
| C2 | 科学推理与定量分析 |
| C3 | 证据论证与科学解释 |
| C4 | 实验设计与数据评价 |
| C5 | 批判质疑与方案创新 |
| C6 | 迁移整合与真实问题解决 |

认知目标、目标难度与高阶思维标签分别描述。标签是否成立，依据设问要求学生完成的思维活动，以及答案、解析或评分点能否检查该活动。计算繁复或背景新颖本身不足以认定高阶思维。

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
│  │  ├─ user_stories.md                    # 用户故事与验收标准
│  │  ├─ images/                           # 用例图、活动图与领域模型图
│  │  └─ Curriculum Standard/              # 课标资料与高阶思维研究
│  │     ├─ Higher-Order Thinking Skills in High School Physics.md
│  │     │                                 # 六项能力标签与审核判据
│  │     ├─ Official Documents/            # 全国、上海、江苏、浙江原始 PDF
│  │     └─ Interpretations/               # 四份对应的 Markdown 分析报告
│  ├─ algorithm/                           # 算法研究
│  │  └─ research.md                       # SWE-agent 文献调研与项目启发
│  ├─ software/                            # 软件设计与交互原型
│  │  ├─ prototype/                        # 历史交互原型
│  │  ├─ architecture.md                   # 系统设计技术方案
│  │  ├─ code_quality.md                   # 阶段性代码质量检查
│  │  └─ code_review.md                    # 代码评审记录
│  ├─ mgmt/                                # 项目管理
│  │  ├─ communication_mgmt_plan.md         # 沟通管理计划
│  │  └─ risk_mgmt_plan.md                  # 风险管理计划
│  └─ retrospection/                       # 复盘总结预留
├─ code/
│  ├─ backend/                             # FastAPI、SQLite、LangGraph
│  │  ├─ agents/                           # 智能体、内容粗筛与记忆
│  │  ├─ resources/                        # 知识索引与演示题
│  │  └─ tests/                            # 后端回归测试
│  └─ frontend/                            # Vue 3、TypeScript、Vite
└─ tests/
   ├─ unit/                                # 单元测试预留
   └─ integration/                         # 集成测试预留
```

预留空目录通过 `.gitkeep` 保留在 Git 中。
