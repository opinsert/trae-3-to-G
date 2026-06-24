import pytest
from pydantic import ValidationError as PydanticValidationError
from app.models.schemas import (
    ToolInfo,
    DrawingStep,
    ProcessCard,
    Operation,
    ValidationError,
    ValidationWarning,
    ValidationResult,
    ConvertResult,
    ConvertData,
    ConvertResponse,
    GCodeValidateRequest,
    GCodeValidateResponse,
    ExampleItem,
    ExampleListResponse,
    AdvanceResponse,
)


class TestToolInfo:
    def test_create_valid(self):
        tool = ToolInfo(name="立铣刀", length=75.0, diameter=10.0)
        assert tool.name == "立铣刀"
        assert tool.length == 75.0
        assert tool.diameter == 10.0

    def test_missing_name_raises(self):
        with pytest.raises(PydanticValidationError):
            ToolInfo(length=75.0, diameter=10.0)

    def test_zero_dimensions(self):
        tool = ToolInfo(name="测试", length=0, diameter=0)
        assert tool.length == 0
        assert tool.diameter == 0


class TestDrawingStep:
    def test_create_minimal(self):
        step = DrawingStep(step=1, step_content="铣削平面")
        assert step.step == 1
        assert step.step_content == "铣削平面"
        assert step.tooling == ""

    def test_create_full(self):
        step = DrawingStep(
            step=1,
            step_content="铣削",
            tooling="立铣刀",
            spindle_speed=3000,
            cutting_speed=200,
            feed_rate=0.1,
            depth_of_cut=2.0,
            feed_count=3,
            machine_time=5.0,
            auxiliary_time=1.0,
            remark="测试备注",
        )
        assert step.spindle_speed == 3000
        assert step.remark == "测试备注"

    def test_optional_fields_default_none(self):
        step = DrawingStep(step=1, step_content="test")
        assert step.spindle_speed is None
        assert step.cutting_speed is None
        assert step.feed_rate is None


class TestProcessCard:
    def _make_card(self, **overrides):
        defaults = {
            "product_name": "测试产品",
            "process_name": "铣削",
            "process_number": "OP001",
            "version": "V1.0",
            "equipment": "CNC",
            "control_system": "FANUC",
            "fixture": "虎钳",
            "material": "铝合金",
            "tool_info": ToolInfo(name="立铣刀", length=75, diameter=10),
        }
        defaults.update(overrides)
        return ProcessCard(**defaults)

    def test_create_valid(self):
        card = self._make_card()
        assert card.product_name == "测试产品"
        assert card.tool_info.name == "立铣刀"

    def test_optional_fields_default(self):
        card = self._make_card()
        assert card.workshop == ""
        assert card.blank_available_pieces is None
        assert card.preparation_time is None

    def test_with_optional_fields(self):
        card = self._make_card(
            workshop="一车间",
            material_grade="6061-T6",
            blank_type="铸件",
            equipment_model="VMC-850",
        )
        assert card.workshop == "一车间"
        assert card.material_grade == "6061-T6"


class TestOperation:
    def test_create_valid(self):
        op = Operation(
            sequence=1,
            content="铣削平面",
            parameters="X=0, Y=0",
            equipment="CNC",
        )
        assert op.sequence == 1
        assert op.content == "铣削平面"

    def test_optional_remark(self):
        op = Operation(
            sequence=1,
            content="test",
            parameters="",
            equipment="",
        )
        assert op.remark == ""


class TestValidationModels:
    def test_validation_error(self):
        err = ValidationError(line=1, code="E001", message="无效G代码")
        assert err.line == 1
        assert err.suggestion == ""

    def test_validation_warning(self):
        warn = ValidationWarning(line=5, message="缺少F参数")
        assert warn.line == 5

    def test_validation_result_valid(self):
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert result.valid is True

    def test_validation_result_with_errors(self):
        err = ValidationError(line=1, code="E001", message="test")
        result = ValidationResult(valid=False, errors=[err], warnings=[])
        assert result.valid is False
        assert len(result.errors) == 1


class TestConvertModels:
    def test_convert_result(self):
        cr = ConvertResult(success=True, message="成功")
        assert cr.success is True
        assert cr.missing_fields == []

    def test_convert_response_no_data(self):
        resp = ConvertResponse(success=False, message="失败")
        assert resp.data is None

    def test_gcode_validate_request(self):
        req = GCodeValidateRequest(gcode="G00 X10")
        assert req.gcode == "G00 X10"
        assert req.process_card is None


class TestExampleModels:
    def test_example_item(self):
        item = ExampleItem(
            id=1,
            name="测试",
            description="描述",
            category="铣削",
            card_data=ProcessCard(
                product_name="p",
                process_name="n",
                process_number="001",
                version="1",
                equipment="e",
                control_system="c",
                fixture="f",
                material="m",
                tool_info=ToolInfo(name="t", length=1, diameter=1),
            ),
            operations_data=[],
        )
        assert item.id == 1
        assert item.gcode == ""

    def test_example_list_response(self):
        resp = ExampleListResponse(success=True, data=[])
        assert resp.success is True
        assert resp.data == []

    def test_advance_response(self):
        resp = AdvanceResponse(success=True, data={"key": "value"})
        assert resp.data["key"] == "value"
