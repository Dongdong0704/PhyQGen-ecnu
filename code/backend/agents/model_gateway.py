"""Bounded OpenAI-compatible requests and validated illustration downloads."""

import asyncio
import base64
import binascii
import ipaddress
import json
import socket
from io import BytesIO

import httpx
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_TEXT_BYTES = 256 * 1024
MAX_IMAGE_RESPONSE = (MAX_IMAGE_BYTES * 4 // 3) + 64 * 1024
DNS_TIMEOUT = 8
CONNECT_TIMEOUT = 10
DOWNLOAD_TIMEOUT = 25
CHAT_PATH = "chat/completions"
IMAGE_PATH = "images/generations"
IMAGE_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


class GenerationError(Exception):
    """A message safe to display in the generation interface."""


class RenderedResponseError(GenerationError):
    """The model responded but did not provide usable output."""


def _parse_url(value):
    try:
        url = httpx.URL(value)
    except (httpx.InvalidURL, TypeError, ValueError):
        raise GenerationError("API 地址无效，请在个人中心检查模型配置。") from None
    if url.scheme not in {"https", "http"} or not url.host or url.userinfo or url.fragment:
        raise GenerationError("API 地址需为有效的 HTTP 或 HTTPS 地址。")
    return url


def _base_url(value):
    url = _parse_url((value or "").strip())
    if url.query:
        raise GenerationError("API 基础地址不能包含查询参数。")
    path = url.path.rstrip("/") or "/v1"
    return url.copy_with(path=path)


def _is_local(url):
    return url.host in {"localhost", "127.0.0.1", "::1"}


def _origin(url):
    return url.scheme, url.host, url.port or (443 if url.scheme == "https" else 80)


async def _connect_addresses(url, allow_local):
    if _is_local(url) and allow_local:
        return ["127.0.0.1" if url.host == "localhost" else url.host]
    if url.scheme != "https":
        raise GenerationError("远程模型及配图地址需使用 HTTPS。")
    try:
        records = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(
                url.raw_host.decode("ascii"), _origin(url)[2], type=socket.SOCK_STREAM,
            ),
            DNS_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise GenerationError(f"域名解析超过 {DNS_TIMEOUT} 秒，请检查 API 地址和本机 DNS。") from None
    except (OSError, UnicodeError, ValueError):
        raise GenerationError("服务地址无法解析，请检查 API 地址或网络。") from None
    addresses = sorted({record[4][0] for record in records}, key=lambda addr: (":" in addr, addr))
    if not addresses:
        raise GenerationError("服务地址无法解析，请检查 API 地址或网络。")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast:
            raise GenerationError("模型服务需使用公网 HTTPS 地址或本机回环地址。")
    return addresses[:3]


async def _request(client, method, url, *, body=None, key=None, limit, timeout, allow_local=False):
    async def connect(addresses, headers):
        for index, address in enumerate(addresses):
            # Preserve the provider's TLS identity while pinning the checked IP.
            request = client.build_request(
                method, url.copy_with(host=address), json=body, headers=headers,
                extensions={"sni_hostname": url.raw_host.decode("ascii")},
            )
            request.headers.pop("Cookie", None)
            try:
                return await client.send(request, stream=True)
            except (httpx.ConnectTimeout, httpx.ConnectError):
                # Only retry when no HTTP request was sent.
                if index == len(addresses) - 1:
                    raise

    async def read():
        addresses = await _connect_addresses(url, allow_local)
        headers = {"Host": url.netloc.decode("ascii"), "Accept-Encoding": "identity"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        response = await connect(addresses, headers)
        try:
            if response.status_code in (401, 403):
                raise GenerationError("模型服务拒绝请求，请检查 API 密钥和模型权限。")
            if response.status_code == 429:
                raise GenerationError("模型服务调用受限，请检查服务额度或稍后重试。")
            if response.status_code in (400, 404, 422):
                raise GenerationError("模型服务未接受请求，请检查 API 地址、模型名称与接口能力。")
            if response.status_code in (408, 504):
                raise GenerationError(f"模型服务或上游网关报告超时（HTTP {response.status_code}），请稍后重试。")
            if not response.is_success:
                raise GenerationError("模型服务暂时无法提供数据，请稍后重试。")
            data = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=64 * 1024):
                if len(data) + len(chunk) > limit:
                    raise RenderedResponseError("服务返回的数据超过大小限制。")
                data.extend(chunk)
            return bytes(data)
        finally:
            await response.aclose()

    try:
        return await asyncio.wait_for(read(), timeout)
    except httpx.ConnectTimeout:
        raise GenerationError(f"尝试连接时未能在 {CONNECT_TIMEOUT} 秒内建立连接，请检查 API 地址和本机网络。") from None
    except httpx.ConnectError:
        raise GenerationError("无法建立模型服务连接，请检查 API 地址、网络和 TLS 证书。") from None
    except httpx.WriteTimeout:
        raise GenerationError("上传请求超时，请检查网络后重试。") from None
    except httpx.ReadTimeout:
        raise GenerationError("等待模型服务响应超时，请稍后重试。") from None
    except asyncio.TimeoutError:
        raise GenerationError(f"模型服务在 {timeout} 秒内未返回完整结果，请稍后重试。") from None
    except (httpx.HTTPError, UnicodeError, ValueError):
        raise GenerationError("模型服务连接失败，请检查 API 地址、密钥和网络。") from None


def model_client():
    # The request URL can be an IP shared by different providers. Use a fresh
    # TLS connection for each request so Host and SNI always match its provider.
    return httpx.AsyncClient(
        trust_env=False, follow_redirects=False,
        timeout=httpx.Timeout(None, connect=CONNECT_TIMEOUT, write=30, pool=CONNECT_TIMEOUT),
        limits=httpx.Limits(max_keepalive_connections=0),
    )


def _endpoint(base, path):
    if base.path.endswith(f"/{path}"):
        return base
    if any(base.path.endswith(f"/{other}") for other in (CHAT_PATH, IMAGE_PATH)):
        raise GenerationError("API 地址的端点与当前智能体的接口类型不匹配。请填写 API 基础地址或对应的完整端点。")
    return base.copy_with(path=f"{base.path}/{path}")


async def _post(client, base, path, key, body, limit, timeout):
    raw = await _request(
        client, "POST", _endpoint(base, path), body=body, key=key,
        limit=limit, timeout=timeout, allow_local=True,
    )
    try:
        parsed = json.loads(raw)
    except (ValueError, RecursionError):
        raise RenderedResponseError("模型服务没有返回有效 JSON。") from None
    if not isinstance(parsed, dict):
        raise RenderedResponseError("模型服务返回的 JSON 结构不正确。")
    return parsed


def _model(config):
    model = config.get("model")
    if not model or not config.get("base_url"):
        raise GenerationError("请在个人中心配置 API 地址和模型。")
    return _base_url(config["base_url"]), model


async def chat(client, config, system_prompt, user_content, *, timeout):
    base, model = _model(config)
    response = await _post(
        client, base, CHAT_PATH, config.get("api_key"),
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        },
        MAX_TEXT_BYTES, timeout,
    )
    try:
        content = response["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(block["text"] for block in content if block.get("type") == "text")
        if isinstance(content, str) and content.strip():
            return content.strip()
    except (KeyError, IndexError, TypeError, AttributeError):
        pass
    raise RenderedResponseError("模型服务未返回可用的文本结果。")


async def draw(client, config, prompt, *, timeout):
    base, model = _model(config)
    response = await _post(
        client, base, IMAGE_PATH, config.get("api_key"),
        {"model": model, "prompt": prompt, "n": 1, "size": "1024x1024"},
        MAX_IMAGE_RESPONSE, timeout,
    )
    try:
        item = response["data"][0]
        if item.get("b64_json"):
            raw = base64.b64decode(item["b64_json"], validate=True)
        elif item.get("url"):
            url = _parse_url(item["url"])
            raw = await _request(
                client, "GET", url, limit=MAX_IMAGE_BYTES, timeout=DOWNLOAD_TIMEOUT,
                allow_local=_is_local(base) and _origin(base) == _origin(url),
            )
        else:
            raise ValueError
    except (KeyError, IndexError, TypeError, AttributeError, ValueError, binascii.Error):
        raise RenderedResponseError("绘图服务未返回可用的配图。") from None
    return await asyncio.to_thread(_image_data_url, raw)


def _image_data_url(raw):
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        raise RenderedResponseError("绘图服务返回的配图为空或超过大小限制。")
    try:
        with Image.open(BytesIO(raw), formats=list(IMAGE_TYPES)) as image:
            if image.width * image.height > 20_000_000:
                raise ValueError
            image.load()
            mime_type = IMAGE_TYPES[image.format]
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, SyntaxError):
        raise RenderedResponseError("绘图服务返回的文件无法作为配图打开。") from None
    return f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}"
