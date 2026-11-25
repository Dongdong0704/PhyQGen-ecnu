"""Persist generation progress and commit each usable draft with its task item."""

import asyncio
import logging
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from accounts import Teacher
from agents.settings import missing_roles, read_model
from generation import QUESTION_TIMEOUT_SECONDS, GenerationError, generate_question, knowledge_status
from questions import insert_question, version_snapshot
from storage import db, decode, encode, now


router = APIRouter(prefix="/v1/generation")
logger = logging.getLogger(__name__)


class GenerationParams(BaseModel):
    knowledge_point: str = Field(max_length=1000)
    grade: Literal["高一", "高二", "高三"]
    question_type: Literal["single_choice", "multiple_choice", "fill_blank", "short_answer"]
    bloom_level: Literal["remember", "understand", "apply", "analyze"]
    difficulty: Literal["基础", "中等", "困难"]
    count: int = Field(ge=1, le=5, strict=True)
    require_illustration: bool = False
    use_kb: bool = True
    context: str = Field(default="", max_length=4000)
    thinking_tags: list[Literal["C1", "C2", "C3", "C4", "C5", "C6"]] = Field(default_factory=list, max_length=6)


def write_task(conn, task):
    conn.execute("UPDATE tasks SET completed=?, payload=? WHERE id=?", (task["completed"], encode(task), task["id"]))


def finalize_status(task):
    items = task["items"]
    task["progress"] = sum(item["progress"] for item in items) // len(items)
    task["completed"] = all(item["status"] in {"draft", "failed"} for item in items)
    if task["completed"]:
        drafts = sum(item["status"] == "draft" for item in items)
        if drafts == 0:
            task["stage"] = "生成失败"
            task["error"] = "本批次没有成功入库的草稿"
        elif drafts < len(items):
            task["stage"] = "部分完成"
            task["error"] = "有个别题目未能入库，请查看逐题结果"
        else:
            task["stage"] = "草稿已暂存，待教师审核"
    else:
        task["stage"] = "正在生成"


def finish_interrupted_tasks():
    with db(write=True) as conn:
        for row in conn.execute("SELECT payload FROM tasks WHERE completed = 0").fetchall():
            task = decode(row[0])
            for item in task["items"]:
                if item["status"] in {"pending", "running"}:
                    item.update(status="failed", stage="服务已中断", progress=100, error="服务已重启，请重新提交未完成的题目")
            finalize_status(task)
            write_task(conn, task)


def question_payload(task, result):
    params = task["params"]
    date = now()
    question = {
        **{key: params[key] for key in ("grade", "question_type", "bloom_level", "difficulty", "knowledge_point", "thinking_tags")},
        **{key: result.get(key) for key in ("title", "content", "options", "answer", "explanation", "illustration_url")},
        "user_id": task["user_id"],
        "task_id": task["id"],
        "require_illustration": params["require_illustration"],
        "created_at": date,
        "updated_at": date,
        "teacher_status": "pending",
        "version": 1,
        "evidence": result.get("evidence", []),
        "kb_reason": result.get("kb_reason", ""),
        "confirmations": [],
        "rating": None,
        "comment": "",
    }
    if isinstance(question["options"], dict):
        question["options"] = encode(question["options"])
    question["versions"] = [version_snapshot(question, "system")]
    return question


def patch_item(task_id, index, changes, result=None):
    with db(write=True) as conn:
        row = conn.execute("SELECT payload FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            return
        task = decode(row[0])
        item = task["items"][index - 1]
        item.update(changes)
        if result is not None:
            question = insert_question(conn, question_payload(task, result))
            item["question_id"] = question["id"]
        finalize_status(task)
        write_task(conn, task)


async def run_item(semaphore, task, config, index):
    task_id = task["id"]
    stage_name = "等待调度"

    def update(stage, progress, attempt):
        nonlocal stage_name
        stage_name = stage
        patch_item(task_id, index, {"stage": stage, "progress": min(99, max(0, progress)), "attempt": attempt, "status": "running"})

    async with semaphore:
        result = None
        try:
            result = await asyncio.wait_for(
                generate_question(task["params"], config, update, index),
                timeout=QUESTION_TIMEOUT_SECONDS,
            )
            changes = {"status": "draft", "stage": "草稿已暂存", "progress": 100}
            if result.get("error"):
                changes["error"] = result["error"]
            patch_item(task_id, index, changes, result)
            return
        except asyncio.TimeoutError:
            error = f"单题生成达到总时限，超时阶段为「{stage_name}」。请检查对应智能体配置或重试"
        except GenerationError as exc:
            error = str(exc)
        except Exception as exc:
            logger.error("Generation item %s #%s failed (%s)", task_id, index, type(exc).__name__)
            error = "草稿保存失败" if result is not None else "题目生成失败，请重试"

        if result is None:
            patch_item(task_id, index, {"status": "failed", "stage": "生成失败", "progress": 100, "error": error})
        else:
            draft = question_payload(task, result)
            draft["id"] = 0
            patch_item(task_id, index, {"status": "failed", "stage": "暂存失败", "progress": 100, "error": error, "retained_draft": draft})


async def run_task(semaphore, task, config):
    await asyncio.gather(*(run_item(semaphore, task, config, item["index"]) for item in task["items"]))


@router.get("/knowledge")
def knowledge(_user: Teacher):
    return knowledge_status()


@router.post("/tasks", status_code=201)
async def create_task(body: GenerationParams, user: Teacher, request: Request):
    params = body.model_dump()
    params["knowledge_point"] = params["knowledge_point"].strip()
    if not params["knowledge_point"]:
        raise HTTPException(422, "请输入知识点或命题要求")
    params["thinking_tags"] = list(dict.fromkeys(params["thinking_tags"]))
    task = {
        "id": f"TASK-{uuid.uuid4().hex[:16]}",
        "user_id": user["id"],
        "created_at": now(),
        "params": params,
        "stage": "待处理",
        "progress": 0,
        "completed": False,
        "items": [
            {"index": index, "status": "pending", "stage": "待处理", "progress": 0, "attempt": 0}
            for index in range(1, body.count + 1)
        ],
    }
    with db(write=True) as conn:
        config = read_model(conn, user["id"])
        missing = missing_roles(config, body.require_illustration)
        if missing:
            names = "、".join(missing)
            raise HTTPException(409, f"请先在个人中心配置并保存以下智能体的模型 API：{names}")
        running = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=0", (user["id"],)).fetchone()[0]
        if running >= 2:
            raise HTTPException(409, "尚有两批题目在生成，请等待完成后再提交")
        conn.execute(
            "INSERT INTO tasks (id, user_id, created_at, payload) VALUES (?, ?, ?, ?)",
            (task["id"], user["id"], task["created_at"], encode(task)),
        )
    worker = asyncio.create_task(run_task(request.app.state.generation_slots, task, config))
    workers = request.app.state.workers
    workers.add(worker)
    worker.add_done_callback(workers.discard)
    return task


@router.get("/tasks")
def recent_tasks(user: Teacher):
    with db() as conn:
        rows = conn.execute("SELECT payload FROM tasks WHERE user_id=? ORDER BY created_at DESC, rowid DESC", (user["id"],))
        return [decode(row[0]) for row in rows]


@router.get("/tasks/{task_id}")
def task_detail(task_id: str, user: Teacher):
    with db() as conn:
        row = conn.execute("SELECT payload FROM tasks WHERE id=? AND user_id=?", (task_id, user["id"])).fetchone()
        if row is None:
            raise HTTPException(404, "没有找到这个生成批次")
        return decode(row[0])
