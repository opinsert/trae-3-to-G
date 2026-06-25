import re
from app.models.schemas import ProcessCard, Operation

class GCodeGenerator:
    def __init__(self):
        self.gcode_lines = []
        self.process_card = None
    
    def generate(self, process_card: ProcessCard, operations: list) -> str:
        self.gcode_lines = []
        self.process_card = process_card
        
        self._add_header(process_card)
        self._add_initialization()
        
        if operations and len(operations) > 0:
            for op in operations:
                self._add_operation(op)
        else:
            self._generate_from_process_card()
        
        self._add_finalization()
        
        return '\n'.join(self.gcode_lines)
    
    def _add_header(self, process_card: ProcessCard):
        self.gcode_lines.append(f"; 产品名称: {process_card.product_name}")
        self.gcode_lines.append(f"; 工序名称: {process_card.process_name}")
        self.gcode_lines.append(f"; 工序编号: {process_card.process_number}")
        self.gcode_lines.append(f"; 版本号: {process_card.version}")
        self.gcode_lines.append(f"; 设备: {process_card.equipment}")
        self.gcode_lines.append(f"; 数控系统: {process_card.control_system}")
        self.gcode_lines.append(f"; 夹具: {process_card.fixture}")
        self.gcode_lines.append(f"; 材料: {process_card.material}")
        if process_card.tool_info:
            self.gcode_lines.append(f"; 刀具: {process_card.tool_info.name} (直径:{process_card.tool_info.diameter}mm, 长度:{process_card.tool_info.length}mm)")
        self.gcode_lines.append("")
    
    def _add_initialization(self):
        self.gcode_lines.append("G90 G54 G17 G40 G49 G80 G21")
        self.gcode_lines.append("T01 M06")
        self.gcode_lines.append("G43 H01 Z50.0 M08")
        self.gcode_lines.append("M03 S3000")
        self.gcode_lines.append("G00 Z50.0")
        self.gcode_lines.append("")
    
    def _add_operation(self, op: Operation):
        self.gcode_lines.append(f"; 步骤{op.sequence}: {op.content}")
        self.gcode_lines.append(f"; 参数: {op.parameters}")

        content = op.content

        if "斜坡进刀" in content:
            self._generate_ramp_entry(op)
        elif "型腔" in content or "腔体" in content or "pocket" in content:
            self._generate_pocket_clearing(op)
        elif "侧壁" in content or "壁面" in content:
            self._generate_wall_finish(op)
        elif "底面" in content and "精加工" in content:
            self._generate_floor_finish(op)
        elif "铣平面" in content or "平面铣" in content or "面铣" in content:
            self._generate_face_milling(op)
        elif "轮廓" in content or "外形" in content:
            self._generate_profile_milling(op)
        elif "钻孔" in content or "打孔" in content:
            self._generate_drilling(op)
        elif "攻丝" in content or "攻牙" in content:
            self._generate_tapping(op)
        elif "铰孔" in content or "铰刀" in content:
            self._generate_reaming(op)
        elif "镗孔" in content or "镗削" in content:
            self._generate_boring(op)
        elif "倒角" in content:
            self._generate_chamfering(op)
        elif "螺纹" in content:
            self._generate_thread_milling(op)
        elif "深孔" in content:
            self._generate_deep_hole_drilling(op)
        elif "往复" in content or "来回" in content:
            self._generate_zigzag_milling(op)
        elif "圆孔" in content or "圆" in content:
            self._generate_circle_milling(op)
        elif "铣削" in content or "加工" in content:
            self._generate_generic_milling(op)
        elif "快移" in content or "定位" in content:
            self._generate_rapid_code(op)
        elif "返回安全高度" in content or "回退" in content:
            self._generate_retract()
        else:
            self._generate_generic_code(op)

        self.gcode_lines.append("")
    
    def _generate_from_process_card(self):
        process_card = self.process_card
        process_name = process_card.process_name if process_card else ""
        
        if "铣平面" in process_name or "平面铣" in process_name:
            self._generate_face_milling_from_card()
        elif "钻孔" in process_name:
            self._generate_drilling_from_card()
        elif "攻丝" in process_name or "攻牙" in process_name:
            self._generate_tapping_from_card()
        elif "铰孔" in process_name:
            self._generate_reaming_from_card()
        elif "镗孔" in process_name:
            self._generate_boring_from_card()
        elif "倒角" in process_name:
            self._generate_chamfering_from_card()
        elif "螺纹" in process_name:
            self._generate_thread_milling_from_card()
        elif "深孔" in process_name:
            self._generate_deep_hole_drilling_from_card()
        elif "圆孔" in process_name or "圆" in process_name:
            self._generate_circle_milling_from_card()
        else:
            self._generate_circle_milling_from_card()
    
    def _extract_numeric(self, text, patterns, default):
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return default

    def _extract_hole_diameter(self, text):
        return self._extract_numeric(text, [
            r'[\u03A6Φ]?(\d+(\.\d+)?)[\s]*mm',
            r'圆孔[\s]*(\d+(\.\d+)?)'
        ], 10.0)
    
    def _extract_hole_depth(self, text):
        return self._extract_numeric(text, [
            r'深度[\s]*[\u03A6Φ]?(\d+(\.\d+)?)[\s]*mm',
            r'深[\s]*(\d+(\.\d+)?)[\s]*mm'
        ], 5.0)
    
    def _extract_workpiece_size(self, text):
        match = re.search(r'(\d+(\.\d+)?)[\s]*[×xX×][\s]*(\d+(\.\d+)?)[\s]*mm', text)
        if match:
            return (float(match.group(1)), float(match.group(3)))
        return (50.0, 50.0)

    def _extract_card_params(self):
        text = f"{self.process_card.product_name} {self.process_card.process_name}"
        hole_diameter = self._extract_hole_diameter(text)
        hole_depth = self._extract_hole_depth(text)
        width, height = self._extract_workpiece_size(text)
        return text, hole_diameter, hole_depth, width / 2.0, height / 2.0

    def _add_tool_change_block(self, x, y, cycle_line):
        self.gcode_lines.append("M05")
        self.gcode_lines.append("T02 M06")
        self.gcode_lines.append("G43 H02 Z50.0")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(cycle_line)
        self.gcode_lines.append("G80")
        self.gcode_lines.append("G00 Z50.0")
        self.gcode_lines.append("T01 M06")
        self.gcode_lines.append("G43 H01 Z50.0")
        self.gcode_lines.append("M03 S3000")
    
    def _generate_face_milling_from_card(self):
        text = f"{self.process_card.product_name} {self.process_card.process_name} {self.process_card.material}"
        # face milling uses full text including material for size extraction
        width, height = self._extract_workpiece_size(text)
        tool_diameter = self.process_card.tool_info.diameter if self.process_card.tool_info else 16.0
        
        self.gcode_lines.append("; 平面铣削")
        self.gcode_lines.append(f"G00 X0 Y0")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z-2.0 F150")
        
        step_over = tool_diameter * 0.7
        y = 0
        while y < height:
            self.gcode_lines.append(f"G01 X{width:.3f} F200")
            y += step_over
            self.gcode_lines.append(f"G01 Y{min(y, height):.3f} F500")
            self.gcode_lines.append(f"G01 X0 F200")
            y += step_over
            self.gcode_lines.append(f"G01 Y{min(y, height):.3f} F500")
        
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_circle_milling_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        tool_diameter = self.process_card.tool_info.diameter if self.process_card.tool_info else 8.0
        
        self.gcode_lines.append(f"; 铣圆孔 - 直径:{hole_diameter}mm, 深度:{hole_depth}mm")
        self._generate_circle_milling_code(x_pos, y_pos, hole_diameter, hole_depth, tool_diameter)
    
    def _generate_drilling_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        
        self.gcode_lines.append(f"; 钻孔 - 直径:{hole_diameter}mm, 深度:{hole_depth}mm")
        self.gcode_lines.append(f"G00 X{x_pos:.3f} Y{y_pos:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G81 Z{hole_depth * -1:.3f} R2.0 F50")
        self.gcode_lines.append("G80")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_tapping_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        self.gcode_lines.append(f"; 攻丝 - M{hole_diameter}")
        self._add_tool_change_block(x_pos, y_pos, f"G84 Z{hole_depth * -1:.3f} R2.0 F{hole_diameter * 50}")
    
    def _generate_reaming_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        self.gcode_lines.append(f"; 铰孔 - 直径:{hole_diameter}mm")
        self._add_tool_change_block(x_pos, y_pos, f"G85 Z{hole_depth * -1:.3f} R2.0 F20")
    
    def _generate_boring_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        self.gcode_lines.append(f"; 镗孔 - 直径:{hole_diameter}mm, 深度:{hole_depth}mm")
        self._add_tool_change_block(x_pos, y_pos, f"G86 Z{hole_depth * -1:.3f} R2.0 F30")
    
    def _generate_chamfering_from_card(self):
        _, hole_diameter, _, x_pos, y_pos = self._extract_card_params()
        
        self.gcode_lines.append("; 倒角")
        self.gcode_lines.append(f"G00 X{x_pos:.3f} Y{y_pos:.3f}")
        self.gcode_lines.append("G01 Z1.0 F500")
        chamfer_radius = hole_diameter / 2.0 + 2.0
        self.gcode_lines.append(f"G01 X{x_pos + chamfer_radius:.3f} Y{y_pos:.3f} F100")
        self.gcode_lines.append(f"G01 Z-1.0 F50")
        self.gcode_lines.append(f"G02 X{x_pos:.3f} Y{y_pos + chamfer_radius:.3f} I{-chamfer_radius:.3f} J0 F50")
        self.gcode_lines.append(f"G02 X{x_pos - chamfer_radius:.3f} Y{y_pos:.3f} I0 J{-chamfer_radius:.3f} F50")
        self.gcode_lines.append(f"G02 X{x_pos:.3f} Y{y_pos - chamfer_radius:.3f} I{chamfer_radius:.3f} J0 F50")
        self.gcode_lines.append(f"G02 X{x_pos + chamfer_radius:.3f} Y{y_pos:.3f} I0 J{chamfer_radius:.3f} F50")
        self.gcode_lines.append("G01 Z1.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_thread_milling_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        pitch = 1.5
        
        self.gcode_lines.append(f"; 螺纹铣削 - M{hole_diameter}x{pitch}")
        thread_radius = hole_diameter / 2.0
        tool_offset = thread_radius - 0.5
        
        self.gcode_lines.append(f"G00 X{x_pos + tool_offset:.3f} Y{y_pos:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{hole_depth * -1:.3f} F50")
        
        cycles = int(hole_depth / pitch)
        for _ in range(cycles):
            self.gcode_lines.append(f"G02 I{-tool_offset:.3f} J0 Z{hole_depth * -1 + _ * pitch:.3f} F100")
        
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_deep_hole_drilling_from_card(self):
        _, hole_diameter, hole_depth, x_pos, y_pos = self._extract_card_params()
        peck_depth = 10.0
        
        self.gcode_lines.append(f"; 深孔钻 - 直径:{hole_diameter}mm, 深度:{hole_depth}mm")
        self.gcode_lines.append(f"G00 X{x_pos:.3f} Y{y_pos:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        
        current_depth = 0
        while current_depth > hole_depth * -1:
            next_depth = max(current_depth - peck_depth, hole_depth * -1)
            self.gcode_lines.append(f"G01 Z{next_depth:.3f} F50")
            self.gcode_lines.append("G01 Z5.0 F200")
            self.gcode_lines.append(f"G01 Z{next_depth + 2.0:.3f} F200")
            current_depth = next_depth
        
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_circle_milling_code(self, x, y, hole_diameter, hole_depth, tool_diameter):
        radius = hole_diameter / 2.0
        tool_radius = tool_diameter / 2.0
        cutter_radius = radius - tool_radius
        
        if cutter_radius <= 0:
            self.gcode_lines.append(f"; 错误: 刀具直径({tool_diameter}mm)大于等于孔直径({hole_diameter}mm)")
            return
        
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{hole_depth * -1:.3f} F100")
        self.gcode_lines.append(f"G02 I{cutter_radius:.3f} J0 F200")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_face_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x_start = params.get('X', 0)
        y_start = params.get('Y', 0)
        x_end = params.get('X_END', 50)
        y_end = params.get('Y_END', 50)
        depth = params.get('Z', -2)
        feed = params.get('F', 200)
        
        tool_diameter = self.process_card.tool_info.diameter if self.process_card and self.process_card.tool_info else 16.0
        step_over = tool_diameter * 0.7
        
        self.gcode_lines.append("; 平面铣削")
        self.gcode_lines.append(f"G00 X{x_start:.3f} Y{y_start:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{depth:.3f} F150")
        
        y = y_start
        direction = 1
        while y < y_end:
            if direction == 1:
                self.gcode_lines.append(f"G01 X{x_end:.3f} F{feed}")
            else:
                self.gcode_lines.append(f"G01 X{x_start:.3f} F{feed}")
            y += step_over
            self.gcode_lines.append(f"G01 Y{min(y, y_end):.3f} F500")
            direction *= -1
        
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_profile_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 25)
        y = params.get('Y', 25)
        width = params.get('WIDTH', 50)
        height = params.get('HEIGHT', 50)
        depth = params.get('Z', -5)
        feed = params.get('F', 150)
        
        self.gcode_lines.append("; 轮廓铣削")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{depth:.3f} F100")
        self.gcode_lines.append(f"G01 X{x + width:.3f} F{feed}")
        self.gcode_lines.append(f"G01 Y{y + height:.3f} F{feed}")
        self.gcode_lines.append(f"G01 X{x:.3f} F{feed}")
        self.gcode_lines.append(f"G01 Y{y:.3f} F{feed}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_drilling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        depth = params.get('Z', -10)
        feed = params.get('F', 50)
        
        self.gcode_lines.append("; 钻孔")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G81 Z{depth:.3f} R2.0 F{feed}")
        self.gcode_lines.append("G80")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_tapping(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        depth = params.get('Z', -10)
        pitch = params.get('P', 1.0)
        
        self.gcode_lines.append("; 攻丝")
        self._add_tool_change_block(x, y, f"G84 Z{depth:.3f} R2.0 F{pitch * 50}")
    
    def _generate_reaming(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        depth = params.get('Z', -10)
        feed = params.get('F', 20)
        
        self.gcode_lines.append("; 铰孔")
        self._add_tool_change_block(x, y, f"G85 Z{depth:.3f} R2.0 F{feed}")
    
    def _generate_boring(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        depth = params.get('Z', -10)
        feed = params.get('F', 30)
        
        self.gcode_lines.append("; 镗孔")
        self._add_tool_change_block(x, y, f"G86 Z{depth:.3f} R2.0 F{feed}")
    
    def _generate_chamfering(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 25)
        y = params.get('Y', 25)
        radius = params.get('R', 5)
        feed = params.get('F', 50)
        
        self.gcode_lines.append("; 倒角")
        self.gcode_lines.append(f"G00 X{x + radius:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z1.0 F500")
        self.gcode_lines.append(f"G01 Z-1.0 F{feed}")
        self.gcode_lines.append(f"G02 X{x:.3f} Y{y + radius:.3f} I{-radius:.3f} J0 F{feed}")
        self.gcode_lines.append(f"G02 X{x - radius:.3f} Y{y:.3f} I0 J{-radius:.3f} F{feed}")
        self.gcode_lines.append(f"G02 X{x:.3f} Y{y - radius:.3f} I{radius:.3f} J0 F{feed}")
        self.gcode_lines.append(f"G02 X{x + radius:.3f} Y{y:.3f} I0 J{radius:.3f} F{feed}")
        self.gcode_lines.append("G01 Z1.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_thread_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 25)
        y = params.get('Y', 25)
        diameter = params.get('D', 10)
        depth = params.get('Z', -10)
        pitch = params.get('P', 1.5)
        feed = params.get('F', 100)
        
        thread_radius = diameter / 2.0
        tool_offset = thread_radius - 0.5
        
        self.gcode_lines.append(f"; 螺纹铣削 - M{diameter}x{pitch}")
        self.gcode_lines.append(f"G00 X{x + tool_offset:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{depth:.3f} F50")
        
        cycles = int(abs(depth) / pitch)
        for i in range(cycles):
            current_z = depth + i * pitch
            self.gcode_lines.append(f"G02 I{-tool_offset:.3f} J0 Z{current_z:.3f} F{feed}")
        
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_deep_hole_drilling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        depth = params.get('Z', -50)
        feed = params.get('F', 50)
        peck_depth = params.get('PECK', 10)
        
        self.gcode_lines.append("; 深孔钻")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        
        current_depth = 0
        while current_depth > depth:
            next_depth = max(current_depth - peck_depth, depth)
            self.gcode_lines.append(f"G01 Z{next_depth:.3f} F{feed}")
            self.gcode_lines.append("G01 Z5.0 F200")
            self.gcode_lines.append(f"G01 Z{next_depth + 2.0:.3f} F200")
            current_depth = next_depth
        
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_zigzag_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x_start = params.get('X', 0)
        y_start = params.get('Y', 0)
        width = params.get('WIDTH', 50)
        height = params.get('HEIGHT', 50)
        depth = params.get('Z', -2)
        feed = params.get('F', 200)
        step_over = params.get('STEP', 5)
        
        self.gcode_lines.append("; 往复铣削")
        self.gcode_lines.append(f"G00 X{x_start:.3f} Y{y_start:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{depth:.3f} F150")
        
        y = y_start
        while y < y_start + height:
            self.gcode_lines.append(f"G01 X{x_start + width:.3f} F{feed}")
            y += step_over
            self.gcode_lines.append(f"G01 Y{min(y, y_start + height):.3f} F500")
            self.gcode_lines.append(f"G01 X{x_start:.3f} F{feed}")
            y += step_over
            self.gcode_lines.append(f"G01 Y{min(y, y_start + height):.3f} F500")
        
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_circle_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 25)
        y = params.get('Y', 25)
        diameter = params.get('D', 10)
        depth = params.get('Z', -5)
        feed = params.get('F', 200)
        
        tool_diameter = self.process_card.tool_info.diameter if self.process_card and self.process_card.tool_info else 8.0
        radius = diameter / 2.0
        tool_radius = tool_diameter / 2.0
        cutter_radius = radius - tool_radius
        
        self.gcode_lines.append("; 圆孔铣削")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append(f"G01 Z{depth:.3f} F100")
        self.gcode_lines.append(f"G02 I{cutter_radius:.3f} J0 F{feed}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")
    
    def _generate_generic_milling(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        z = params.get('Z', -5)
        feed = params.get('F', 100)
        # Safety: ramp entry, never straight plunge
        rx = min(x + 5.0, 50.0)
        ry = min(y + 5.0, 50.0)
        self.gcode_lines.append("; 铣削加工 (安全斜坡进刀)")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z5.0 F500")
        self.gcode_lines.append(f"G01 X{rx:.3f} Y{ry:.3f} Z{z:.3f} F{feed}")
        self.gcode_lines.append("G01 Z2.0 F500")
        self.gcode_lines.append("G00 Z50.0")

    def _generate_rapid_code(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        z = params.get('Z', 50)
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f} Z{z:.3f}")

    def _generate_generic_code(self, op: Operation):
        params = self._parse_parameters(op.parameters)
        x = params.get('X', 0)
        y = params.get('Y', 0)
        z = params.get('Z', 0)
        feed = params.get('F', 100)
        # Safety: if cutting downward, use ramp entry
        if z < 0:
            self.gcode_lines.append("; 安全斜坡进刀 (通用)")
            self.gcode_lines.append(f"G00 X{max(0, x - 3):.3f} Y{max(0, y - 3):.3f}")
            self.gcode_lines.append("G01 Z5.0 F500")
            self.gcode_lines.append(f"G01 X{x:.3f} Y{y:.3f} Z{z:.3f} F{feed}")
        else:
            self.gcode_lines.append(f"G01 X{x:.3f} Y{y:.3f} Z{z:.3f} F{feed}")
    
    def _parse_parameters(self, param_str: str) -> dict:
        params = {}
        if not param_str:
            return params
        
        parts = param_str.split(',')
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                try:
                    params[key.strip()] = float(value.strip())
                except ValueError:
                    params[key.strip()] = value.strip()
        return params
    
    # ---- new: pocket / ramp / wall / floor operations ----

    def _generate_ramp_entry(self, op: Operation):
        """Ramped entry from clearance height to cutting depth.

        Never plunges straight down — always moves X/Y while descending.
        """
        params = self._parse_parameters(op.parameters)
        x = params.get('RAMP_X', params.get('X', 5.0))
        y = params.get('RAMP_Y', params.get('Y', 5.0))
        z_target = params.get('Z', -3.0)
        feed = params.get('F', 200)

        self.gcode_lines.append("; 斜坡进刀 (安全进刀，禁止直插)")
        self.gcode_lines.append(f"G00 X{x:.3f} Y{y:.3f}")
        self.gcode_lines.append("G01 Z5.0 F500")
        self.gcode_lines.append(f"G01 X{x + 3:.3f} Y{y + 3:.3f} Z{z_target:.3f} F{feed}")

    def _generate_pocket_clearing(self, op: Operation):
        """Clear a pocket area at the current Z level (zigzag pattern)."""
        params = self._parse_parameters(op.parameters)
        x_start = params.get('X', 0)
        y_start = params.get('Y', 0)
        x_end = params.get('X_END', 50)
        y_end = params.get('Y_END', 50)
        feed = params.get('F', 300)
        step = params.get('STEP', 7.0)

        # Safety: enforce max 3mm DOC at generator level
        z_current = params.get('Z', 0)
        z_prev = params.get('Z_PREV', 0)
        doc = abs(z_current - z_prev)
        if doc > 0 and doc > 3.0:
            self.gcode_lines.append(f"; !! 安全警告: 切深{doc:.1f}mm超过3mm限制")
            self.gcode_lines.append(f"; !! 已强制限制为分层加工，请检查工序参数")

        self.gcode_lines.append(f"; 型腔清层 Z={z_current:.2f}")
        self.gcode_lines.append(f"G00 X{x_start:.3f} Y{y_start:.3f}")

        y = y_start
        direction = 1
        while y < y_end:
            if direction == 1:
                self.gcode_lines.append(f"G01 X{x_end:.3f} F{feed}")
            else:
                self.gcode_lines.append(f"G01 X{x_start:.3f} F{feed}")
            y += step
            self.gcode_lines.append(f"G01 Y{min(y, y_end):.3f} F500")
            direction *= -1

    def _generate_wall_finish(self, op: Operation):
        """Profile the pocket walls at current Z level with tool radius offset."""
        params = self._parse_parameters(op.parameters)
        w = params.get('WIDTH', 50)
        h = params.get('HEIGHT', 50)
        z = params.get('Z', -3)
        feed = params.get('F', 120)

        # Tool radius compensation: offset inward by half tool diameter
        tool_dia = self.process_card.tool_info.diameter if self.process_card and self.process_card.tool_info else 10.0
        offset = tool_dia / 2.0

        self.gcode_lines.append(f"; 侧壁精修 Z={z:.2f} (刀径补偿{offset:.1f}mm)")
        self.gcode_lines.append(f"G01 X{offset:.3f} Y{offset:.3f} F{feed}")
        self.gcode_lines.append(f"G01 X{w - offset:.3f} F{feed}")
        self.gcode_lines.append(f"G01 Y{h - offset:.3f} F{feed}")
        self.gcode_lines.append(f"G01 X{offset:.3f} F{feed}")
        self.gcode_lines.append(f"G01 Y{offset:.3f} F{feed}")

    def _generate_floor_finish(self, op: Operation):
        """Finish the pocket floor with ramp entry + fine step-over zigzag."""
        params = self._parse_parameters(op.parameters)
        x_start = params.get('X', 5.0)
        y_start = params.get('Y', 5.0)
        x_end = params.get('X_END', 50)
        y_end = params.get('Y_END', 50)
        z = params.get('Z', -65.0)
        feed = params.get('F', 120)
        step = params.get('STEP', 3.5)

        self.gcode_lines.append(f"; 底面精加工 Z={z:.2f} (安全斜坡进刀)")
        self.gcode_lines.append(f"G00 X{x_start - 3:.3f} Y{y_start - 3:.3f}")
        self.gcode_lines.append("G01 Z5.0 F500")
        self.gcode_lines.append(f"G01 X{x_start:.3f} Y{y_start:.3f} Z{z:.2f} F150")

        y = y_start
        direction = 1
        while y < y_end:
            if direction == 1:
                self.gcode_lines.append(f"G01 X{x_end:.3f} F{feed}")
            else:
                self.gcode_lines.append(f"G01 X{x_start:.3f} F{feed}")
            y += step
            self.gcode_lines.append(f"G01 Y{min(y, y_end):.3f} F300")
            direction *= -1

    def _generate_retract(self):
        """Safe retract to clearance height."""
        self.gcode_lines.append("G00 Z50.0")

    def _add_finalization(self):
        self.gcode_lines.append("G00 Z100.0 M09")
        self.gcode_lines.append("M05")
        self.gcode_lines.append("M30")

def generate_gcode(process_card: ProcessCard, operations: list) -> str:
    generator = GCodeGenerator()
    return generator.generate(process_card, operations)