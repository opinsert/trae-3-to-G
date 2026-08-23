import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.parameter_extractor import (
    ParameterExtractor,
    extract_parameters,
    validate_and_convert,
    REQUIRED_FIELDS,
)
from app.models.schemas import ProcessCard, ToolInfo, Operation


class TestFallbackExtract:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_extracts_product_name(self):
        text = "产品名称：铝合金外壳\n工序名称：铣削"
        result = self.extractor._fallback_extract(text)
        assert result['product_name'] == '铝合金外壳'

    def test_extracts_process_name(self):
        text = "工序名称：平面铣削\n工序编号：OP001"
        result = self.extractor._fallback_extract(text)
        assert result['process_name'] == '平面铣削'

    def test_extracts_process_number(self):
        text = "工序编号：OP001\n版本号：V1.0"
        result = self.extractor._fallback_extract(text)
        assert result['process_number'] == 'OP001'

    def test_extracts_version(self):
        text = "版本号：V2.0\n设备名称：CNC"
        result = self.extractor._fallback_extract(text)
        assert result['version'] == 'V2.0'

    def test_extracts_equipment(self):
        text = "设备名称：CNC加工中心\n数控系统：FANUC"
        result = self.extractor._fallback_extract(text)
        assert result['equipment'] == 'CNC加工中心'

    def test_extracts_control_system(self):
        text = "数控系统：FANUC 0i\n夹具名称：虎钳"
        result = self.extractor._fallback_extract(text)
        assert result['control_system'] == 'FANUC 0i'

    def test_extracts_fixture(self):
        text = "夹具名称：真空吸盘\n材料名称：铝合金"
        result = self.extractor._fallback_extract(text)
        assert result['fixture'] == '真空吸盘'

    def test_extracts_material(self):
        text = "材料名称：6061铝合金\n刀具名称：立铣刀"
        result = self.extractor._fallback_extract(text)
        assert result['material'] == '6061铝合金'

    def test_extracts_tool_name(self):
        text = "刀具名称：立铣刀\n产品名称：测试"
        result = self.extractor._fallback_extract(text)
        assert '立铣刀' in result['tool_name']

    def test_extracts_tool_length_as_float(self):
        text = "长度：75\n直径：10"
        result = self.extractor._fallback_extract(text)
        assert result['tool_length'] == 75.0

    def test_extracts_tool_diameter_as_float(self):
        text = "直径：10\n其他信息"
        result = self.extractor._fallback_extract(text)
        assert result['tool_diameter'] == 10.0

    def test_empty_text_returns_defaults(self):
        result = self.extractor._fallback_extract("")
        for field in REQUIRED_FIELDS:
            assert field in result

    def test_operations_list_extracted(self):
        text = "1.快速定位\n2.铣削加工\n3.退刀"
        result = self.extractor._fallback_extract(text)
        assert len(result['operations']) == 3
        assert result['operations'][0]['sequence'] == 1

    def test_operations_with_chinese_numbering(self):
        text = "1、定位到起始点\n2、开始加工\n3、收尾"
        result = self.extractor._fallback_extract(text)
        assert len(result['operations']) == 3

    def test_invalid_tool_dimensions_default_to_zero(self):
        text = "长度：无\n直径：未知"
        result = self.extractor._fallback_extract(text)
        assert result['tool_length'] == 0
        assert result['tool_diameter'] == 0


class TestExtractOperations:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_numbered_operations(self):
        text = "1.快速定位\n2.铣削加工"
        ops = self.extractor._extract_operations(text)
        assert len(ops) == 2
        assert ops[0]['sequence'] == 1
        assert '快速定位' in ops[0]['content']

    def test_chinese_numbered_operations(self):
        text = "1、定位\n2、加工\n3、退刀"
        ops = self.extractor._extract_operations(text)
        assert len(ops) == 3

    def test_no_operations_found(self):
        text = "这是普通文本，没有编号步骤"
        ops = self.extractor._extract_operations(text)
        assert ops == []


class TestExtractValue:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_extract_until_delimiter(self):
        text = "测试值：结束"
        result = self.extractor._extract_value(text, 0)
        assert result == '测试值'

    def test_extract_to_end(self):
        text = "hello"
        result = self.extractor._extract_value(text, 0)
        assert result == 'hello'


class TestValidateParameters:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_all_fields_present(self):
        params = {field: 'value' for field in REQUIRED_FIELDS}
        params['tool_length'] = 10
        params['tool_diameter'] = 5
        valid, missing = self.extractor.validate_parameters(params)
        assert valid is True
        assert missing == []

    def test_missing_fields_detected(self):
        params = {'product_name': '测试'}
        valid, missing = self.extractor.validate_parameters(params)
        assert valid is False
        assert len(missing) > 0

    def test_zero_tool_diameter_is_missing_because_it_changes_toolpath(self):
        valid, missing = self.extractor.validate_parameters({'tool_diameter': 0})
        assert valid is False
        assert 'tool_diameter' in missing


class TestToProcessCard:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_creates_process_card(self):
        params = {
            'product_name': '铝合金外壳',
            'process_name': '铣削',
            'process_number': 'OP001',
            'version': 'V1.0',
            'equipment': 'CNC',
            'control_system': 'FANUC',
            'fixture': '虎钳',
            'material': '铝合金',
            'tool_name': '立铣刀',
            'tool_length': 75,
            'tool_diameter': 10,
        }
        card = self.extractor.to_process_card(params)
        assert isinstance(card, ProcessCard)
        assert card.product_name == '铝合金外壳'
        assert card.tool_info.name == '立铣刀'
        assert card.tool_info.diameter == 10

    def test_missing_fields_use_defaults(self):
        card = self.extractor.to_process_card({})
        assert card.product_name == ''
        assert card.tool_info.length == 0


class TestToOperations:
    def setup_method(self):
        self.extractor = ParameterExtractor()

    def test_converts_operations(self):
        ops_data = [
            {'sequence': 1, 'content': '定位', 'parameters': 'X=0', 'equipment': 'CNC', 'remark': ''},
            {'sequence': 2, 'content': '加工', 'parameters': 'Z=-5', 'equipment': 'CNC', 'remark': ''},
        ]
        ops = self.extractor.to_operations(ops_data)
        assert len(ops) == 2
        assert isinstance(ops[0], Operation)
        assert ops[0].sequence == 1

    def test_drawing_feed_per_revolution_converts_to_mm_per_minute(self):
        ops = self.extractor.to_operations([{
            'step': 1,
            'step_content': '钻孔',
            'parameters': 'X=10, Y=20, Z=-8',
            'spindle_speed': 750,
            'feed_rate': 0.2,
            'tooling': '麻花钻',
        }])
        assert 'F=150.000' in ops[0].parameters
        assert 'S=750' in ops[0].parameters

    def test_empty_list(self):
        ops = self.extractor.to_operations([])
        assert ops == []

    def test_missing_sequence_uses_index(self):
        ops_data = [{'content': '加工', 'parameters': '', 'equipment': '', 'remark': ''}]
        ops = self.extractor.to_operations(ops_data)
        assert ops[0].sequence == 1


class TestExtractAsync:
    @pytest.mark.asyncio
    async def test_extract_uses_fallback_when_no_api_key(self):
        extractor = ParameterExtractor()
        extractor.api_key = ""
        result = await extractor.extract("产品名称：测试产品")
        assert 'product_name' in result

    @pytest.mark.asyncio
    async def test_extract_falls_back_on_api_error(self):
        extractor = ParameterExtractor()
        extractor.api_key = "fake_key"
        with patch.object(extractor, '_extract_with_ai', side_effect=Exception("API error")):
            result = await extractor.extract("产品名称：测试产品")
            assert 'product_name' in result


class TestValidateAndConvert:
    def test_valid_params_returns_tuple(self):
        params = {
            'product_name': '铝合金外壳',
            'process_name': '铣削',
            'process_number': 'OP001',
            'version': 'V1.0',
            'equipment': 'CNC',
            'control_system': 'FANUC',
            'fixture': '虎钳',
            'material': '铝合金',
            'tool_name': '立铣刀',
            'tool_length': 75,
            'tool_diameter': 10,
            'operations': [
                {'sequence': 1, 'content': '加工', 'parameters': '', 'equipment': '', 'remark': ''}
            ],
        }
        result, missing = validate_and_convert(params)
        assert missing is None
        process_card, operations = result
        assert isinstance(process_card, ProcessCard)
        assert len(operations) == 1

    def test_invalid_params_returns_missing(self):
        result, missing = validate_and_convert({'product_name': '测试'})
        assert result is None
        assert len(missing) > 0


class TestExtractParametersFunction:
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        result = await extract_parameters("产品名称：测试\n工序名称：铣削")
        assert 'product_name' in result
