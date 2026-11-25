"""Real provider capability tests for each configured generation agent."""

from .common import MODEL_TIMEOUTS, ROLE_LABELS, role_failure
from .model_gateway import GenerationError, chat, draw, model_client


TEST_IMAGE = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAANUlEQVR4n"
    "O3QsQ0AMAzDsLT//9yeoCkbeYAN6LzZdZf3x0GSKEmUJEoSJYmSREmiJFGSaMoHo8QBPwYSAhsAAAAASUVORK5CYII="
)


async def test_connection(role: str, config: dict):
    if role not in ROLE_LABELS:
        raise GenerationError("未知的智能体。")
    prompt = "你正在执行模型连通性测试，请按用户的要求给出简短回复。"
    async with model_client() as client:
        try:
            if role == "illustrator":
                await draw(
                    client, config, "Draw a simple blue square on a white background.",
                    timeout=MODEL_TIMEOUTS[role],
                )
            elif role == "vision_reviewer":
                response = await chat(
                    client, config, prompt,
                    [
                        {"type": "text", "text": "图片主色是红色还是蓝色？仅回复 RED 或 BLUE。"},
                        {"type": "image_url", "image_url": {"url": TEST_IMAGE}},
                    ],
                    timeout=60,
                )
                if response.strip("`* .!。！\n").upper() not in {"RED", "红", "红色"}:
                    raise GenerationError("接口已响应，但未通过图片识别测试。请检查模型是否支持图片输入。")
            else:
                await chat(client, config, prompt, "请回复 OK。", timeout=60)
        except GenerationError as exc:
            raise GenerationError(role_failure(role, exc)) from None
