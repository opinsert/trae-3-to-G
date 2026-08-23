import re

from app.utils.ai_gateway import is_ai_gateway_configured, request_chat_completion_json
from app.utils.config import settings


def _empty_ocr_result(**overrides) -> dict:
    result = {
        'product_name': '',
        'process_name': '',
        'process_number': '',
        'version': '',
        'equipment': '',
        'control_system': '',
        'fixture': '',
        'material': '',
        'tool_name': '',
        'tool_length': 0,
        'tool_diameter': 0,
        'steps': [],
        'workshop': '',
        'process_card_number': '',
        'material_grade': '',
        'blank_type': '',
        'blank_size': '',
        'blank_available_pieces': None,
        'pieces_per_machine': None,
        'equipment_model': '',
        'equipment_no': '',
        'simultaneous_pieces': None,
        'fixture_no': '',
        'cutting_fluid': '',
        'station_tool_no': '',
        'station_tool_name': '',
        'preparation_time': None,
        'unit_time': None,
        'drawing_steps': [],
    }
    result.update(overrides)
    return result


class OCRProcessor:
    async def recognize(self, image_data: str) -> dict:
        if not image_data or not image_data.strip():
            raise ValueError('图片数据不能为空')
        if not is_ai_gateway_configured():
            raise RuntimeError('视觉 OCR 未配置，请设置有效的 VISION_OCR_API_KEY 和视觉模型')

        image_url = image_data if image_data.startswith('data:image/') else f'data:image/png;base64,{image_data}'
        parsed = await request_chat_completion_json(
            [
                {
                    'role': 'system',
                    'content': '你是专业的机械加工工序卡OCR与结构化信息提取助手，只输出JSON。',
                },
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': self._build_vision_prompt()},
                        {'type': 'image_url', 'image_url': {'url': image_url}},
                    ],
                },
            ],
            timeout=settings.vision_ocr_timeout,
            response_format={'type': 'json_object'},
        )
        normalized = self._normalize_vision_result(parsed)
        if not self._has_valid_ocr_data(normalized):
            raise ValueError('视觉模型未识别到有效的工序卡字段')
        return normalized

    def _build_vision_prompt(self) -> str:
        return '''请识别图片中的机械加工工序卡/工艺卡表格，并只返回一个合法JSON对象。不要输出Markdown、解释或代码块。

字段必须包含：
{
  "product_name": "",
  "process_name": "",
  "process_number": "",
  "version": "",
  "equipment": "",
  "control_system": "",
  "fixture": "",
  "material": "",
  "tool_name": "",
  "tool_length": 0,
  "tool_diameter": 0,
  "workshop": "",
  "process_card_number": "",
  "material_grade": "",
  "blank_type": "",
  "blank_size": "",
  "blank_available_pieces": null,
  "pieces_per_machine": null,
  "equipment_model": "",
  "equipment_no": "",
  "simultaneous_pieces": null,
  "fixture_no": "",
  "cutting_fluid": "",
  "station_tool_no": "",
  "station_tool_name": "",
  "preparation_time": null,
  "unit_time": null,
  "drawing_steps": [
    {
      "step": 1,
      "step_content": "",
      "tooling": "",
      "spindle_speed": null,
      "cutting_speed": null,
      "feed_rate": null,
      "depth_of_cut": null,
      "feed_count": null,
      "machine_time": null,
      "auxiliary_time": null,
      "remark": ""
    }
  ],
  "steps": []
}

要求：
1. 保持字段名完全一致。
2. 未识别的文本字段填空字符串。
3. 未识别的数字字段填null；tool_length和tool_diameter未识别时填0。
4. drawing_steps按工步表逐行提取，数值字段只保留数字，不要带单位。
5. steps保留为空数组即可，除非图片中有旧格式工步信息。
6. 不要猜测图片中没有的信息。'''

    def _has_valid_ocr_data(self, parsed: dict) -> bool:
        if not isinstance(parsed, dict):
            return False
        drawing_steps = parsed.get('drawing_steps', [])
        return any([
            parsed.get('process_name'),
            parsed.get('process_card_number'),
            parsed.get('material_grade'),
            parsed.get('equipment'),
            parsed.get('equipment_model'),
            isinstance(drawing_steps, list) and len(drawing_steps) > 0,
        ])

    def _normalize_vision_result(self, parsed: dict) -> dict:
        normalized = self._ensure_full_fields(parsed if isinstance(parsed, dict) else {})
        normalized['tool_length'] = self._to_number(normalized.get('tool_length'), 0)
        normalized['tool_diameter'] = self._to_number(normalized.get('tool_diameter'), 0)

        for field in [
            'blank_available_pieces', 'pieces_per_machine', 'simultaneous_pieces',
            'preparation_time', 'unit_time',
        ]:
            normalized[field] = self._to_number(normalized.get(field), None)

        normalized['drawing_steps'] = self._normalize_drawing_steps(normalized.get('drawing_steps'))
        normalized['steps'] = normalized.get('steps') if isinstance(normalized.get('steps'), list) else []
        return normalized

    def _normalize_drawing_steps(self, steps: list) -> list:
        if not isinstance(steps, list):
            return []

        normalized_steps = []
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            normalized_step = {
                'step': self._to_int(step.get('step'), index + 1),
                'step_content': str(step.get('step_content') or step.get('content') or ''),
                'tooling': str(step.get('tooling') or step.get('equipment') or ''),
                'spindle_speed': self._to_number(step.get('spindle_speed'), None),
                'cutting_speed': (
                    self._to_number(step.get('cutting_speed'), None) * 1000
                    if self._to_number(step.get('cutting_speed'), None) is not None
                    else None
                ),
                'feed_rate': self._to_number(step.get('feed_rate'), None),
                'feed_rate_mm_min': (
                    self._to_number(step.get('feed_rate'), None) * self._to_number(step.get('spindle_speed'), None)
                    if self._to_number(step.get('feed_rate'), None) is not None
                    and self._to_number(step.get('spindle_speed'), None) is not None
                    else None
                ),
                'depth_of_cut': self._to_number(step.get('depth_of_cut'), None),
                'feed_count': self._to_number(step.get('feed_count'), None),
                'machine_time': self._to_number(step.get('machine_time'), None),
                'auxiliary_time': self._to_number(step.get('auxiliary_time'), None),
                'remark': str(step.get('remark') or ''),
            }
            if any(
                normalized_step.get(field) not in (None, '')
                for field in normalized_step
                if field != 'step'
            ):
                normalized_steps.append(normalized_step)
        return normalized_steps

    def _to_number(self, value, default=None):
        if value is None or value == '':
            return default
        if isinstance(value, (int, float)):
            return value
        match = re.search(r'-?\d+(?:\.\d+)?', str(value).strip())
        if not match:
            return default
        number = float(match.group(0))
        return int(number) if number.is_integer() else number

    def _to_int(self, value, default=0):
        number = self._to_number(value, default)
        try:
            return int(number)
        except (ValueError, TypeError):
            return default

    def _ensure_full_fields(self, parsed: dict) -> dict:
        normalized = _empty_ocr_result()
        normalized.update({key: value for key, value in parsed.items() if key in normalized})
        return normalized


ocr_processor = OCRProcessor()


async def ocr_recognize(image_data: str) -> dict:
    return await ocr_processor.recognize(image_data)
