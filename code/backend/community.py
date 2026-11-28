"""Read-only sharing of confirmed exercises and the associated discussions."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from accounts import User
from storage import db, decode, now


router = APIRouter(prefix="/v1")
EXCELLENT_THRESHOLD = 4
DISCUSSION_LIMIT = 2000
SQLITE_MAX_ID = 2**63 - 1

EXCELLENT_FILTER = """
    json_extract(q.payload, '$.teacher_status') = 'confirmed'
    AND json_extract(q.payload, '$.rating') >= :threshold
    AND EXISTS (
        SELECT 1 FROM json_each(q.payload, '$.confirmations') AS confirmation
        WHERE json_extract(confirmation.value, '$.version') = json_extract(q.payload, '$.version')
    )
"""
PUBLIC_SUMMARY = """
    q.id, q.user_id,
    json_extract(q.payload, '$.title') AS title,
    json_extract(q.payload, '$.content') AS content,
    json_extract(q.payload, '$.question_type') AS question_type,
    json_extract(q.payload, '$.grade') AS grade,
    json_extract(q.payload, '$.bloom_level') AS bloom_level,
    json_extract(q.payload, '$.created_at') AS created_at,
    json_extract(q.payload, '$.updated_at') AS updated_at,
    json_extract(q.payload, '$.version') AS version,
    json_extract(q.payload, '$.rating') AS max_teacher_rating,
    COALESCE(json_extract(q.payload, '$.illustration_url'), '') <> '' AS has_illustration
"""


class ExcellentQuestionSummary(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    question_type: str
    grade: str
    bloom_level: str
    created_at: str
    updated_at: str
    version: int
    max_teacher_rating: int
    has_illustration: bool


class PublishedConfirmation(BaseModel):
    version: int
    teacher_id: int
    teacher_name: str
    confirmed_at: str


class PublishedEvidence(BaseModel):
    source: str
    fragment_id: str
    index_version: str
    content: str


class ExcellentQuestionDetail(ExcellentQuestionSummary):
    difficulty: str
    knowledge_point: str
    thinking_tags: list[str] = Field(default_factory=list)
    options: str | None = None
    answer: str
    explanation: str
    illustration_url: str | None = None
    require_illustration: bool
    teacher_status: Literal["confirmed"]
    rating: int
    evidence: list[PublishedEvidence]
    kb_reason: str
    confirmations: list[PublishedConfirmation]


class ExcellentQuestionPage(BaseModel):
    items: list[ExcellentQuestionSummary]
    total: int
    page: int
    page_size: int


def require_excellent_question(conn, question_id: int) -> None:
    row = conn.execute(
        f"SELECT 1 FROM questions q WHERE q.id=:question_id AND {EXCELLENT_FILTER}",
        {"question_id": question_id, "threshold": EXCELLENT_THRESHOLD},
    ).fetchone()
    if row is None:
        raise HTTPException(404, "当前题目已不属于优秀定稿，请刷新列表")


@router.get("/excellent-questions/list", response_model=ExcellentQuestionPage)
def excellent_list(
    _user: User,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str = Query(default="", max_length=500),
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    keyword = keyword.strip().casefold()
    where_clause = EXCELLENT_FILTER
    order = "ASC" if sort_order == "asc" else "DESC"
    order_by = f"created_at {order}, q.id {order}"
    if sort_by in {"max_rating", "max_teacher_rating", "rating"}:
        order_by = f"max_teacher_rating {order}, {order_by}"

    with db() as conn:
        conn.execute("BEGIN")
        if keyword:
            conn.create_function("casefold", 1, str.casefold, deterministic=True)
            where_clause += """
                AND INSTR(CASEFOLD(
                    json_extract(q.payload, '$.title') || ' ' || json_extract(q.payload, '$.content')
                ), :keyword) > 0
            """
        params = {"threshold": EXCELLENT_THRESHOLD, "keyword": keyword}
        total = conn.execute(
            f"SELECT COUNT(*) FROM questions q WHERE {where_clause}", params,
        ).fetchone()[0]
        offset = (page - 1) * page_size
        if offset >= total:
            return {"items": [], "total": total, "page": page, "page_size": page_size}
        rows = conn.execute(
            f"""SELECT {PUBLIC_SUMMARY} FROM questions q WHERE {where_clause}
                ORDER BY {order_by} LIMIT :page_size OFFSET :offset""",
            {**params, "page_size": page_size, "offset": offset},
        ).fetchall()

    return {"items": [dict(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/excellent-questions/{question_id}", response_model=ExcellentQuestionDetail)
def excellent_detail(question_id: int, _user: User):
    with db() as conn:
        conn.execute("BEGIN")
        require_excellent_question(conn, question_id)
        row = conn.execute("SELECT payload FROM questions WHERE id=?", (question_id,)).fetchone()
        question = decode(row[0])
    confirmation = next(
        record for record in question["confirmations"] if record["version"] == question["version"]
    )
    fields = set(ExcellentQuestionDetail.model_fields.keys())
    return {
        **{key: value for key, value in question.items() if key in fields},
        "confirmations": [confirmation],
        "max_teacher_rating": question["rating"],
        "has_illustration": bool(question.get("illustration_url")),
    }


class DiscussionMessage(BaseModel):
    id: int
    question_id: int
    user_id: int
    username: str
    role: str
    parent_id: int | None
    reply_to_username: str | None
    content: str
    created_at: str


class DiscussionThread(DiscussionMessage):
    replies: list[DiscussionMessage] = Field(default_factory=list)


class DiscussionPage(BaseModel):
    items: list[DiscussionThread]
    total: int
    page: int
    page_size: int
    next_after_id: int | None


@router.get("/discussions/list", response_model=DiscussionPage)
def discussions(
    question_id: int,
    _user: User,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    after_id: int | None = Query(default=None, ge=0, le=SQLITE_MAX_ID),
):
    with db() as conn:
        conn.execute("BEGIN")
        require_excellent_question(conn, question_id)
        total = conn.execute(
            "SELECT COUNT(*) FROM discussions WHERE question_id=? AND parent_id IS NULL", (question_id,),
        ).fetchone()[0]
        offset = (page - 1) * page_size if after_id is None else 0
        rows = conn.execute(
            """SELECT d.*, u.username, u.role
               FROM discussions d JOIN users u ON d.user_id=u.id
               WHERE d.question_id=? AND d.parent_id IS NULL AND d.id>?
               ORDER BY d.id LIMIT ? OFFSET ?""",
            (question_id, after_id or 0, page_size + 1, min(offset, total)),
        ).fetchall()
        topics = {row["id"]: {**dict(row), "replies": []} for row in rows[:page_size]}
        next_after_id = rows[page_size - 1]["id"] if len(rows) > page_size else None
        if topics:
            placeholders = ", ".join("?" for _ in topics)
            replies = conn.execute(
                f"""SELECT d.*, u.username, u.role
                    FROM discussions d JOIN users u ON d.user_id=u.id
                    WHERE d.question_id=? AND d.parent_id IN ({placeholders})
                    ORDER BY d.id""",
                (question_id, *topics),
            )
            for reply in replies:
                topics[reply["parent_id"]]["replies"].append(dict(reply))

    return {
        "items": list(topics.values()),
        "total": total,
        "page": page,
        "page_size": page_size,
        "next_after_id": next_after_id,
    }


class DiscussionPost(BaseModel):
    question_id: int
    content: str
    parent_id: int | None = None


@router.post("/discussions/post", response_model=DiscussionThread)
def post_discussion(body: DiscussionPost, user: User):
    text = body.content.strip()
    if not text:
        raise HTTPException(422, "请填写讨论内容")
    if len(text) > DISCUSSION_LIMIT:
        raise HTTPException(422, f"讨论内容最多 {DISCUSSION_LIMIT} 字")
    with db(write=True) as conn:
        require_excellent_question(conn, body.question_id)
        parent_id = reply_name = None
        if body.parent_id is not None:
            parent = conn.execute(
                """SELECT d.id, d.parent_id, u.username
                   FROM discussions d JOIN users u ON d.user_id=u.id
                   WHERE d.id=? AND d.question_id=?""",
                (body.parent_id, body.question_id),
            ).fetchone()
            if parent is None:
                raise HTTPException(404, "回复的讨论已删除")
            parent_id = parent["parent_id"] or parent["id"]
            reply_name = parent["username"]
        created_at = now()
        cursor = conn.execute(
            """INSERT INTO discussions
               (question_id, user_id, parent_id, reply_to_username, content, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (body.question_id, user["id"], parent_id, reply_name, text, created_at),
        )
    return {
        "id": cursor.lastrowid,
        "question_id": body.question_id,
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "parent_id": parent_id,
        "reply_to_username": reply_name,
        "content": text,
        "created_at": created_at,
        "replies": [],
    }


class DiscussionDelete(BaseModel):
    discussion_id: int


@router.delete("/discussions/delete")
def delete_discussion(body: DiscussionDelete, user: User):
    with db(write=True) as conn:
        target = conn.execute(
            """SELECT d.user_id, q.user_id AS owner
               FROM discussions d JOIN questions q ON d.question_id=q.id WHERE d.id=?""",
            (body.discussion_id,),
        ).fetchone()
        if target is None:
            raise HTTPException(404, "讨论已删除")
        if user["role"] != "ADMIN" and user["id"] not in (target["user_id"], target["owner"]):
            raise HTTPException(403, "没有权限删除此讨论")
        conn.execute("DELETE FROM discussions WHERE id=?", (body.discussion_id,))
    return {"success": True, "message": "讨论已删除"}
