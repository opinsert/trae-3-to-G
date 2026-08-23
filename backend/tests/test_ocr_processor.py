import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1 import drawing
from app.api.v1.drawing import DrawingRequest
from app.core.ocr_processor import OCRProcessor
from app.utils.ai_gateway import parse_json_object


VALID_RESULT = {
    'process_name': '钻削',
    'process_card_number': '5',
    'material_grade': '45',
    'equipment': '钻床',
    'drawing_steps': [
        {
            'step': '1',
            'step_content': '钻孔 M8',
            'tooling': 'Φ7 麻花钻',
            'spindle_speed': '750 r/min',
            'cutting_speed': '16.49 m/min',
            'feed_rate': '0.2 mm/r',
        }
    ],
}


def test_invalid_provider_json_is_gateway_failure():
    with pytest.raises(RuntimeError, match='无效 JSON'):
        parse_json_object('not-json')


def test_visual_result_is_normalized_for_process_card_form():
    processor = OCRProcessor()
    with patch('app.core.ocr_processor.is_ai_gateway_configured', return_value=True), patch(
        'app.core.ocr_processor.request_chat_completion_json',
        new=AsyncMock(return_value=VALID_RESULT),
    ) as request_json:
        result = asyncio.run(processor.recognize('data:image/png;base64,ZmFrZQ=='))

    assert result['process_name'] == '钻削'
    assert result['drawing_steps'][0]['spindle_speed'] == 750
    assert result['drawing_steps'][0]['cutting_speed'] == 16490
    assert result['drawing_steps'][0]['feed_rate'] == 0.2
    assert result['drawing_steps'][0]['feed_rate_mm_min'] == 150
    assert result['steps'] == []
    assert request_json.await_args.kwargs['response_format'] == {'type': 'json_object'}


def test_missing_visual_configuration_fails_loudly():
    processor = OCRProcessor()
    with patch('app.core.ocr_processor.is_ai_gateway_configured', return_value=False):
        with pytest.raises(RuntimeError, match='视觉 OCR 未配置'):
            asyncio.run(processor.recognize('ZmFrZQ=='))


def test_empty_image_fails_before_request():
    processor = OCRProcessor()
    with pytest.raises(ValueError, match='图片数据不能为空'):
        asyncio.run(processor.recognize(''))


def test_visual_response_without_process_fields_is_rejected():
    processor = OCRProcessor()
    with patch('app.core.ocr_processor.is_ai_gateway_configured', return_value=True), patch(
        'app.core.ocr_processor.request_chat_completion_json',
        new=AsyncMock(return_value={'product_name': '只有产品名'}),
    ):
        with pytest.raises(ValueError, match='未识别到有效的工序卡字段'):
            asyncio.run(processor.recognize('ZmFrZQ=='))


def test_ocr_extract_returns_service_unavailable_when_not_configured():
    with patch.object(drawing, 'ocr_recognize', new=AsyncMock(side_effect=RuntimeError('视觉 OCR 未配置'))):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(drawing.ocr_extract(DrawingRequest(image='ZmFrZQ==')))

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == '视觉 OCR 未配置'


def test_ocr_extract_returns_bad_gateway_for_provider_failure():
    with patch.object(drawing, 'ocr_recognize', new=AsyncMock(side_effect=TimeoutError('timeout'))):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(drawing.ocr_extract(DrawingRequest(image='ZmFrZQ==')))

    assert exc_info.value.status_code == 502
    assert '视觉 OCR 请求失败' in exc_info.value.detail
