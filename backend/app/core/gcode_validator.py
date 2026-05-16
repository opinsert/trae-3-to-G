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
    
    def validate(self, gcode: str) -> ValidationResult:
        errors = []
        warnings = []
        lines = gcode.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line or line.startswith(';'):
                continue
            
            line_errors, line_warnings = self._validate_line(line, line_num)
            errors.extend(line_errors)
            warnings.extend(line_warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_line(self, line: str, line_num: int) -> tuple:
        errors = []
        warnings = []
        
        codes = self.code_pattern.findall(line)
        coords = self.coord_pattern.findall(line)
        
        for code_type, code_num in codes:
            full_code = f"{code_type}{code_num}"
            if code_type == 'G' and full_code not in self.valid_g_codes:
                errors.append(ValidationError(
                    line=line_num,
                    code='E001',
                    message=f"无效的G代码: {full_code}",
                    suggestion=f"请使用有效的G代码，如G00, G01, G02等"
                ))
            elif code_type == 'M' and full_code not in self.valid_m_codes:
                errors.append(ValidationError(
                    line=line_num,
                    code='E002',
                    message=f"无效的M代码: {full_code}",
                    suggestion=f"请使用有效的M代码，如M03, M05, M30等"
                ))
        
        for axis, value in coords:
            try:
                coord_value = float(value)
                if axis == 'X' and (coord_value < 0 or coord_value > 200):
                    errors.append(ValidationError(
                        line=line_num,
                        code='E003',
                        message=f"X坐标超出范围: {coord_value}",
                        suggestion=f"X坐标应在0-200范围内"
                    ))
                elif axis == 'Y' and (coord_value < 0 or coord_value > 200):
                    errors.append(ValidationError(
                        line=line_num,
                        code='E003',
                        message=f"Y坐标超出范围: {coord_value}",
                        suggestion=f"Y坐标应在0-200范围内"
                    ))
                elif axis == 'Z' and (coord_value < 0 or coord_value > 100):
                    errors.append(ValidationError(
                        line=line_num,
                        code='E003',
                        message=f"Z坐标超出范围: {coord_value}",
                        suggestion=f"Z坐标应在0-100范围内"
                    ))
            except ValueError:
                errors.append(ValidationError(
                    line=line_num,
                    code='E004',
                    message=f"坐标值格式错误: {axis}{value}",
                    suggestion="请使用有效的数值格式"
                ))
        
        if 'G01' in line and 'F' not in line.upper():
            warnings.append(ValidationWarning(
                line=line_num,
                message="G01指令缺少进给速度F参数"
            ))
        
        if 'G00' in line and ('F' in line.upper() or 'S' in line.upper()):
            warnings.append(ValidationWarning(
                line=line_num,
                message="G00快速移动指令中包含F或S参数，这些参数将被忽略"
            ))
        
        return errors, warnings

def validate_gcode(gcode: str) -> ValidationResult:
    validator = GCodeValidator()
    return validator.validate(gcode)
