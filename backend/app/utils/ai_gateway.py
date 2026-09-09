import json
import logging

import aiohttp

from app.utils.config import is_configured_secret, settings

logger = logging.getLogger(__name__)


def is_ai_gateway_configured() -> bool:
    return (
        settings.vision_ocr_enabled
        and is_configured_secret(settings.vision_ocr_api_key)
        and bool(settings.vision_ocr_model)
    )


def parse_json_object(content: str) -> dict:
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1].rsplit('\n```', 1)[0]
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError('AI API 返回了无效 JSON') from error


async def request_chat_completion_json(
    messages: list,
    timeout: int = 40,
    response_format: dict = None,
) -> dict:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.vision_ocr_api_key}',
    }
    body = {
        'model': settings.vision_ocr_model,
        'messages': messages,
        # 诊断记录：poke2api 中转拒绝 temperature<1.0（0.1 直接 400），思考型
        # 模型不支持采样温度配置，故移除该字段交给服务端默认值。
        'max_tokens': 4096,
    }
    if response_format:
        body['response_format'] = response_format
    reasoning = (settings.ai_reasoning_effort or '').strip().lower()
    if reasoning in {'low', 'medium', 'high'}:
        # AI 思考强度（环境变量 AI_REASONING_EFFORT 控制）；模型不支持时服务端
        # 可能返回 400，下面会自动去掉该可选参数后重试，不中断主流程。
        body['reasoning_effort'] = reasoning
    url = settings.vision_ocr_base_url.rstrip('/') + '/v1/chat/completions'

    async def _post(payload: dict) -> dict:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status >= 400:
                    response.raise_for_status()
                return await response.json()

    try:
        result = await _post(body)
    except aiohttp.ClientResponseError as exc:
        # 模型/网关不支持 reasoning_effort / response_format 时去掉可选参数重试
        retry_body = dict(body)
        dropped = []
        if 'reasoning_effort' in retry_body:
            retry_body.pop('reasoning_effort', None)
            dropped.append('reasoning_effort')
        if response_format and 'response_format' in retry_body:
            retry_body.pop('response_format', None)
            dropped.append('response_format')
        if not dropped:
            raise
        logger.warning(
            'AI 请求失败(status=%s)，去掉 %s 后重试',
            getattr(exc, 'status', '?'),
            '、'.join(dropped),
        )
        result = await _post(retry_body)

    try:
        content = result['choices'][0]['message']['content']
    except (KeyError, IndexError) as error:
        raise ValueError(f'AI API 响应格式异常: {error}') from error
    return parse_json_object(content)
