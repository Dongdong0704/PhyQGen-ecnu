"""Account maintenance endpoints used by the existing administrator dashboard."""

import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from accounts import Admin, Register, add_user, hash_password, ok, public_user, validate_email
from generation import knowledge_status
from storage import db, now


router = APIRouter(prefix="/v1/admin")


def find_user(conn, user_id):
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(404, "用户不存在")
    return user


def record_action(conn, admin, action):
    conn.execute("INSERT INTO admin_audits (actor, action, time) VALUES (?, ?, ?)", (admin["username"], action, now()))


@router.get("/users")
def list_users(_admin: Admin, role: Literal["TEACHER", "ADMIN"] | None = None):
    with db() as conn:
        rows = conn.execute("SELECT * FROM users WHERE ? IS NULL OR role=? ORDER BY id", (role, role)).fetchall()
    return ok({"users": [public_user(user) for user in rows]})


@router.post("/users", status_code=201)
def create_user(body: Register, admin: Admin):
    with db(write=True) as conn:
        user = add_user(conn, body.username, body.email, body.password, body.role)
        record_action(conn, admin, f"创建账号 {user['username']}")
    return ok(public_user(user))


@router.get("/users/{user_id}")
def get_user(user_id: int, _admin: Admin):
    with db() as conn:
        return ok(public_user(find_user(conn, user_id)))


class UserPatch(BaseModel):
    username: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=254)
    role: Literal["TEACHER", "ADMIN"] | None = None
    is_active: bool | None = None


@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserPatch, admin: Admin):
    with db(write=True) as conn:
        user = find_user(conn, user_id)
        new = {**dict(user), **body.model_dump(exclude_none=True)}
        if admin["id"] == user_id and (not new["is_active"] or new["role"] != "ADMIN"):
            raise HTTPException(422, "不能禁用当前管理员或移除自身管理员角色")
        username = new["username"].strip()
        if len(username) < 3:
            raise HTTPException(422, "用户名须为3～50个字符")
        try:
            conn.execute(
                "UPDATE users SET username=?, email=?, role=?, is_active=?, updated_at=? WHERE id=?",
                (username, validate_email(new["email"]), new["role"], new["is_active"], now(), user_id),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "用户名已存在") from None
        if not new["is_active"] or new["role"] != user["role"]:
            conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        record_action(conn, admin, f"更新账号 {username}")
    return ok()


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


@router.put("/users/{user_id}/password")
def reset_password(user_id: int, body: ResetPassword, admin: Admin):
    with db(write=True) as conn:
        user = find_user(conn, user_id)
        conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?", (hash_password(body.new_password), now(), user_id))
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        record_action(conn, admin, f"重置账号密码 {user['username']}")
    return ok()


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: Admin):
    if admin["id"] == user_id:
        raise HTTPException(422, "不能删除当前管理员")
    with db(write=True) as conn:
        user = find_user(conn, user_id)
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        record_action(conn, admin, f"删除账号 {user['username']}")
    return ok()


@router.get("/status")
def system_status(_admin: Admin):
    with db() as conn:
        rows = conn.execute("SELECT actor, action, time FROM admin_audits ORDER BY id DESC LIMIT 200").fetchall()
    return {**knowledge_status(), "concurrency": 2, "batch_size": 5, "audits": [dict(row) for row in rows]}
