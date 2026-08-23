import pytest
from app.core.gcode_generator import GCodeGenerator, generate_gcode
from app.models.schemas import ProcessCard, ToolInfo, Operation


def make_process_card(**kwargs):
    defaults = {
        "product_name": "测试产品",
        "process_name": "铣削",
        "process_number": "OP001",
        "version": "V1.0",
        "equipment": "CNC加工中心",
        "control_system": "FANUC",
        "fixture": "虎钳",
        "material": "铝合金",
        "tool_info": ToolInfo(name="立铣刀", length=75.0, diameter=10.0),
    }
    defaults.update(kwargs)
    return ProcessCard(**defaults)


def make_operation(sequence=1, content="铣削平面", parameters="X=0, Y=0, Z=-2, F=200", equipment="", remark=""):
    return Operation(
        sequence=sequence,
        content=content,
        parameters=parameters,
        equipment=equipment,
        remark=remark,
    )


class TestGCodeGeneratorInit:
    def test_initial_state(self):
        gen = GCodeGenerator()
        assert gen.gcode_lines == []
        assert gen.process_card is None


class TestParseParameters:
    def setup_method(self):
        self.gen = GCodeGenerator()

    def test_empty_string(self):
        assert self.gen._parse_parameters("") == {}

    def test_single_param(self):
        result = self.gen._parse_parameters("X=10")
        assert result == {"X": 10.0}

    def test_multiple_params(self):
        result = self.gen._parse_parameters("X=10, Y=20, Z=-5, F=200")
        assert result == {"X": 10.0, "Y": 20.0, "Z": -5.0, "F": 200.0}

    def test_non_numeric_value(self):
        result = self.gen._parse_parameters("NAME=test")
        assert result == {"NAME": "test"}

    def test_whitespace_handling(self):
        result = self.gen._parse_parameters("  X = 10 , Y = 20 ")
        assert result["X"] == 10.0
        assert result["Y"] == 20.0


class TestGenerate:
    def setup_method(self):
        self.gen = GCodeGenerator()
        self.card = make_process_card()

    def test_generate_with_operations(self):
        ops = [make_operation(content="铣平面", parameters="X=0, Y=0, X_END=50, Y_END=50, Z=-2, F=200")]
        gcode = self.gen.generate(self.card, ops)
        assert "G90" in gcode
        assert "M30" in gcode
        assert "; 产品名称: 测试产品" in gcode

    def test_generate_without_operations_requires_geometry(self):
        with pytest.raises(ValueError, match="至少提供一个"):
            self.gen.generate(self.card, [])

    def test_header_contains_process_card_info(self):
        gcode = self.gen.generate(self.card, [make_operation()])
        assert "测试产品" in gcode
        assert "OP001" in gcode
        assert "FANUC" in gcode
        assert "铝合金" in gcode

    def test_initialization_codes(self):
        gcode = self.gen.generate(self.card, [make_operation()])
        assert "G90 G54 G17 G40 G49 G80 G21" in gcode
        assert "T01 M06" in gcode
        assert "M03 S3000" in gcode

    def test_finalization_codes(self):
        gcode = self.gen.generate(self.card, [make_operation()])
        assert "M05" in gcode
        assert "M30" in gcode


class TestOperationDispatch:
    def setup_method(self):
        self.gen = GCodeGenerator()
        self.card = make_process_card()

    def _generate_with_op(self, content, parameters="X=10, Y=10, Z=-5, F=100"):
        op = make_operation(content=content, parameters=parameters)
        return self.gen.generate(self.card, [op])

    def test_face_milling(self):
        gcode = self._generate_with_op("铣平面", "X=0, Y=0, X_END=50, Y_END=50, Z=-2, F=200")
        assert "; 平面铣削" in gcode

    def test_face_milling_alt_keyword(self):
        gcode = self._generate_with_op("平面铣", "X=0, Y=0, X_END=50, Y_END=50, Z=-2, F=200")
        assert "; 平面铣削" in gcode

    def test_profile_milling(self):
        gcode = self._generate_with_op("轮廓加工", "X=10, Y=10, WIDTH=50, HEIGHT=40, Z=-5, F=100")
        assert "; 轮廓铣削" in gcode

    def test_drilling(self):
        gcode = self._generate_with_op("钻孔")
        assert "; 钻孔" in gcode
        assert "G81" in gcode

    def test_tapping(self):
        gcode = self._generate_with_op("攻丝")
        assert "; 攻丝" in gcode
        assert "G84" in gcode

    def test_reaming(self):
        gcode = self._generate_with_op("铰孔")
        assert "; 铰孔" in gcode
        assert "G85" in gcode

    def test_boring(self):
        gcode = self._generate_with_op("镗孔")
        assert "; 镗孔" in gcode
        assert "G86" in gcode

    def test_chamfering(self):
        gcode = self._generate_with_op("倒角", parameters="X=25, Y=25, R=5, F=50")
        assert "; 倒角" in gcode
        assert "G02" in gcode

    def test_thread_milling(self):
        gcode = self._generate_with_op("螺纹铣削", parameters="X=25, Y=25, D=10, Z=-10, P=1.5, F=100")
        assert "; 螺纹铣削" in gcode

    def test_deep_hole_drilling(self):
        gcode = self._generate_with_op("深孔加工", parameters="X=10, Y=10, Z=-50, F=50, PECK=10")
        assert "; 深孔钻" in gcode

    def test_zigzag_milling(self):
        gcode = self._generate_with_op("往复铣削", parameters="X=0, Y=0, WIDTH=50, HEIGHT=50, Z=-2, F=200, STEP=5")
        assert "; 往复铣削" in gcode

    def test_circle_milling(self):
        gcode = self._generate_with_op("铣圆孔", parameters="X=25, Y=25, D=20, Z=-5, F=200")
        assert "; 圆孔铣削" in gcode

    def test_generic_milling(self):
        gcode = self._generate_with_op("铣削零件")
        assert "; 铣削加工" in gcode

    def test_rapid_positioning(self):
        gcode = self._generate_with_op("快移到位置")
        assert "G00" in gcode

    def test_unknown_operation_requires_supported_type(self):
        with pytest.raises(ValueError, match="支持的工序类型"):
            self._generate_with_op("未知操作")


class TestExtractHelpers:
    def setup_method(self):
        self.gen = GCodeGenerator()

    def test_extract_hole_diameter_with_unit(self):
        assert self.gen._extract_hole_diameter("Φ20mm 的圆孔") == 20.0

    def test_extract_hole_diameter_default(self):
        assert self.gen._extract_hole_diameter("无直径信息") == 10.0

    def test_extract_hole_diameter_from_text(self):
        assert self.gen._extract_hole_diameter("圆孔15") == 15.0

    def test_extract_hole_depth_with_keyword(self):
        assert self.gen._extract_hole_depth("深度 10mm") == 10.0

    def test_extract_hole_depth_short(self):
        assert self.gen._extract_hole_depth("深 8mm") == 8.0

    def test_extract_hole_depth_default(self):
        assert self.gen._extract_hole_depth("无深度信息") == 5.0

    def test_extract_workpiece_size(self):
        w, h = self.gen._extract_workpiece_size("100×80mm 工件")
        assert w == 100.0
        assert h == 80.0

    def test_extract_workpiece_size_default(self):
        w, h = self.gen._extract_workpiece_size("无尺寸")
        assert w == 50.0
        assert h == 50.0


class TestGenerateFromProcessCard:
    def setup_method(self):
        self.gen = GCodeGenerator()

    @pytest.mark.parametrize(
        "process_name",
        [
            "铣平面加工", "钻孔加工", "攻丝加工", "铰孔精加工", "镗孔加工",
            "倒角加工", "螺纹加工", "深孔加工", "圆孔加工", "其他加工",
        ],
    )
    def test_process_card_without_geometry_requires_operations(self, process_name):
        card = make_process_card(process_name=process_name)
        with pytest.raises(ValueError, match="至少提供一个"):
            self.gen.generate(card, [])


class TestCircleMillingCode:
    def setup_method(self):
        self.gen = GCodeGenerator()
        self.gen.gcode_lines = []

    def test_generates_arc(self):
        self.gen._generate_circle_milling_code(25, 25, 20, 5, 8)
        output = '\n'.join(self.gen.gcode_lines)
        assert "G02" in output

    def test_tool_too_large(self):
        self.gen._generate_circle_milling_code(25, 25, 10, 5, 12)
        output = '\n'.join(self.gen.gcode_lines)
        assert "错误" in output


class TestGenerateGcodeFunction:
    def test_convenience_function(self):
        card = make_process_card()
        ops = [make_operation(content="钻孔", parameters="X=50, Y=50, Z=-20, F=80")]
        gcode = generate_gcode(card, ops)
        assert "G81" in gcode
        assert "M30" in gcode
