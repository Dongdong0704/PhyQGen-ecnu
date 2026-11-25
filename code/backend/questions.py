"""Private question bank, revision history and teacher confirmation."""

import base64
import binascii
import io
import warnings
from collections import Counter

from fastapi import APIRouter, HTTPException
from PIL import Image
from pydantic import BaseModel, Field

from accounts import Teacher
from storage import db, decode, encode, now


router = APIRouter(prefix="/v1")
CONTENT_FIELDS = ("title", "content", "options", "answer", "explanation", "illustration_url")
CHOICE_TYPES = {"single_choice", "multiple_choice"}
IMAGE_TYPES = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP", "gif": "GIF", "bmp": "BMP"}
BUILTIN_IMAGES = {"/illustrations/newton.svg", "/illustrations/fall.svg", "/illustrations/circuit.svg"}


def version_snapshot(question, source):
    return {
        **{key: question[key] for key in CONTENT_FIELDS},
        "version": question["version"],
        "created_at": question["updated_at"],
        "source": source,
    }


def insert_question(conn, question):
    cursor = conn.execute("INSERT INTO questions (user_id, payload) VALUES (?, '')", (question["user_id"],))
    question["id"] = cursor.lastrowid
    write_question(conn, question)
    return question


def own_question(conn, user_id, question_id):
    row = conn.execute("SELECT payload FROM questions WHERE user_id=? AND id=?", (user_id, question_id)).fetchone()
    if row is None:
        raise HTTPException(404, "题目不存在，或不属于当前教师")
    return decode(row[0])


def write_question(conn, question):
    conn.execute("UPDATE questions SET payload=? WHERE id=?", (encode(question), question["id"]))


def parse_options(value):
    try:
        options = decode(value or "{}")
    except ValueError:
        return None
    if isinstance(options, dict) and all(isinstance(option, str) for option in options.values()):
        return options
    return None


def list_questions(conn, user_id):
    rows = conn.execute("SELECT payload FROM questions WHERE user_id=? ORDER BY id DESC", (user_id,))
    return [decode(row[0]) for row in rows]


def validate_illustration(value):
    if not value or value in BUILTIN_IMAGES:
        return
    header, separator, content = value.partition(",")
    prefix = "data:image/"
    format_name = header.removeprefix(prefix).removesuffix(";base64")
    if not separator or header != f"{prefix}{format_name};base64" or format_name not in IMAGE_TYPES:
        raise HTTPException(422, "请上传 PNG、JPEG、WebP、GIF 或 BMP 格式的图片")
    try:
        raw_image = base64.b64decode(content, validate=True)
        if len(raw_image) > 5 * 1024 * 1024:
            raise HTTPException(422, "配图大小不能超过5 MB")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw_image)) as image:
                if image.format != IMAGE_TYPES[format_name] or image.width * image.height > 20_000_000:
                    raise ValueError("invalid image type or size")
                image.verify()
    except (OSError, ValueError, SyntaxError, binascii.Error, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "图片无法预览，请重新上传") from None


class Revision(BaseModel):
    version: int = Field(ge=1)


class DraftPatch(Revision):
    title: str = Field(max_length=300)
    content: str = Field(max_length=50_000)
    options: str | None = Field(default=None, max_length=50_000)
    answer: str = Field(max_length=50_000)
    explanation: str = Field(max_length=50_000)
    illustration_url: str | None = Field(default=None, max_length=7_000_100)


class RatingPatch(BaseModel):
    rating: int = Field(ge=0, le=5)
    comment: str = Field(default="", max_length=10_000)


class ExportSelection(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=1000)


def check_version(question, version):
    if question["version"] != version:
        raise HTTPException(409, "题目已更新，请刷新后操作")


def is_confirmed(question):
    return question["teacher_status"] == "confirmed" and any(
        item["version"] == question["version"] for item in question["confirmations"]
    )


@router.get("/questions")
def questions(user: Teacher):
    with db() as conn:
        return list_questions(conn, user["id"])


@router.post("/questions/export")
def export_questions(selection: ExportSelection, user: Teacher):
    with db() as conn:
        conn.execute("BEGIN")
        questions = [own_question(conn, user["id"], question_id) for question_id in dict.fromkeys(selection.ids)]
    if not all(map(is_confirmed, questions)):
        raise HTTPException(409, "只能导出当前版本已由教师确认的题目")
    return questions


@router.get("/questions/{question_id}")
def question_detail(question_id: int, user: Teacher):
    with db() as conn:
        return own_question(conn, user["id"], question_id)


@router.patch("/questions/{question_id}")
def edit_question(question_id: int, patch: DraftPatch, user: Teacher):
    if patch.options and parse_options(patch.options) is None:
        raise HTTPException(422, "选项须为 JSON 对象，且每个选项的内容须为文本")
    if "illustration_url" in patch.model_fields_set:
        validate_illustration(patch.illustration_url)
    with db(write=True) as conn:
        question = own_question(conn, user["id"], question_id)
        check_version(question, patch.version)
        question.update(patch.model_dump(exclude={"version"}, exclude_unset=True))
        question.update(version=patch.version + 1, teacher_status="pending", updated_at=now())
        question["versions"].append(version_snapshot(question, "teacher"))
        write_question(conn, question)
    return question


@router.post("/questions/{question_id}/confirm")
def confirm_question(question_id: int, revision: Revision, user: Teacher):
    with db(write=True) as conn:
        question = own_question(conn, user["id"], question_id)
        check_version(question, revision.version)
        if is_confirmed(question):
            return question
        for field, label in (("title", "标题"), ("content", "题干"), ("answer", "答案"), ("explanation", "解析")):
            if not question[field].strip():
                raise HTTPException(422, f"请先补全{label}")
        if question["question_type"] in CHOICE_TYPES:
            choices = parse_options(question["options"])
            if not choices or len(choices) < 2 or any(not option.strip() for option in choices.values()):
                raise HTTPException(422, "请补全选择题选项")
        if question["require_illustration"] and not question["illustration_url"]:
            raise HTTPException(422, "此题要求配图，请先补充可预览的图片")
        validate_illustration(question["illustration_url"])
        confirmed_at = now()
        question["confirmations"].append({
            "version": question["version"],
            "teacher_id": user["id"],
            "teacher_name": user["username"],
            "confirmed_at": confirmed_at,
        })
        question.update(teacher_status="confirmed", updated_at=confirmed_at)
        write_question(conn, question)
    return question


@router.post("/questions/{question_id}/rating")
def rate_question(question_id: int, patch: RatingPatch, user: Teacher):
    with db(write=True) as conn:
        question = own_question(conn, user["id"], question_id)
        question.update(patch.model_dump())
        write_question(conn, question)
    return question


@router.delete("/questions/{question_id}")
def delete_question(question_id: int, user: Teacher):
    with db(write=True) as conn:
        own_question(conn, user["id"], question_id)
        conn.execute("DELETE FROM questions WHERE id=? AND user_id=?", (question_id, user["id"]))
    return {}


@router.get("/overview/stats")
def overview_stats(user: Teacher):
    with db() as conn:
        conn.execute("BEGIN")
        questions = list_questions(conn, user["id"])
        task_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user["id"],)).fetchone()[0]
    confirmed_count = sum(map(is_confirmed, questions))
    return {
        "total_questions": len(questions),
        "pending_questions": len(questions) - confirmed_count,
        "confirmed_questions": confirmed_count,
        "total_tasks": task_count,
        "recent_questions": questions[:5],
        **{
            f"questions_by_{field}": dict(Counter(str(q[source] or "未评分") for q in questions))
            for field, source in (
                ("type", "question_type"), ("bloom", "bloom_level"), ("grade", "grade"),
                ("knowledge", "knowledge_point"), ("rating", "rating"),
            )
        },
    }
