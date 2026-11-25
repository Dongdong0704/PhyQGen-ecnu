"""Account sessions, profile and per-teacher model credentials."""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from storage import db, decode, encode, now


router = APIRouter(prefix="/v1")
bearer = HTTPBearer(auto_error=False)
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]


def ok(data=None):
    return {"code": 0, "message": "操作成功", "data": data if data is not None else {}}


def hash_password(password):
    salt = secrets.token_hex(16)
    return f"{salt}:{password_digest(password, salt)}"


def password_digest(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()


def check_password(password, stored):
    salt, digest = stored.split(":")
    return hmac.compare_digest(password_digest(password, salt), digest)


def public_user(user):
    result = dict(user)
    result.pop("password_hash", None)
    result["is_active"] = bool(result["is_active"])
    return result


def validate_email(email):
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(422, "请输入有效的邮箱地址")
    return email


def add_user(conn, username, email, password, role):
    username = username.strip()
    if len(username) < 3:
        raise HTTPException(422, "用户名须为3～50个字符")
    created = now()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, role, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, validate_email(email), hash_password(password), role, created, created),
        )
    except sqlite3.IntegrityError:
        raise HTTPException(409, "用户名已存在") from None
    return conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()


def token_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(conn, user):
    timestamp = int(time.time())
    token = secrets.token_urlsafe(32)
    conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (timestamp,))
    conn.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token_digest(token), user["id"], timestamp + 7 * 86400))
    conn.execute("INSERT INTO logins (user_id, login_time) VALUES (?, ?)", (user["id"], now()))
    return ok({"access_token": token, "token_type": "bearer", "user": public_user(user)})


def current_user(credentials: Credentials):
    if not credentials:
        raise HTTPException(401, "请先登录")
    with db() as conn:
        user = conn.execute(
            "SELECT u.* FROM users u JOIN sessions s ON s.user_id = u.id "
            "WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1",
            (token_digest(credentials.credentials), int(time.time())),
        ).fetchone()
    if user is None:
        raise HTTPException(401, "登录已失效，请重新登录")
    return user


User = Annotated[sqlite3.Row, Depends(current_user)]


def require_teacher(user: User):
    if user["role"] != "TEACHER":
        raise HTTPException(403, "请使用教师账号")
    return user


def require_admin(user: User):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "请使用管理员账号")
    return user


Teacher = Annotated[sqlite3.Row, Depends(require_teacher)]
Admin = Annotated[sqlite3.Row, Depends(require_admin)]


class Login(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(min_length=6, max_length=128)


class Register(Login):
    email: str = Field(default="", max_length=254)
    role: Literal["TEACHER", "ADMIN"] = "TEACHER"


@router.get("/auth/options")
def auth_options():
    return {"demo": os.getenv("PHYQGEN_DEMO") == "1"}


@router.post("/auth/login")
def login(body: Login):
    with db(write=True) as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (body.username.strip(),)).fetchone()
        if user is None or not check_password(body.password, user["password_hash"]):
            raise HTTPException(400, "用户名或密码错误")
        if not user["is_active"]:
            raise HTTPException(403, "账号已禁用，请联系管理员")
        return start_session(conn, user)


@router.post("/auth/register", status_code=201)
def register(body: Register):
    if body.role != "TEACHER":
        raise HTTPException(403, "普通注册仅支持教师账号")
    with db(write=True) as conn:
        return start_session(conn, add_user(conn, body.username, body.email, body.password, body.role))


@router.post("/auth/logout")
def logout(credentials: Credentials):
    if credentials:
        with db(write=True) as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_digest(credentials.credentials),))
    return {}


class ProfilePatch(BaseModel):
    email: str | None = Field(default=None, max_length=254)
    avatar_url: str | None = Field(default=None, max_length=4_000_000)


@router.get("/profile/info")
def profile(user: User):
    return public_user(user)


@router.put("/profile/info")
def edit_profile(body: ProfilePatch, user: User):
    email = user["email"] if body.email is None else validate_email(body.email)
    avatar = user["avatar_url"] if body.avatar_url is None else body.avatar_url
    if avatar and not re.match(r"^data:image/(png|jpeg|webp|gif|bmp);base64,", avatar):
        raise HTTPException(422, "请上传 PNG、JPEG、WebP、GIF 或 BMP 头像")
    with db(write=True) as conn:
        conn.execute("UPDATE users SET email=?, avatar_url=?, updated_at=? WHERE id=?", (email, avatar, now(), user["id"]))
    return ok()


class ChangePassword(BaseModel):
    old_password: str = Field(max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


@router.post("/profile/change-password")
def change_password(body: ChangePassword, user: User, credentials: Credentials):
    with db(write=True) as conn:
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
        if row is None or not check_password(body.old_password, row["password_hash"]):
            raise HTTPException(400, "原密码不正确")
        conn.execute("UPDATE users SET password_hash=?, updated_at=? WHERE id=?", (hash_password(body.new_password), now(), user["id"]))
        conn.execute("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (user["id"], token_digest(credentials.credentials)))
    return ok()


@router.get("/profile/stats")
def profile_stats(user: User):
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM questions WHERE user_id=?", (user["id"],)).fetchone()[0]
        log = conn.execute("SELECT COUNT(*) AS total_logins, MAX(login_time) AS last_login_time FROM logins WHERE user_id=?", (user["id"],)).fetchone()
    return {"total_questions": count, **dict(log)}


@router.get("/profile/login-logs")
def login_logs(user: User):
    with db() as conn:
        rows = conn.execute("SELECT id, login_time FROM logins WHERE user_id=? ORDER BY id DESC LIMIT 100", (user["id"],)).fetchall()
    return [{**dict(row), "login_status": "success"} for row in rows]


@router.get("/profile/preferences")
def preferences(user: User):
    with db() as conn:
        row = conn.execute("SELECT payload FROM preferences WHERE user_id = ?", (user["id"],)).fetchone()
    return {"theme": "light", "language": "zh-CN", "email_notifications": False, **(decode(row[0]) if row else {})}


class PreferencesPatch(BaseModel):
    theme: str | None = Field(default=None, max_length=30)
    language: str | None = Field(default=None, max_length=30)
    default_difficulty: str | None = Field(default=None, max_length=30)
    default_question_type: str | None = Field(default=None, max_length=30)
    email_notifications: bool | None = None


@router.put("/profile/preferences")
def save_preferences(body: PreferencesPatch, user: User):
    with db(write=True) as conn:
        row = conn.execute("SELECT payload FROM preferences WHERE user_id = ?", (user["id"],)).fetchone()
        settings = {**(decode(row[0]) if row else {}), **body.model_dump(exclude_none=True)}
        conn.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?)", (user["id"], encode(settings)))
    return ok()
