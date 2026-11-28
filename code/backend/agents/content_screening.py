"""Local screening for explicit unsafe requests and generated question text."""

import re
import unicodedata

from .model_gateway import GenerationError


class ContentScreeningError(GenerationError):
    """A classroom suitability decision that should stop the generation run."""


_REVISION_GUIDANCE = "请改写为具体的物理知识点或安全的教学情境。"
REQUEST_REFUSAL = "命题要求不适合高中课堂。" + _REVISION_GUIDANCE
DRAFT_REFUSAL = "生成的内容不适合高中课堂，已拦截。请调整命题要求后重试。"

# Match requests for unsafe conduct, rather than isolated physics terms such as 爆炸 or 高压.
_NOT_PROHIBITION = r"(?<![不勿禁])(?<!不要)(?<!不得)(?<!禁止)(?<!严禁)(?<!防止)(?<!避免)(?<!无需)(?<!不应)"
_UNSAFE = re.compile(
    _NOT_PROHIBITION + r"(?:"
    # Instructions for dangerous acts or self-harm.
    r"(?:自制|制造|组装|改装|制作|配制|设计)(?:一个|一枚|一把|简易|小型|微型|真实|可用|的){0,4}"
    r"(?:炸弹|炸药|爆炸装置|爆炸物|武器|枪支|枪械|毒剂)"
    r"|(?:教(?:我|学生|同学|别人)(?:如何|怎样|怎么)?|(?<!教我)(?<!教学生)(?<!教同学)(?<!教别人)(?:如何|怎样|怎么))"
    r"(?:用[^。！？!?,，;；]{1,12})?"
    r"(?:杀人|杀害他人|伤害(?:同学|他人|自己)|自残|自杀|投毒|炸毁学校)"
    r"|(?:鼓励|诱导|逼迫)(?:他人|别人|学生|青少年|未成年人)?(?:自残|自杀|伤害自己)"
    # Unsuitable classroom content and explicit requests for private data.
    r"|(?:生成|写出|写|描述|加入|展示|提供|绘制)(?:一段|一些|详细的|露骨的){0,2}(?:色情内容|色情描写|露骨性描写|性行为细节)"
    r"|(?:辱骂|羞辱|骚扰)(?:某个|一名|特定的)?(?:同学|老师|学生|真实人物)"
    r"|(?:宣扬|煽动)(?:种族歧视|仇恨|校园霸凌|欺凌)"
    r"|(?:公开|泄露|公布|索取|提供)(?:某个|某位|同学的|别人的|他人的|学生的|老师的|真实的|真实){0,3}"
    r"(?:身份证号|手机号|家庭住址|私人联系方式)"
    # Instructions to override the planner or extract hidden data.
    r"|(?:忽略|无视|绕过)(?:之前|以上|先前|原有|前面|所有|系统|安全|的){0,5}(?:规则|指令|限制|审核|提示词)"
    r"|(?:输出|打印|泄露|显示|返回|告诉我)(?:你的|原始|完整的|完整|当前的|真实的|内部的|本系统的| ){0,4}"
    r"(?:系统提示词|api\s*(?:密钥|key)|访问令牌)"
    r"|\b(?:ignore|disregard)\s+(?:(?:all|the|prior|previous|above|system|safety)\s+){1,5}"
    r"(?:instructions|rules|policies|restrictions)\b"
    r"|\b(?:reveal|print|show|output)\s+(?:(?:your|the|full|original)\s+){0,3}(?:system prompt|api key|access token)\b"
    r"|\b(?:how to|steps to|instructions (?:to|for))\s+(?:build (?:a )?bomb|make (?:a )?bomb|kill yourself)\b"
    r")"
)


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = "".join(char for char in text if unicodedata.category(char) != "Cf")
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    return " ".join(text.split())


def check_generation_request(params: dict) -> None:
    """Reject explicit unsafe intent in either free-text field or across the pair."""
    topic = params.get("knowledge_point") or ""
    context = params.get("context") or ""
    for value, label in ((topic, "知识点 / 命题要求"), (context, "补充约束")):
        if _UNSAFE.search(_normalize(value)):
            raise ContentScreeningError(f"「{label}」含有不适合高中课堂的要求。{_REVISION_GUIDANCE}")
    if topic and context and _UNSAFE.search(_normalize(f"{topic}\n{context}")):
        raise ContentScreeningError(REQUEST_REFUSAL)


def check_planned_content(draft: dict, illustration_plan) -> None:
    """Stop flagged output before handing it to the reviewer or illustrator."""
    fields = list(draft.values())
    if isinstance(illustration_plan, dict):
        fields.extend(illustration_plan.get(key) for key in ("image_type", "blueprint_text"))
    if any(_UNSAFE.search(_normalize(value)) for value in fields if isinstance(value, str)):
        raise ContentScreeningError(DRAFT_REFUSAL)
