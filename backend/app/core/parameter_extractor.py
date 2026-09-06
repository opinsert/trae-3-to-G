import re
from typing import Optional

from app.models.schemas import ProcessCard, ToolInfo, Operation

# 保持 drawing/STL 旧调用方的兼容性；自然语言流程使用下方的严格字段集合。
REQUIRED_FIELDS = ['tool_diameter']
NATURAL_LANGUAGE_REQUIRED_FIELDS = [
    'product_name', 'process_name', 'process_number', 'version', 'equipment',
    'control_system', 'fixture', 'material', 'tool_name', 'tool_length',
    'tool_diameter', 'cutting_fluid', 'operations',
]

PROCESS_CARD_DEFAULTS = {
    'product_name': '未命名零件（仿真）',
    'process_name': '仿真加工',
    'process_number': 'SIM-001',
    'version': 'A',
    'equipment': '三轴加工中心（仿真）',
    'control_system': 'FANUC-compatible',
    'fixture': '未指定夹具（仿真）',
    'material': '未指定材料（仿真）',
    'tool_name': '立铣刀（仿真）',
    'tool_length': 75.0,
}

FIELD_LABELS = {
    'product_name': '产品名称',
    'process_name': '工序名称',
    'process_number': '工序编号',
    'version': '版本号',
    'equipment': '设备名称',
    'control_system': '数控系统',
    'fixture': '夹具名称',
    'material': '材料名称',
    'tool_name': '刀具名称',
    'tool_length': '刀具长度',
    'tool_diameter': '刀具直径',
    'cutting_fluid': '冷却方式',
    'operations': '操作步骤',
}

_OPERATION_PARAM_PATTERN = re.compile(
    r'\b(X_END|Y_END|WIDTH|HEIGHT|RAMP_X|RAMP_Y|PECK|STEP|X|Y|Z|F|S|D|R|P)\s*=\s*([+-]?\d+(?:\.\d+)?)',
    re.IGNORECASE,
)

# 叙述式工步：捕获「工步N ...」直到下一个「工步N」或文本末尾（可跨行、可出现在行中）
_WORDED_STEP_PATTERN = re.compile(r'工步\s*(\d+)\s*[.、)）:：]?\s*(.*?)(?=工步\s*\d+|$)', re.S)
# 「1号键槽铣刀（d=6mm，l=50mm，H01=0）」→ 刀具描述 + 括号规格
_TOOL_SPEC_PATTERN = re.compile(
    r'(\d+\s*号[^，。；：\s（(]{0,10}?刀|[^，。；：\s（(0-9]{1,10}?刀)\s*[（(]([^）)]*)[）)]'
)
_SPINDLE_PATTERN = re.compile(r'转速[：:]?\s*(\d+(?:\.\d+)?)\s*(?:r/min|rpm|转/分)?')
_FEED_PATTERN = re.compile(r'进给(?:速度)?[：:]?\s*[Ff]?[=：:]?\s*(\d+(?:\.\d+)?)\s*(?:mm/min)?')


def _parse_worded_step(sequence: int, segment: str) -> dict:
    seg = re.sub(r'\s*\n\s*', '', segment).strip().rstrip('。')

    equipment = ''
    label_match = re.search(r'(?:刀具|工艺装备|设备)[：:]\s*([^，,；;。]+)', seg)
    tool_match = _TOOL_SPEC_PATTERN.search(seg)
    if label_match:
        equipment = label_match.group(1).strip()
    elif tool_match:
        equipment = tool_match.group(0)

    # 参数扫描时先剔除刀具括号规格，避免 d=/l=/H01= 混入加工参数
    seg_for_params = seg.replace(tool_match.group(0), '〔刀〕', 1) if tool_match else seg
    parameters = [
        f'{key.upper()}={value}'
        for key, value in _OPERATION_PARAM_PATTERN.findall(seg_for_params)
    ]
    spindle = _SPINDLE_PATTERN.search(seg_for_params)
    feed = _FEED_PATTERN.search(seg_for_params)
    if spindle and not any(p.startswith('S=') for p in parameters):
        parameters.append(f'S={spindle.group(1)}')
    if feed and not any(p.startswith('F=') for p in parameters):
        parameters.append(f'F={feed.group(1)}')

    # content：截取到刀具/参数/转速中最先出现的位置
    cut_positions = [
        m.start() for m in [
            label_match, tool_match,
            _OPERATION_PARAM_PATTERN.search(seg_for_params),
            _SPINDLE_PATTERN.search(seg_for_params), _FEED_PATTERN.search(seg_for_params),
        ] if m
    ]
    content = (seg_for_params[:min(cut_positions)] if cut_positions else seg).strip(' ，,；;。至')

    remark_match = re.search(r'(?:工艺说明|备注)[：:]\s*(.+)$', seg)
    if remark_match:
        remark = remark_match.group(1).strip()
    else:
        # 兜底：剔除刀具/转速/进给后剩余的描述文字（如「每层切深2mm」）
        residue = seg_for_params
        for m in (spindle, feed):
            if m:
                residue = residue.replace(m.group(0), '', 1)
        residue = residue.replace('〔刀〕', '', 1)
        if content:
            residue = residue.replace(content, '', 1)
        residue = re.sub(r'(?:r/min|rpm|mm/min)', '', residue)
        remark = re.sub(r'^[，,；;。\s]+|[，,；;。\s]+$', '', re.sub(r'[，,；;]{2,}', '，', residue))

    return {
        'sequence': sequence,
        'content': content,
        'parameters': ', '.join(parameters),
        'equipment': equipment,
        'remark': remark,
    }


def extract_operations(text: str) -> list:
    # 叙述式「工步N …」格式（可跨行）优先
    if '工步' in text:
        worded = [
            _parse_worded_step(int(number), segment)
            for number, segment in _WORDED_STEP_PATTERN.findall(text)
            if segment.strip()
        ]
        if worded:
            return worded

    operations = []
    for line in text.splitlines():
        match = re.match(r'^\s*(\d+)[.、)）:\s]+(.+)$', line)
        if not match:
            continue
        raw_content = match.group(2).strip()
        parameters = [
            f'{key.upper()}={value}'
            for key, value in _OPERATION_PARAM_PATTERN.findall(raw_content)
        ]
        first_parameter = _OPERATION_PARAM_PATTERN.search(raw_content)
        content = raw_content[:first_parameter.start()].rstrip(' ，,；;') if first_parameter else raw_content
        equipment_match = re.search(r'(?:刀具|工艺装备|设备)[：:]\s*([^，,；;。]+)', raw_content)
        remark_match = re.search(r'(?:工艺说明|备注)[：:]\s*(.+)$', raw_content)
        operations.append({
            'sequence': int(match.group(1)),
            'content': content,
            'parameters': ', '.join(parameters),
            'equipment': equipment_match.group(1).strip() if equipment_match else '',
            'remark': remark_match.group(1).strip() if remark_match else '',
        })
    return operations


def _is_missing(value, numeric=False):
    if value is None:
        return True
    if numeric:
        return not isinstance(value, (int, float)) or value <= 0
    normalized = str(value).strip()
    return not normalized or normalized in {'未知', '未指定', '未填写', '仿真', 'None', 'null'}


def _merge_operations(previous: list, incoming: list) -> list:
    merged = {int(item.get('sequence', index + 1)): dict(item) for index, item in enumerate(previous or [])}
    for index, item in enumerate(incoming or [], 1):
        sequence = int(item.get('sequence', index))
        current = merged.get(sequence, {})
        merged[sequence] = {
            **current,
            **{key: value for key, value in item.items() if value not in (None, '')},
            'sequence': sequence,
        }
    return [merged[key] for key in sorted(merged)]


def merge_natural_language_draft(previous: Optional[dict], incoming: dict) -> dict:
    previous = previous or {}
    merged = dict(previous)
    fields = NATURAL_LANGUAGE_REQUIRED_FIELDS[:-1]
    for field in fields:
        value = incoming.get(field)
        if value not in (None, '', 0):
            merged[field] = value
    merged['operations'] = _merge_operations(previous.get('operations', []), incoming.get('operations', []))
    merged['field_sources'] = {**(previous.get('field_sources') or {}), **(incoming.get('field_sources') or {})}
    return merged


def natural_language_missing_fields(params: dict) -> list:
    missing = []
    for field in NATURAL_LANGUAGE_REQUIRED_FIELDS[:-1]:
        if _is_missing(params.get(field), numeric=field in {'tool_length', 'tool_diameter'}):
            missing.append(field)
    operations = params.get('operations') or []
    if not operations:
        missing.append('operations')
        return missing
    for operation in operations:
        sequence = operation.get('sequence', '?')
        for field in ('content', 'equipment', 'parameters', 'remark'):
            if _is_missing(operation.get(field)):
                missing.append(f'operations[{sequence}].{field}')
    return missing


class ParameterExtractor:
    """纯脚本（正则）提取器。按用户要求不使用 AI：确定性、毫秒级、离线可用。"""

    def extract(self, text: str) -> dict:
        return self._fallback_extract(text)

    def _fallback_extract(self, text: str) -> dict:
        result = {field: '' for field in NATURAL_LANGUAGE_REQUIRED_FIELDS if field != 'operations'}
        result.update({'tool_length': 0, 'tool_diameter': 0, 'operations': []})
        field_patterns = {
            'product_name': [r'产品名称[：:]\s*([^|，。\n]+)'],
            'process_name': [r'工序名称[：:]\s*([^|，。\n]+)'],
            'process_number': [r'工序编号[：:]\s*([^|，。\n]+)', r'编号[：:]\s*([^|，。\n]+)'],
            'version': [r'版本号?[：:]\s*([^|，。\n]+)'],
            'equipment': [r'设备(?:名称)?[：:]\s*([^|，。\n]+)'],
            'control_system': [r'数控系统[：:]\s*([^|，。\n]+)'],
            'fixture': [r'夹具(?:名称)?[：:]\s*([^|，。\n]+)'],
            'material': [r'材料(?:名称)?[：:]\s*([^|，。\n]+)'],
            'tool_name': [r'刀具名称[：:]\s*([^|，。\n]+)', r'刀具[：:]\s*([^|，。\n]+)'],
            'tool_length': [r'(?:刀具)?长度[：:]\s*(\d+(?:\.\d+)?)\s*(?:mm)?'],
            'tool_diameter': [r'(?:刀具)?直径[：:]\s*(\d+(?:\.\d+)?)\s*(?:mm)?'],
            'cutting_fluid': [r'(?:冷却方式|切削液)[：:]\s*([^|，。\n]+)'],
        }
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    result[field] = match.group(1).strip()
                    break
        for field in ('tool_length', 'tool_diameter'):
            try:
                result[field] = float(result[field]) if result[field] else 0
            except (ValueError, TypeError):
                result[field] = 0
        result['operations'] = self._extract_operations(text)
        self._backfill_tool_from_operations(result)
        return result

    def _backfill_tool_from_operations(self, result: dict) -> None:
        """顶层刀具字段缺失时，从首个工步的「N号x刀（d=…，l=…）」规格回填（单刀具流程）。"""
        if result['tool_name'] and result['tool_diameter'] and result['tool_length']:
            return
        for operation in result['operations']:
            match = _TOOL_SPEC_PATTERN.search(operation.get('equipment') or '')
            if not match:
                continue
            spec = match.group(2)
            diameter = re.search(r'\bd\s*=\s*(\d+(?:\.\d+)?)', spec, re.I)
            length = re.search(r'\bl\s*=\s*(\d+(?:\.\d+)?)', spec, re.I)
            if not result['tool_name']:
                result['tool_name'] = match.group(1).strip()
            if not result['tool_diameter'] and diameter:
                result['tool_diameter'] = float(diameter.group(1))
            if not result['tool_length'] and length:
                result['tool_length'] = float(length.group(1))
            return

    def _extract_value(self, text: str, start_idx: int) -> str:
        end_chars = ['：', ':', '，', ',', '。', '.', '\n', ' ', '、']
        value = ''
        i = start_idx
        while i < len(text):
            if text[i] in end_chars:
                break
            value += text[i]
            i += 1
        return value.strip()

    def _extract_operations(self, text: str) -> list:
        return extract_operations(text)

    def validate_parameters(self, params: dict, use_defaults: bool = True) -> tuple:
        if use_defaults:
            for field, value in PROCESS_CARD_DEFAULTS.items():
                if params.get(field) in (None, '', 0):
                    params[field] = value
        missing = []
        for field in REQUIRED_FIELDS:
            value = params.get(field, '')
            if value is None or value == '' or value == 0:
                missing.append(field)
        return len(missing) == 0, missing

    def _drawing_step_to_operation(self, step: dict, index: int) -> Operation:
        content = str(step.get('step_content') or step.get('content') or '').strip()
        parameters = str(step.get('parameters') or '').strip()
        feed_mm_min = step.get('feed_rate_mm_min')
        if feed_mm_min is None and step.get('feed_rate') is not None and step.get('spindle_speed') is not None:
            feed_mm_min = float(step['feed_rate']) * float(step['spindle_speed'])
        generated_values = []
        if not parameters:
            for key in ('X', 'Y', 'Z', 'X_END', 'Y_END', 'WIDTH', 'HEIGHT', 'D', 'R', 'P'):
                value = step.get(key) if key in step else step.get(key.lower())
                if value is not None:
                    generated_values.append(f'{key}={value}')
        if feed_mm_min is not None and not re.search(r'(^|,)\s*F\s*=', parameters, re.IGNORECASE):
            generated_values.append(f'F={feed_mm_min:.3f}')
        if step.get('spindle_speed') is not None and not re.search(r'(^|,)\s*S\s*=', parameters, re.IGNORECASE):
            generated_values.append(f'S={float(step["spindle_speed"]):.0f}')
        if generated_values:
            parameters = ', '.join(filter(None, [parameters, *generated_values]))
        return Operation(
            sequence=step.get('sequence', step.get('step', index)),
            content=content,
            parameters=parameters,
            equipment=step.get('equipment', step.get('tooling', '')),
            remark=step.get('remark', ''),
        )

    def to_process_card(self, params: dict) -> ProcessCard:
        return ProcessCard(
            product_name=params.get('product_name', ''),
            process_name=params.get('process_name', ''),
            process_number=params.get('process_number', ''),
            version=params.get('version', ''),
            equipment=params.get('equipment', ''),
            control_system=params.get('control_system', ''),
            fixture=params.get('fixture', ''),
            material=params.get('material', ''),
            cutting_fluid=params.get('cutting_fluid', ''),
            tool_info=ToolInfo(
                name=params.get('tool_name', ''),
                length=params.get('tool_length', 0),
                diameter=params.get('tool_diameter', 0),
            ),
        )

    def to_operations(self, ops_data: list) -> list:
        return [self._drawing_step_to_operation(op, idx) for idx, op in enumerate(ops_data, 1)]


def extract_parameters(text: str) -> dict:
    return ParameterExtractor().extract(text)


def validate_and_convert(params: dict, use_defaults: bool = True) -> tuple:
    extractor = ParameterExtractor()
    valid, missing = extractor.validate_parameters(params, use_defaults=use_defaults)
    if not valid:
        return None, missing
    process_card = extractor.to_process_card(params)
    operations = extractor.to_operations(params.get('operations', []))
    return (process_card, operations), None


def normalize_draft(params: dict) -> dict:
    extractor = ParameterExtractor()
    return {
        'process_card': extractor.to_process_card(params).model_dump(),
        'operations': [operation.model_dump() for operation in extractor.to_operations(params.get('operations', []))],
        'field_sources': params.get('field_sources') or {},
    }


def draft_to_params(draft: dict) -> dict:
    card = draft.get('process_card') or {}
    tool = card.get('tool_info') or {}
    return {
        'product_name': card.get('product_name', ''),
        'process_name': card.get('process_name', ''),
        'process_number': card.get('process_number', ''),
        'version': card.get('version', ''),
        'equipment': card.get('equipment', ''),
        'control_system': card.get('control_system', ''),
        'fixture': card.get('fixture', ''),
        'material': card.get('material', ''),
        'tool_name': tool.get('name', ''),
        'tool_length': tool.get('length', 0),
        'tool_diameter': tool.get('diameter', 0),
        'cutting_fluid': card.get('cutting_fluid', ''),
        'operations': draft.get('operations') or [],
        'field_sources': draft.get('field_sources') or {},
    }


def natural_language_missing_labels(params: dict) -> list:
    missing = []
    for field in natural_language_missing_fields(params):
        if field.startswith('operations['):
            match = re.match(r'operations\[(\d+)\]\.(.+)', field)
            sequence, name = match.groups()
            label = {'content': '操作内容', 'equipment': '刀具/工艺装备', 'parameters': '工艺参数/要求', 'remark': '工艺说明'}[name]
            missing.append({'path': field, 'label': f'工步{sequence} {label}', 'scope': 'operation', 'code': 'REQUIRED_FIELD', 'reason': f'工步{sequence}缺少{label}'})
        else:
            missing.append({'path': field, 'label': FIELD_LABELS[field], 'scope': 'process_card', 'code': 'REQUIRED_FIELD', 'reason': f'缺少{FIELD_LABELS[field]}'})
    return missing


def natural_language_value_errors(params: dict) -> list:
    errors = []
    tool_name = str(params.get('tool_name') or '').strip()
    for operation in params.get('operations') or []:
        equipment = str(operation.get('equipment') or '').strip()
        if equipment and tool_name and tool_name not in equipment:
            errors.append({'path': f"operations[{operation.get('sequence')}].equipment", 'label': '刀具/工艺装备', 'scope': 'operation', 'code': 'UNSUPPORTED_MULTI_TOOL', 'reason': '第一版自然语言流程只支持单刀具工序'})
        values = {key.upper(): float(value) for key, value in re.findall(r'([A-Z_]+)\s*=\s*([+-]?\d+(?:\.\d+)?)', operation.get('parameters', ''), re.I)}
        for key, value in values.items():
            if key in {'X', 'X_END', 'RAMP_X'} and not 0 <= value <= 200:
                errors.append({'path': f"operations[{operation.get('sequence')}].parameters", 'label': 'X坐标', 'scope': 'machine', 'code': 'OUT_OF_MACHINE_RANGE', 'reason': f'X={value}不在0..200范围内'})
            if key in {'Y', 'Y_END', 'RAMP_Y'} and not 0 <= value <= 200:
                errors.append({'path': f"operations[{operation.get('sequence')}].parameters", 'label': 'Y坐标', 'scope': 'machine', 'code': 'OUT_OF_MACHINE_RANGE', 'reason': f'Y={value}不在0..200范围内'})
            if key == 'Z' and not 0 <= value <= 100:
                errors.append({'path': f"operations[{operation.get('sequence')}].parameters", 'label': 'Z坐标', 'scope': 'machine', 'code': 'OUT_OF_MACHINE_RANGE', 'reason': f'Z={value}不在0..100范围内'})
            if key in {'STEP', 'PECK'} and value <= 0:
                errors.append({'path': f"operations[{operation.get('sequence')}].parameters", 'label': key, 'scope': 'operation', 'code': 'INVALID_PARAMETER_VALUE', 'reason': f'{key}必须大于0'})
    return errors
