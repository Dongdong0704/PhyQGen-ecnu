"""PhyQGen HTTP entry point."""

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import accounts
import admin
import community
import questions
import tasks
from agents import settings as agent_settings
from storage import db, decode, initialize


def bootstrap_accounts():
    admin_password = os.getenv("PHYQGEN_ADMIN_PASSWORD")
    demo = os.getenv("PHYQGEN_DEMO") == "1"
    with db(write=True) as conn:
        if admin_password and conn.execute("SELECT 1 FROM users WHERE role='ADMIN'").fetchone() is None:
            if len(admin_password) < 12:
                raise RuntimeError("PHYQGEN_ADMIN_PASSWORD must be at least 12 characters")
            accounts.add_user(conn, "admin", "", admin_password, "ADMIN")
        if demo and conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None:
            teacher = accounts.add_user(conn, "teacher", "teacher@example.com", "Teacher123", "TEACHER")
            accounts.add_user(conn, "admin", "admin@example.com", "Admin123", "ADMIN")
            accounts.add_user(conn, "physics_li", "li@example.com", "Teacher123", "TEACHER")
            fixture = Path(__file__).parent / "resources" / "demo_questions.json"
            for question in decode(fixture.read_text(encoding="utf-8")):
                question["user_id"] = teacher["id"]
                for confirmation in question["confirmations"]:
                    confirmation["teacher_id"] = teacher["id"]
                questions.insert_question(conn, question)


@asynccontextmanager
async def lifespan(app):
    initialize()
    bootstrap_accounts()
    tasks.finish_interrupted_tasks()
    app.state.workers = set()
    app.state.generation_slots = asyncio.Semaphore(2)
    try:
        yield
    finally:
        workers = list(app.state.workers)
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        tasks.finish_interrupted_tasks()


app = FastAPI(title="PhyQGen", lifespan=lifespan)
for router in (accounts.router, admin.router, agent_settings.router, community.router, questions.router, tasks.router):
    app.include_router(router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def invalid_input(_request: Request, exc: RequestValidationError):
    fields = {
        "base_url": "API 地址", "model": "模型名称", "api_key": "API 密钥", "role": "智能体",
        "username": "用户名", "email": "邮箱", "password": "密码",
        "new_password": "新密码", "old_password": "原密码", "count": "生成数量",
        "grade": "年级", "difficulty": "目标难度", "knowledge_point": "知识点",
        "question_type": "题型", "bloom_level": "认知目标", "thinking_tags": "高阶思维标签",
        "illustration_url": "配图", "context": "补充约束",
    }
    location = exc.errors()[0].get("loc", ())
    label = next((fields[part] for part in location if part in fields), "")
    message = f"请检查{label}的格式和长度" if label else "提交的数据格式不正确"
    return JSONResponse(status_code=422, content={"detail": message})


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
