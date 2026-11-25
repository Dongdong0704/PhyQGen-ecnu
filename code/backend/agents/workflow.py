"""Compile and run the LangGraph workflow for one question."""

import asyncio
from collections.abc import Callable

from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context

from knowledge import retrieve_evidence

from .illustrator import generate_illustration
from .model_gateway import model_client
from .planner import build_requirements, plan_question
from .state import GenerationContext, GenerationState
from .text_reviewer import review_text
from .vision_reviewer import review_illustration


def _route_after_text(state: GenerationState) -> str:
    if state["next_step"] == "text_complete":
        return "illustrator" if state["params"].get("require_illustration") else END
    return state["next_step"]


def _route_after_image(state: GenerationState) -> str:
    return state["next_step"]


question_graph = (
    StateGraph(GenerationState, context_schema=GenerationContext)
    .add_node("planner", plan_question)
    .add_node("text_reviewer", review_text)
    .add_node("illustrator", generate_illustration)
    .add_node("vision_reviewer", review_illustration)
    .add_edge(START, "planner")
    .add_conditional_edges("planner", _route_after_text, ["planner", "text_reviewer", "illustrator", END])
    .add_conditional_edges("text_reviewer", _route_after_text, ["planner", "illustrator", END])
    .add_conditional_edges("illustrator", _route_after_image, ["vision_reviewer", END])
    .add_conditional_edges("vision_reviewer", _route_after_image, ["illustrator", END])
    .compile()
)


async def generate_question(params: dict, settings: dict, update: Callable[[str, int, int], None], index: int) -> dict:
    evidence = []
    if params.get("use_kb"):
        update("知识检索", 12, 1)
        try:
            evidence = await asyncio.to_thread(retrieve_evidence, params["knowledge_point"], params["grade"])
            kb_reason = "命题时已提供以下知识库参考片段。" if evidence else "知识库未检索到相关资料，已按常规流程命题。"
        except (OSError, ValueError, KeyError, TypeError):
            kb_reason = "知识库检索暂不可用，已按常规流程命题。"
    else:
        kb_reason = "本次已关闭知识库增强。"

    requirements = build_requirements(params, index)
    initial_state: GenerationState = {
        "params": params,
        "requirements": requirements,
        "planner_payload": {
            "命题要求": requirements,
            "资料片段": evidence,
            "批量命题提示": "根据本题序号选择不同情境、数值或设问角度。",
        },
        "text_attempt": 0,
        "image_round": 0,
    }
    async with model_client() as client:
        with tracing_context(enabled=False):
            result = await question_graph.ainvoke(
                initial_state, context=GenerationContext(client=client, settings=settings, update=update),
            )

    draft = {
        **result["draft"]["question"],
        "illustration_url": result.get("illustration_url"),
        "evidence": evidence,
        "kb_reason": kb_reason,
    }
    warning = result.get("text_warning", "") + result.get("image_warning", "")
    if warning:
        draft["error"] = warning
    return draft
