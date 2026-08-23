"""
GCodeValidator 测试套件

测试策略：验证意图而非仅验证行为（Rule 9）。
每个测试用例命名体现"为什么"该行为重要——即它保护了什么安全/正确性不变式。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.gcode_validator import GCodeValidator, validate_gcode


class TestValidGCode:
    """合法G代码应当完全通过验证，因为正常程序不应产生误报。"""

    def test_standard_program_passes_validation(self):
        """标准CNC程序（初始化-切削-结束）应无错误，
        确保验证器不会阻止正常加工流程。"""
        gcode = "\n".join([
            "G90 G54 G17 G40 G49 G80 G21 G94",
            "T01 M06",
            "G43 H01 Z50.0 M08",
            "M03 S3000",
            "G00 Z50.0",
            "G00 X10.0 Y10.0",
            "G01 Z5.0 F500",
            "G01 X50.0 F500",
            "G00 Z50.0",
            "G00 X0 Y0",
            "M05",
            "M09",
            "M30",
        ])
        result = validate_gcode(gcode)
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_empty_program_is_valid(self):
        """空程序不应报错，因为验证器应只检查存在的指令。"""
        result = validate_gcode("")
        assert result.valid is True

    def test_comment_only_program_is_valid(self):
        """纯注释程序不应报错。"""
        gcode = "; This is a comment\n; Another comment"
        result = validate_gcode(gcode)
        assert result.valid is True


class TestSpindleValidation:
    """主轴状态验证：切削前必须启动主轴，否则刀具不旋转会损坏工件和刀具。"""

    def test_cutting_without_spindle_start_reports_error(self):
        """在主轴未启动时执行切削(G01)应报错(E005)，
        因为刀具不旋转会导致刀具折断或工件损坏。"""
        gcode = "\n".join([
            "G90 G54",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0 F500",  # No M03/M04 before this
        ])
        result = validate_gcode(gcode)
        assert not result.valid
        e005_errors = [e for e in result.errors if e.code == 'E005']
        assert len(e005_errors) >= 1
        assert "主轴未启动" in e005_errors[0].message

    def test_cutting_after_spindle_start_is_ok(self):
        """M03启动主轴后再切削应无E005错误。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0 F500",
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        e005_errors = [e for e in result.errors if e.code == 'E005']
        assert len(e005_errors) == 0

    def test_g02_arc_without_spindle_reports_error(self):
        """G02圆弧插补也是切削运动，无主轴同样应报错。"""
        gcode = "\n".join([
            "G90 G54",
            "G00 X10.0 Y10.0 Z50.0",
            "G02 X20.0 Y10.0 I5.0 J0 F200",
        ])
        result = validate_gcode(gcode)
        e005_errors = [e for e in result.errors if e.code == 'E005']
        assert len(e005_errors) >= 1

    def test_spindle_not_stopped_before_program_end_warns(self):
        """M30结束前不停主轴(M05)会导致主轴持续旋转，存在安全隐患。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0 F500",
            "G00 Z50.0",
            "M30",  # No M05 before this
        ])
        result = validate_gcode(gcode)
        spindle_warnings = [w for w in result.warnings if "主轴" in w.message and "停止" in w.message]
        assert len(spindle_warnings) >= 1


class TestSafeZHeightValidation:
    """安全高度验证：在Z低于安全高度时水平移动可能撞到夹具或工件。"""

    def test_horizontal_move_below_safe_z_warns(self):
        """当Z低于安全高度(5.0)时进行XY移动应警告，
        因为低Z的水平运动可能撞到夹具。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 Z2.0",       # Z=2.0 < safe_z_height(5.0)
            "G00 X50.0 Y50.0",  # Horizontal move at low Z
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        collision_warnings = [w for w in result.warnings if "安全高度" in w.message]
        assert len(collision_warnings) >= 1

    def test_horizontal_move_above_safe_z_no_warning(self):
        """当Z>=安全高度时水平移动不应警告。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 Z50.0",        # Z=50 >= safe_z_height
            "G00 X50.0 Y50.0",  # Safe horizontal move
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        collision_warnings = [w for w in result.warnings if "安全高度" in w.message]
        assert len(collision_warnings) == 0

    def test_configurable_safe_z_height(self):
        """安全高度阈值应可配置，不同机床有不同安全高度需求。"""
        validator = GCodeValidator()
        validator.safe_z_height = 10.0  # Raise threshold
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 Z8.0",        # Z=8 < new threshold of 10
            "G00 X50.0 Y50.0",
            "M05",
            "M30",
        ])
        result = validator.validate(gcode)
        collision_warnings = [w for w in result.warnings if "安全高度" in w.message]
        assert len(collision_warnings) >= 1


class TestIncrementalModeOvertravel:
    """增量模式(G91)超程检测：增量值需累加为绝对位置后判断，
    否则每次增量值在范围内但累加后可能超程，导致机床撞限位。"""

    def test_g91_incremental_accumulates_and_detects_overtravel(self):
        """G91下多次增量移动累加后超出X范围应报E003，
        单次增量看似合理但累加后超程是常见编程错误。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X180.0 Y10.0 Z50.0",  # Start near X limit
            "G91",                        # Switch to incremental
            "G01 X30.0 F500",            # X: 180+30=210 > 200, overtravel!
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        e003_errors = [e for e in result.errors if e.code == 'E003']
        assert len(e003_errors) >= 1
        assert "X" in e003_errors[0].message

    def test_g91_within_range_no_error(self):
        """G91增量移动后仍在范围内不应报超程。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G91",
            "G01 X5.0 F500",   # X: 10+5=15, within range
            "G01 Y5.0 F500",   # Y: 10+5=15, within range
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        e003_errors = [e for e in result.errors if e.code == 'E003']
        assert len(e003_errors) == 0


class TestRapidPlungeValidation:
    """G00快速下刀检测：G00用于快速空行程，不应用于切入材料，
    因为快速进刀无速度控制会折断刀具或损坏工件。"""

    def test_g00_plunge_to_negative_z_warns(self):
        """G00直接下降到负Z（切入工件）应警告，
        因为快速切入缺少进给速度控制，极易折断刀具。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G00 Z-5.0",  # Rapid plunge to negative Z!
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        plunge_warnings = [w for w in result.warnings if "G00" in w.message and "负值" in w.message]
        assert len(plunge_warnings) >= 1

    def test_g01_plunge_to_negative_z_no_rapid_warning(self):
        """G01进刀是正常操作，不应触发快速下刀警告。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-5.0 F500",  # Normal controlled plunge
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        plunge_warnings = [w for w in result.warnings if "G00" in w.message and "负值" in w.message]
        assert len(plunge_warnings) == 0


class TestProgramEndValidation:
    """程序结束后指令检测：M02/M30后的指令不会被执行，
    通常是编程错误或遗留代码，应提醒操作者。"""

    def test_code_after_m30_warns(self):
        """M30之后的指令不会执行，应警告以避免编程者误以为还有后续操作。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0 F500",
            "G00 Z50.0",
            "M05",
            "M30",
            "G00 X0 Y0",  # Unreachable code
        ])
        result = validate_gcode(gcode)
        end_warnings = [w for w in result.warnings if "程序已结束" in w.message]
        assert len(end_warnings) >= 1

    def test_code_after_m02_warns(self):
        """M02与M30等效，之后指令同样应警告。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0 F500",
            "G00 Z50.0",
            "M05",
            "M02",
            "G01 X100.0 F200",  # Unreachable
        ])
        result = validate_gcode(gcode)
        end_warnings = [w for w in result.warnings if "程序已结束" in w.message]
        assert len(end_warnings) >= 1


class TestFeedRateValidation:
    """进给速度验证：切削运动无进给速度可能导致机床使用默认值或停止，
    两者都可能造成加工质量问题。"""

    def test_g01_without_any_prior_feed_rate_warns(self):
        """从未设置过F值时G01缺少F应产生更严重的警告，
        因为机床可能无默认进给速度导致停止或异常。"""
        gcode = "\n".join([
            "G90 G54",
            "M03 S3000",
            "G00 X10.0 Y10.0 Z50.0",
            "G01 Z-2.0",  # No F ever set
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        feed_warnings = [w for w in result.warnings if "进给速度" in w.message and "未设置" in w.message]
        assert len(feed_warnings) >= 1


class TestBackwardCompatibility:
    """向后兼容性：validate_gcode()的签名和返回类型必须保持不变，
    确保现有API调用方（gcode.py, drawing.py等）无需修改。"""

    def test_validate_gcode_returns_validation_result(self):
        """模块级函数仍返回ValidationResult实例。"""
        from app.models.schemas import ValidationResult
        result = validate_gcode("G00 X10.0 Y10.0")
        assert isinstance(result, ValidationResult)

    def test_existing_e001_invalid_gcode_still_works(self):
        """E001无效G代码检测仍正常工作。"""
        gcode = "G99\nG77"
        result = validate_gcode(gcode)
        e001_errors = [e for e in result.errors if e.code == 'E001']
        assert len(e001_errors) >= 1

    def test_existing_e003_coord_range_still_works(self):
        """E003坐标范围检测在绝对模式下仍正常工作。"""
        gcode = "\n".join([
            "G90",
            "M03 S3000",
            "G00 X250.0",  # Out of range
        ])
        result = validate_gcode(gcode)
        e003_errors = [e for e in result.errors if e.code == 'E003']
        assert len(e003_errors) >= 1

    def test_configurable_ranges(self):
        """坐标范围应可配置，适应不同机床行程。"""
        validator = GCodeValidator()
        validator.x_range = (0.0, 500.0)
        gcode = "\n".join([
            "G90",
            "M03 S3000",
            "G00 X300.0 Y10.0 Z50.0",
        ])
        result = validator.validate(gcode)
        e003_errors = [e for e in result.errors if e.code == 'E003']
        assert len(e003_errors) == 0


class TestMillimeterSimulationContract:
    """仿真输出必须明确毫米、绝对坐标和每分钟进给，并允许负Z切削。"""

    def test_negative_z_cutting_passes_in_millimeter_work_coordinates(self):
        gcode = "\n".join([
            "G90 G54 G21 G94",
            "M03 S3000",
            "G00 X10 Y10 Z50",
            "G01 X15 Y15 Z-5 F200",
            "G00 Z50",
            "M05",
            "M30",
        ])
        result = validate_gcode(gcode)
        assert result.valid is True

    def test_missing_unit_and_feed_modes_are_rejected(self):
        result = validate_gcode("G90 G54\nM03 S3000\nG01 X10 Y10 Z-2 F200\nM05\nM30")
        mode_errors = [error for error in result.errors if error.code == 'E006']
        assert len(mode_errors) == 2

    def test_feed_above_simulation_limit_is_rejected(self):
        result = validate_gcode("G90 G54 G21 G94\nM03 S3000\nG01 X10 Y10 Z-2 F6000\nM05\nM30")
        assert any(error.code == 'E009' for error in result.errors)

    def test_spindle_above_simulation_limit_is_rejected(self):
        result = validate_gcode("G90 G54 G21 G94\nM03 S13000\nG01 X10 Y10 Z-2 F200\nM05\nM30")
        assert any(error.code == 'E010' for error in result.errors)
