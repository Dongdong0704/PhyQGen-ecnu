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
| `agents/text_reviewer.py` | 文本审核提示词和修订反馈 |
| `agents/illustrator.py` | 绘图提示词、蓝图处理和重绘请求 |
| `agents/vision_reviewer.py` | 图文核验提示词和配图通过条件 |
| `agents/workflow.py` | LangGraph 节点连线、分支和单题生成入口 |
| `agents/state.py`、`agents/common.py` | 图状态、运行上下文、角色标识、时限和共享校验 |
| `agents/settings.py`、`agents/connections.py`、`agents/model_gateway.py` | 模型配置、连通性测试和模型 HTTP 调用 |

`agents/workflow.py` 中的 `generate_question()` 完成知识检索后，通过 `question_graph.ainvoke()` 运行编译好的 `StateGraph`。问题草稿、审核反馈、轮次和阶段截止时间在图状态中传递。模型凭据、HTTP 客户端和进度回调通过每次运行的 `Runtime` 上下文提供。

- 命题节点输出有效草稿后进入文本审核。输出格式有误或审核提出修改意见时，可返回命题节点，命题最多尝试三次。
- 文本阶段完成后按配图开关结束或进入配图。图文核验可将反馈送回配图节点，配图最多尝试两次。
- 图结束后由现有任务层提交草稿和进度。

[LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) · [生成与审核的迭代模式](https://docs.langchain.com/oss/python/langgraph/workflows-agents#evaluator-optimizer)
