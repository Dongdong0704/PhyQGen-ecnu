"""Per-question graph state and runtime dependencies."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from httpx import AsyncClient
from typing_extensions import TypedDict


class PlannedDraft(TypedDict):
    question: dict
    plan: dict
    attempt: int


class GenerationState(TypedDict, total=False):
    params: dict
    requirements: dict
    planner_payload: dict
    text_deadline: float
    text_attempt: int
    draft: PlannedDraft
    text_warning: str
    image_deadline: float
    image_round: int
    image_feedback: str
    candidate_image: str
    illustration_url: str
    image_warning: str
    next_step: Literal[
        "planner", "text_reviewer", "text_complete",
        "illustrator", "vision_reviewer", "__end__",
    ]


@dataclass(frozen=True)
class GenerationContext:
    client: AsyncClient
    settings: dict
    update: Callable[[str, int, int], None]
