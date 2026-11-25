"""Physics illustration generation and revision prompts."""

import asyncio

from langgraph.graph import END
from langgraph.runtime import Runtime

from .common import IMAGE_PHASE_TIMEOUT, MODEL_TIMEOUTS, clean_text, role_failure, within_phase
from .model_gateway import GenerationError, draw
from .state import GenerationContext, GenerationState


def _drawing_prompt(draft, plan):
    blueprint = plan.get("illustration_plan")
    blueprint = blueprint if isinstance(blueprint, dict) else {}
    return (
        "生成一道中学物理习题的配图。使用简洁清晰、适合试卷印刷的构图。"
        "只绘制题干涉及的对象、关系和必要标注，核对方向、标量数值和单位，避免解题过程和答案。\n"
        f"题干：{draft['content']}\n类型：{clean_text(blueprint.get('image_type'), 50) or '物理模型图'}\n"
        f"绘图说明：{clean_text(blueprint.get('blueprint_text'), 4000) or '按题干绘制必要的空间关系和标注。'}"
    )


async def generate_illustration(
    state: GenerationState, runtime: Runtime[GenerationContext],
) -> GenerationState:
    context = runtime.context
    draft = state["draft"]
    round_number = state["image_round"]
    deadline = state.get("image_deadline")
    if deadline is None:
        deadline = asyncio.get_running_loop().time() + IMAGE_PHASE_TIMEOUT
    prompt = _drawing_prompt(draft["question"], draft["plan"])
    if round_number:
        prompt = f"{prompt}\n上轮核验修改意见：{state['image_feedback']}"
    context.update("配图生成" if round_number == 0 else "重绘配图", 70 + 13 * round_number, draft["attempt"] + round_number)

    try:
        image = await within_phase(
            draw(context.client, context.settings.get("illustrator", {}), prompt, timeout=MODEL_TIMEOUTS["illustrator"]),
            deadline,
        )
    except GenerationError as exc:
        return {
            "next_step": END,
            "image_warning": role_failure("illustrator", exc) + "文本草稿已保留，请在题库中补图。",
        }
    return {"image_deadline": deadline, "candidate_image": image, "next_step": "vision_reviewer"}
