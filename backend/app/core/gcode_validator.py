import re
from app.models.schemas import ValidationResult, ValidationError, ValidationWarning


class GCodeValidator:
    def __init__(self):
        self.valid_g_codes = {'G00', 'G01', 'G02', 'G03', 'G04', 'G17', 'G18', 'G19',
                              'G20', 'G21', 'G40', 'G41', 'G42', 'G43', 'G44', 'G49',
                              'G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G80', 'G81',
                              'G82', 'G83', 'G84', 'G85', 'G86', 'G87', 'G88', 'G89',
                              'G90', 'G91', 'G98', 'G99'}

        self.valid_m_codes = {'M00', 'M01', 'M02', 'M03', 'M04', 'M05', 'M06', 'M07',
                              'M08', 'M09', 'M10', 'M11', 'M13', 'M14', 'M15', 'M16',
                              'M30'}

        self.coord_pattern = re.compile(r'([XYZ])([+-]?\d*\.?\d+)')
        self.code_pattern = re.compile(r'([GM])(\d{2})')
        self.feed_pattern = re.compile(r'F([+-]?\d*\.?\d+)')

        # Configurable limits
        self.safe_z_height = 5.0
        self.x_range = (0.0, 200.0)
        self.y_range = (0.0, 200.0)
        self.z_range = (0.0, 100.0)

    def validate(self, gcode: str) -> ValidationResult:
        errors = []
        warnings = []
        lines = gcode.split('\n')

        state = {
            'current_x': None,
            'current_y': None,
            'current_z': None,
            'is_absolute': True,
            'spindle_on': False,
            'current_feed_rate': None,
            'has_work_coordinate': False,
            'has_tool_length_comp': False,
            'program_ended': False,
        }

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line or line.startswith(';'):
                continue

            line_errors, line_warnings = self._validate_line(line, line_num, state)
            errors.extend(line_errors)
            warnings.extend(line_warnings)

        # End-of-program safety check: spindle not stopped before program end
        if state['program_ended'] and state['spindle_on']:
            warnings.append(ValidationWarning(
                line=len(lines),
                message="程序结束前未停止主轴(M05)，存在安全风险"
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_line(self, line: str, line_num: int, state: dict) -> tuple:
        errors = []
        warnings = []

        codes = self.code_pattern.findall(line)
        coords = self.coord_pattern.findall(line)
        feed_match = self.feed_pattern.search(line)

        g_codes_in_line = set()
        m_codes_in_line = set()

        for code_type, code_num in codes:
            full_code = f"{code_type}{code_num}"
            if code_type == 'G':
                g_codes_in_line.add(full_code)
            else:
                m_codes_in_line.add(full_code)

        # --- Syntax validation (existing) ---
        for code_type, code_num in codes:
            full_code = f"{code_type}{code_num}"
            if code_type == 'G' and full_code not in self.valid_g_codes:
                errors.append(ValidationError(
                    line=line_num,
                    code='E001',
                    message=f"无效的G代码: {full_code}",
                    suggestion="请使用有效的G代码，如G00, G01, G02等"
                ))
            elif code_type == 'M' and full_code not in self.valid_m_codes:
                errors.append(ValidationError(
                    line=line_num,
                    code='E002',
                    message=f"无效的M代码: {full_code}",
                    suggestion="请使用有效的M代码，如M03, M05, M30等"
                ))

        # --- Warning: code after program end ---
        if state['program_ended']:
            warnings.append(ValidationWarning(
                line=line_num,
                message="程序已结束(M02/M30)后仍有指令，这些指令将不会被执行"
            ))
            return errors, warnings

        # --- Update state: mode switches ---
        if 'G90' in g_codes_in_line:
            state['is_absolute'] = True
        if 'G91' in g_codes_in_line:
            state['is_absolute'] = False

        # Work coordinate system
        wcs_codes = {'G54', 'G55', 'G56', 'G57', 'G58', 'G59'}
        if g_codes_in_line & wcs_codes:
            state['has_work_coordinate'] = True

        # Tool length compensation
        if 'G43' in g_codes_in_line:
            state['has_tool_length_comp'] = True

        # Spindle state
        if 'M03' in m_codes_in_line or 'M04' in m_codes_in_line:
            state['spindle_on'] = True
        if 'M05' in m_codes_in_line:
            state['spindle_on'] = False

        # Feed rate
        if feed_match:
            state['current_feed_rate'] = float(feed_match.group(1))

        # Program end
        if 'M02' in m_codes_in_line or 'M30' in m_codes_in_line:
            state['program_ended'] = True

        # --- Compute actual coordinates for this line ---
        parsed_coords = {}
        for axis, value in coords:
            try:
                parsed_coords[axis] = float(value)
            except ValueError:
                pass

        # Determine actual absolute positions after this line
        actual_x = state['current_x']
        actual_y = state['current_y']
        actual_z = state['current_z']

        if state['is_absolute']:
            if 'X' in parsed_coords:
                actual_x = parsed_coords['X']
            if 'Y' in parsed_coords:
                actual_y = parsed_coords['Y']
            if 'Z' in parsed_coords:
                actual_z = parsed_coords['Z']
        else:
            # Incremental mode: accumulate
            if 'X' in parsed_coords:
                actual_x = (state['current_x'] or 0.0) + parsed_coords['X']
            if 'Y' in parsed_coords:
                actual_y = (state['current_y'] or 0.0) + parsed_coords['Y']
            if 'Z' in parsed_coords:
                actual_z = (state['current_z'] or 0.0) + parsed_coords['Z']

        # --- Coordinate range validation (with incremental mode support) ---
        has_motion = g_codes_in_line & {'G00', 'G01', 'G02', 'G03'}
        if has_motion or parsed_coords:
            if actual_x is not None and (actual_x < self.x_range[0] or actual_x > self.x_range[1]):
                errors.append(ValidationError(
                    line=line_num,
                    code='E003',
                    message=f"X坐标超出范围: {actual_x}",
                    suggestion=f"X坐标应在{self.x_range[0]}-{self.x_range[1]}范围内"
                ))
            if actual_y is not None and (actual_y < self.y_range[0] or actual_y > self.y_range[1]):
                errors.append(ValidationError(
                    line=line_num,
                    code='E003',
                    message=f"Y坐标超出范围: {actual_y}",
                    suggestion=f"Y坐标应在{self.y_range[0]}-{self.y_range[1]}范围内"
                ))
            if actual_z is not None and (actual_z < self.z_range[0] or actual_z > self.z_range[1]):
                errors.append(ValidationError(
                    line=line_num,
                    code='E003',
                    message=f"Z坐标超出范围: {actual_z}",
                    suggestion=f"Z坐标应在{self.z_range[0]}-{self.z_range[1]}范围内"
                ))

            # For non-incremental raw value check (backwards compat for absolute mode)
            if state['is_absolute']:
                for axis, value in coords:
                    try:
                        coord_value = float(value)
                        # E004 for parse errors already handled above
                    except ValueError:
                        errors.append(ValidationError(
                            line=line_num,
                            code='E004',
                            message=f"坐标值格式错误: {axis}{value}",
                            suggestion="请使用有效的数值格式"
                        ))

        # --- Logic validation ---

        # Cutting move without spindle
        cutting_codes = g_codes_in_line & {'G01', 'G02', 'G03'}
        if cutting_codes and not state['spindle_on']:
            errors.append(ValidationError(
                line=line_num,
                code='E005',
                message="切削指令执行前主轴未启动",
                suggestion="请在切削移动(G01/G02/G03)前添加M03或M04启动主轴"
            ))

        # G01 without feed rate ever set
        if 'G01' in g_codes_in_line and 'F' not in line.upper() and state['current_feed_rate'] is None:
            warnings.append(ValidationWarning(
                line=line_num,
                message="G01指令缺少进给速度F参数，且此前未设置过进给速度"
            ))
        elif 'G01' in g_codes_in_line and 'F' not in line.upper() and state['current_feed_rate'] is not None:
            # Keep existing behavior as a milder warning
            warnings.append(ValidationWarning(
                line=line_num,
                message="G01指令缺少进给速度F参数"
            ))

        # Horizontal move at low Z
        x_changed = 'X' in parsed_coords
        y_changed = 'Y' in parsed_coords
        if (x_changed or y_changed) and (g_codes_in_line & {'G00', 'G01'}):
            current_z = state['current_z']
            if current_z is not None and current_z < self.safe_z_height:
                warnings.append(ValidationWarning(
                    line=line_num,
                    message=f"在低于安全高度(Z={current_z} < {self.safe_z_height})时发生水平移动，存在撞刀风险"
                ))

        # G00 rapid move with F/S (existing warning)
        if 'G00' in g_codes_in_line and ('F' in line.upper() or 'S' in line.upper()):
            # Only warn about F/S in G00 if there's no cutting code on same line
            if not cutting_codes:
                warnings.append(ValidationWarning(
                    line=line_num,
                    message="G00快速移动指令中包含F或S参数，这些参数将被忽略"
                ))

        # --- Safety validation ---

        # Rapid plunge into material: G00 moving Z to negative
        if 'G00' in g_codes_in_line and 'Z' in parsed_coords:
            target_z = actual_z
            if target_z is not None and target_z < 0:
                warnings.append(ValidationWarning(
                    line=line_num,
                    message=f"G00快速移动下降至Z={target_z}(负值)，不应使用G00切入材料，建议改用G01"
                ))

        # --- Update tracked position ---
        if actual_x is not None:
            state['current_x'] = actual_x
        if actual_y is not None:
            state['current_y'] = actual_y
        if actual_z is not None:
            state['current_z'] = actual_z

        return errors, warnings


def validate_gcode(gcode: str) -> ValidationResult:
    validator = GCodeValidator()
    return validator.validate(gcode)
