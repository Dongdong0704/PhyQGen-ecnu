"""Shared generation limits, role names and response validation."""

import asyncio
import json
import re
from typing import Literal

from .model_gateway import GenerationError, RenderedResponseError


AgentRole = Literal["planner", "text_reviewer", "illustrator", "vision_reviewer"]

ROLE_LABELS = {
    "planner": "命题智能体",
    "text_reviewer": "文本审核智能体",
    "illustrator": "配图智能体",
    "vision_reviewer": "图文核验智能体",
}

TEXT_ROLES = ("planner", "text_reviewer")

ILLUSTRATION_ROLES = ("illustrator", "vision_reviewer")

MODEL_TIMEOUTS = {
    "planner": 120,
    "text_reviewer": 90,
    "illustrator": 180,
    "vision_reviewer": 120,
}

TEXT_PHASE_TIMEOUT = 300

IMAGE_PHASE_TIMEOUT = 330

QUESTION_TIMEOUT_SECONDS = TEXT_PHASE_TIMEOUT + IMAGE_PHASE_TIMEOUT + 30

MAX_TEXT_ATTEMPTS = 3

MAX_IMAGE_ROUNDS = 2


def parse_json_object(text):
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S | re.I)
    if fence:
        text = fence[1]
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError):
        raise RenderedResponseError("模型未返回有效的结构化结果。") from None
    if not isinstance(parsed, dict):
        raise RenderedResponseError("模型未返回有效的结构化结果。")
    return parsed


def clean_text(value, limit):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff]", value) or len(value) > limit:
        return ""
    return value


def parse_review(text):
    result = parse_json_object(text)
    passed = result.get("is_passed")
    if not isinstance(passed, bool):
        raise RenderedResponseError("审核模型未返回有效结论。")
    return passed, clean_text(result.get("revision_feedback"), 2000)


async def within_phase(call, deadline):
    try:
        return await asyncio.wait_for(call, deadline - asyncio.get_running_loop().time())
    except asyncio.TimeoutError:
        raise GenerationError("本阶段已达到处理时限，请稍后重试。") from None


def role_failure(role, error):
    return f"{ROLE_LABELS[role]}调用失败。{error}"
