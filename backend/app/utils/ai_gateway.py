import json

import aiohttp

from app.utils.config import is_configured_secret, settings


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
    url = settings.vision_ocr_base_url.rstrip('/') + '/v1/chat/completions'

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.post(url, headers=headers, json=body) as response:
            if response.status >= 400 and response_format:
                body.pop('response_format', None)
                async with session.post(url, headers=headers, json=body) as retry_response:
                    retry_response.raise_for_status()
                    result = await retry_response.json()
            else:
                response.raise_for_status()
                result = await response.json()

    try:
        content = result['choices'][0]['message']['content']
    except (KeyError, IndexError) as error:
        raise ValueError(f'AI API 响应格式异常: {error}') from error
    return parse_json_object(content)
