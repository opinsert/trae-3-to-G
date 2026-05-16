import base64
import io
from PIL import Image

class OCRProcessor:
    def __init__(self, lang='ch'):
        self.lang = lang
        self.ocr = None
    
    def _init_ocr(self):
        if self.ocr is None:
            try:
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False
                )
                return True
            except Exception as e:
                print(f"PaddleOCR初始化失败: {e}")
                return False
    
    def recognize(self, image_data: str) -> dict:
        if not self._init_ocr():
            return self._fallback_recognize(image_data)
        
        try:
            image = self._decode_image(image_data)
            result = self.ocr.ocr(image, cls=True)
            return self._parse_result(result)
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return self._fallback_recognize(image_data)
    
    def _decode_image(self, image_data: str) -> str:
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        temp_path = 'temp_ocr_image.jpg'
        image.save(temp_path)
        return temp_path
    
    def _parse_result(self, result: list) -> dict:
        extracted = {
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
            'operations': [],
            'raw_text': ''
        }
        
        all_text = ''
        lines = []
        
        for page in result:
            for line in page:
                text = line[1][0]
                confidence = line[1][1]
                if confidence > 0.5:
                    all_text += text + '\n'
                    lines.append(text)
        
        extracted['raw_text'] = all_text
        
        keywords = {
            'product_name': ['产品名称', '产品名', '产品'],
            'process_name': ['工序名称', '工序名', '工序'],
            'process_number': ['工序编号', '编号', '工单号', '工序号'],
            'version': ['版本号', '版本', '版次', 'Rev'],
            'equipment': ['设备名称', '设备', '机床', '加工中心'],
            'control_system': ['数控系统', '系统', '控制系统', 'CNC'],
            'fixture': ['夹具名称', '夹具'],
            'material': ['材料名称', '材料', '材质'],
            'tool_name': ['刀具名称', '刀具', '刀'],
            'tool_length': ['长度', '刀长', '总长'],
            'tool_diameter': ['直径', '刀径', '直径φ']
        }
        
        for field, keys in keywords.items():
            for key in keys:
                for line in lines:
                    if key in line:
                        value = self._extract_value_from_line(line, key)
                        if value and (not extracted[field] or len(value) > len(str(extracted[field]))):
                            extracted[field] = value
        
        try:
            extracted['tool_length'] = float(extracted['tool_length']) if extracted['tool_length'] else 0
            extracted['tool_diameter'] = float(extracted['tool_diameter']) if extracted['tool_diameter'] else 0
        except ValueError:
            extracted['tool_length'] = 0
            extracted['tool_diameter'] = 0
        
        extracted['operations'] = self._extract_operations(lines)
        
        return extracted
    
    def _extract_value_from_line(self, line: str, key: str) -> str:
        end_chars = ['：', ':', '，', ',', '。', '.', '\n', ' ', '、', '=']
        idx = line.find(key)
        if idx == -1:
            return ''
        
        start_idx = idx + len(key)
        
        while start_idx < len(line) and line[start_idx] in ['：', ':', ' ', '=']:
            start_idx += 1
        
        value = ''
        i = start_idx
        while i < len(line):
            if line[i] in end_chars:
                break
            value += line[i]
            i += 1
        
        return value.strip()
    
    def _extract_operations(self, lines: list) -> list:
        operations = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            if line_stripped.startswith(tuple(f'{i}.' for i in range(1, 21))) or \
               line_stripped.startswith(tuple(f'{i}、' for i in range(1, 21))):
                
                parts = line_stripped.split('、') if '、' in line_stripped else line_stripped.split('.', 1)
                if len(parts) >= 2:
                    try:
                        seq_part = parts[0].strip()
                        seq = int(''.join([c for c in seq_part if c.isdigit()]))
                        content = parts[1].strip()
                        if content:
                            operations.append({
                                'sequence': seq,
                                'content': content,
                                'parameters': '',
                                'equipment': '',
                                'remark': ''
                            })
                    except ValueError:
                        pass
        
        return operations
    
    def _fallback_recognize(self, image_data: str) -> dict:
        return {
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
            'operations': [],
            'raw_text': '',
            'error': 'OCR服务不可用，请手动输入工序卡信息'
        }

def ocr_recognize(image_data: str) -> dict:
    processor = OCRProcessor()
    return processor.recognize(image_data)
