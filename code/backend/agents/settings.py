"""Independent, encrypted model settings for each generation agent."""

import os
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from accounts import Teacher
from storage import DATA_DIR, db, decode, encode

from .common import AgentRole, ILLUSTRATION_ROLES, ROLE_LABELS, TEXT_ROLES


router = APIRouter(prefix="/v1/profile/model-settings")


class AgentSettings(BaseModel):
    base_url: str = Field(max_length=500)
    model: str = Field(max_length=200)
    api_key: str | None = Field(default=None, max_length=1024)


def load_key():
    key_path = DATA_DIR / "model-settings.key"
    try:
        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as key_file:
            key_file.write(Fernet.generate_key())
    except FileExistsError:
        pass
    if os.name != "nt":
        key_path.chmod(0o600)
    return Fernet(key_path.read_bytes())


def save_model(conn, user_id, config):
    if not config:
        conn.execute("DELETE FROM model_settings WHERE user_id = ?", (user_id,))
        return
    encrypted = load_key().encrypt(encode({"roles": config}).encode()).decode()
    conn.execute("INSERT OR REPLACE INTO model_settings VALUES (?, ?)", (user_id, encrypted))


def migrate_legacy_model(settings):
    # Copy existing associations into independent records so later edits are role-local.
    base_url = settings.get("base_url", "")
    text_model = settings.get("text_model", "")
    api_key = settings.get("api_key")
    text_config = {"base_url": base_url, "model": text_model, "api_key": api_key, "inherited": True}
    roles = {}
    if base_url and text_model:
        roles = {
            "planner": dict(text_config),
            "text_reviewer": dict(text_config),
            "vision_reviewer": {**text_config, "model": settings.get("vision_model") or text_model},
        }
    image_model = settings.get("image_model")
    image_endpoint = settings.get("image_base_url") or base_url
    if image_endpoint and image_model:
        image_key = settings.get("image_api_key")
        roles["illustrator"] = {
            "base_url": image_endpoint, "model": image_model,
            "api_key": image_key or (api_key if image_endpoint == base_url else None),
            "inherited": True,
        }
    return roles


def read_model(conn, user_id):
    row = conn.execute("SELECT config FROM model_settings WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {}
    settings = decode(load_key().decrypt(row[0].encode()).decode())
    if "roles" in settings:
        return settings["roles"]
    return migrate_legacy_model(settings)


def is_configured(config):
    return bool(config.get("base_url") and config.get("model"))


def missing_roles(config, require_illustration=False):
    required_roles = TEXT_ROLES + ILLUSTRATION_ROLES if require_illustration else TEXT_ROLES
    return [ROLE_LABELS[role] for role in required_roles if not is_configured(config.get(role, {}))]


def model_status(config):
    roles = {}
    for role in ROLE_LABELS:
        values = config.get(role, {})
        roles[role] = {
            "base_url": values.get("base_url", ""),
            "model": values.get("model", ""),
            "has_api_key": bool(values.get("api_key")),
            "configured": is_configured(values),
            "inherited": bool(values.get("inherited")),
        }
    return {
        "roles": roles,
        "configured": all(roles[role]["configured"] for role in TEXT_ROLES),
        "illustration_configured": all(roles[role]["configured"] for role in ILLUSTRATION_ROLES),
    }


def checked_endpoint(value, role):
    try:
        endpoint = urlsplit(value)
        if (
            endpoint.scheme in {"http", "https"} and endpoint.hostname and not endpoint.username
            and not endpoint.password and not endpoint.query and not endpoint.fragment
            and not endpoint.netloc.endswith(":") and (endpoint.port is None or endpoint.port > 0)
            and not any(ch.isspace() for ch in value)
            and not any(ch in "\\%" for ch in endpoint.netloc)
        ):
            if endpoint.scheme == "https" or endpoint.hostname in {"localhost", "127.0.0.1", "::1"}:
                base_url = value.rstrip("/")
                wrong_path = "/chat/completions" if role == "illustrator" else "/images/generations"
                if base_url.endswith(wrong_path):
                    interface = "图像生成" if role == "illustrator" else "对话补全"
                    raise HTTPException(422, f"该智能体需要{interface}接口，请填写正确的 API 基础地址或完整接口地址")
                return base_url
    except ValueError:
        pass
    raise HTTPException(422, "API 地址须为有效的 HTTPS 地址，本机服务可用 HTTP。地址中请勿包含密钥或查询参数")


def role_config(body, existing, role):
    base_url = body.base_url.strip()
    model = body.model.strip()
    if not base_url or not model:
        raise HTTPException(422, "请填写该智能体的 API 地址与模型名称")
    base_url = checked_endpoint(base_url, role)
    if body.api_key is None:
        api_key = existing.get("api_key")
        if api_key and base_url != existing["base_url"]:
            raise HTTPException(422, "API 地址已改，请为该智能体重新输入密钥，或清除原密钥")
    else:
        api_key = body.api_key.strip()
    return {"base_url": base_url, "model": model, "api_key": api_key}


@router.get("")
def get_model_settings(user: Teacher):
    with db() as conn:
        return model_status(read_model(conn, user["id"]))


@router.put("/{role}")
def put_model_settings(role: AgentRole, body: AgentSettings, user: Teacher):
    with db(write=True) as conn:
        config = read_model(conn, user["id"])
        config[role] = role_config(body, config.get(role, {}), role)
        save_model(conn, user["id"], config)
    return model_status(config)


@router.delete("/{role}")
def delete_model_settings(role: AgentRole, user: Teacher):
    with db(write=True) as conn:
        config = read_model(conn, user["id"])
        config.pop(role, None)
        save_model(conn, user["id"], config)
    return model_status(config)


@router.post("/{role}/test")
async def check_model_settings(role: AgentRole, body: AgentSettings, user: Teacher):
    from .connections import test_connection
    from .model_gateway import GenerationError

    with db() as conn:
        config = read_model(conn, user["id"])
        settings = role_config(body, config.get(role, {}), role)
    try:
        await test_connection(role, settings)
    except GenerationError as exc:
        raise HTTPException(502, str(exc)) from None
    return {"message": f"{ROLE_LABELS[role]}测试成功"}
