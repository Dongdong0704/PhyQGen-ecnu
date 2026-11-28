"""Build per-question working memory and recall relevant private question history."""

import logging
import sqlite3

from typing_extensions import TypedDict

from storage import db

from .state import GenerationState


logger = logging.getLogger(__name__)


class PromptMemory(TypedDict):
    episodes: list[dict[str, str]]
    examples: list[dict[str, str]]


def start_working_memory(
    params: dict, requirements: dict, evidence: list[dict], memory: PromptMemory | None,
) -> GenerationState:
    payload = {
        "命题要求": requirements,
        "资料片段": evidence,
        "批量命题提示": "根据本题序号选择不同情境、数值或设问角度。",
    }
    if memory and memory["episodes"]:
        payload["近期命题片段"] = memory["episodes"]
    if memory and memory["examples"]:
        payload["教师已确认的参考片段"] = memory["examples"]
    return {
        "params": params,
        "requirements": requirements,
        "planner_payload": payload,
        "text_attempt": 0,
        "image_round": 0,
    }


def recall_episodes(
    conn: sqlite3.Connection, user_id: int, task_id: str, params: dict,
) -> list[dict[str, str]]:
    """Recall original generated drafts, with already saved batch siblings first."""
    rows = conn.execute(
        """
        SELECT substr(json_extract(q.payload, '$.versions[0].title'), 1, 120) AS "标题",
               substr(json_extract(q.payload, '$.versions[0].content'), 1, 240) AS "题干节选"
        FROM questions AS q
        JOIN tasks AS t ON t.id = json_extract(q.payload, '$.task_id') AND t.user_id = q.user_id
        WHERE q.user_id = ?
          AND json_extract(q.payload, '$.grade') = ?
          AND json_extract(q.payload, '$.knowledge_point') = ?
          AND json_extract(q.payload, '$.versions[0].source') = 'system'
          AND (? OR t.id = ?)
        ORDER BY (t.id = ?) DESC, q.id DESC
        LIMIT 4
        """,
        (user_id, params["grade"], params["knowledge_point"], bool(params.get("use_kb")), task_id, task_id),
    )
    return [dict(row) for row in rows]


def recall_confirmed_examples(
    conn: sqlite3.Connection, user_id: int, params: dict,
) -> list[dict[str, str]]:
    """Recall solution excerpts only while their current version remains teacher-confirmed."""
    rows = conn.execute(
        """
        SELECT substr(json_extract(q.payload, '$.title'), 1, 120) AS "标题",
               substr(json_extract(q.payload, '$.content'), 1, 240) AS "题干节选",
               substr(json_extract(q.payload, '$.explanation'), 1, 360) AS "解析节选"
        FROM questions AS q
        JOIN tasks AS t ON t.id = json_extract(q.payload, '$.task_id') AND t.user_id = q.user_id
        WHERE q.user_id = ?
          AND json_extract(q.payload, '$.grade') = ?
          AND json_extract(q.payload, '$.knowledge_point') = ?
          AND json_extract(q.payload, '$.question_type') = ?
          AND COALESCE(json_extract(q.payload, '$.require_illustration'), 0) = ?
          AND json_extract(q.payload, '$.teacher_status') = 'confirmed'
          AND EXISTS (
              SELECT 1 FROM json_each(q.payload, '$.confirmations') AS confirmation
              WHERE json_extract(confirmation.value, '$.version') = json_extract(q.payload, '$.version')
                AND json_extract(confirmation.value, '$.teacher_id') = q.user_id
          )
        ORDER BY json_extract(q.payload, '$.updated_at') DESC, q.id DESC
        LIMIT 2
        """,
        (user_id, params["grade"], params["knowledge_point"], params["question_type"],
         bool(params.get("require_illustration"))),
    )
    return [dict(row) for row in rows]


def load_prompt_memory(user_id: int, task_id: str, params: dict) -> PromptMemory:
    """Read both memory sources in one snapshot and let generation proceed on read errors."""
    try:
        with db() as conn:
            conn.execute("BEGIN")
            episodes = recall_episodes(conn, user_id, task_id, params)
            examples = recall_confirmed_examples(conn, user_id, params) if params.get("use_kb") else []
    except sqlite3.Error:
        logger.warning("Question memory is unavailable")
        return {"episodes": [], "examples": []}
    return {"episodes": episodes, "examples": examples}
