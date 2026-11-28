# FastAPI 后端

从本目录运行 `python -m pip install -r requirements.txt` 安装依赖，再运行 `python -m uvicorn main:app --host 127.0.0.1 --port 8000`。API 文档位于 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。

| 文件 | 职责 |
| --- | --- |
| `main.py`、`storage.py` | 服务入口、数据库、可选演示数据及在途任务处理 |
| `accounts.py` | 注册、登录和个人资料 |
| `agents/settings.py` | 四个智能体独立的模型配置、加密存储和测试接口 |
| `tasks.py` | 逐题进度、并发执行和草稿事务 |
| `generation.py` | 出题和连通性测试的调用入口 |
| `agents/` | 四个智能体、LangGraph 编排和模型调用 |
| `knowledge.py` | 内置知识资料检索 |
| `questions.py` | 私有题库、版本、教师确认与导出检查 |
| `admin.py`、`community.py` | 账号维护、系统状态、优秀习题和讨论 |

`resources/demo_questions.json` 是可选的原型演示题。`resources/knowledge_index.json` 是从参考项目索引提取的真实片段，包含源文件名和片段 ID。`data/` 首次启动时创建，存放 SQLite 数据和模型配置加密密钥。可用环境变量 `PHYQGEN_DATA_DIR` 自定义数据目录。

## 出题状态图

| 文件 | 后续修改位置 |
| --- | --- |
| `agents/planner.py` | 命题提示词、教学要求和草稿校验 |
| `agents/content_screening.py` | 习题输入和命题草稿的本地粗筛 |
| `agents/text_reviewer.py` | 文本审核提示词和修订反馈 |
| `agents/illustrator.py` | 绘图提示词、蓝图处理和重绘请求 |
| `agents/vision_reviewer.py` | 图文核验提示词和配图通过条件 |
| `agents/workflow.py` | LangGraph 节点连线、分支和单题生成入口 |
| `agents/state.py`、`agents/common.py` | 图状态、运行上下文、角色标识、时限和共享校验 |
| `agents/memory.py` | 初始化单题工作记忆，按教师读取近期命题和已确认的参考片段 |
| `agents/settings.py`、`agents/connections.py`、`agents/model_gateway.py` | 模型配置、连通性测试和模型 HTTP 调用 |

`agents/workflow.py` 中的 `generate_question()` 完成知识检索后，通过 `question_graph.ainvoke()` 运行编译好的 `StateGraph`。问题草稿、审核反馈、轮次和阶段截止时间在图状态中传递。模型凭据、HTTP 客户端和进度回调通过每次运行的 `Runtime` 上下文提供。

- 命题节点输出有效草稿后进入文本审核。输出格式有误或审核提出修改意见时，可返回命题节点，命题最多尝试三次。
- 文本阶段完成后按配图开关结束或进入配图。图文核验可将反馈送回配图节点，配图最多尝试两次。
- 图结束后由现有任务层提交草稿和进度。

[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) · [生成与审核的迭代模式](https://docs.langchain.com/oss/python/langgraph/workflows-agents#evaluator-optimizer)

## 出题内容粗筛

任务接口在入库和调用模型前检查「知识点 / 命题要求」与「补充约束」。命中明确的不安全请求时，接口返回可直接在生成页展示的 422 提示。规则判断具备明确意图的表述，正常的碰撞、触电防护和能量分析可继续生成。命题节点在调用模型前使用同一套规则，覆盖直接调用出题图的情况。

命题智能体使用原有的模型调用判断课堂适宜性，遇到不适合的要求可以返回 `{"refused": true}`。明确拒绝或草稿及绘图蓝图命中本地规则时，该题直接结束并提示调整要求。规则覆盖常见明确表达，更复杂的情境仍由模型判断和教师最终审核。

## 智能体记忆

| 记忆 | 入口 | 用途与有效范围 |
| --- | --- | --- |
| 工作记忆 | `start_working_memory()` | 每道题初始化一份 `GenerationState`。命题与文本审核共享本题要求、草稿与修订意见，配图与图文核验共享绘图蓝图、当前候选图和核验反馈。工作状态随本题运行结束释放。 |
| 情景记忆 | `recall_episodes()` | 读取同一教师、同年级和同知识点最近已入库的命题片段，优先选本批次已保存的题目，最多四道。命题智能体用题名和题干节选避开已经使用的情境和设问。 |
| 长期记忆 | `recall_confirmed_examples()` | 读取同一教师本人确认的当前版本，匹配年级、知识点、题型和配图要求，最多两道。命题智能体用题干和解析节选参考命题与解题思路。编辑后要再次确认才能被引用，删除后即退出检索。 |

`load_prompt_memory()` 在每道题开始时从现有 SQLite 数据读取快照。关闭“知识库增强”时，记忆检索只读取当前批次已保存的题目。历史片段只进入命题智能体的输入，本次提交的要求优先，文本审核和图文核验仍独立检查当题。历史检索失败时，出题继续。知识点采用原有字段的精确匹配，同时运行的两道题可能在对方入库前启动，因此近期片段用于减少重复。

任务与题库保留原有的入库和确认流程，三类记忆沿用现有状态和数据表。教师账号信息、模型凭据和历史配图留在原有数据范围，提供给模型的历史内容限于上表中的文本节选。
