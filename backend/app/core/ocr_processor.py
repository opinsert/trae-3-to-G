import base64
import os
import re

try:
    from aip import AipOcr
    BAIDU_AIP_AVAILABLE = True
    print('[后端-OCR] 百度aip 库已安装')
except ImportError:
    BAIDU_AIP_AVAILABLE = False
    print('[后端-OCR] 百度aip 库未安装')

from app.utils.config import settings

class OCRProcessor:
    def __init__(self):
        self.baidu_client = None
        self._init_baidu_ocr()

    def _init_baidu_ocr(self):
        print('[后端-OCR] ============== 百度OCR 初始化开始 ==============')
        
        if not BAIDU_AIP_AVAILABLE:
            print('[后端-OCR] [FAIL] 百度aip 库未安装')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            return
        
        app_id = settings.baidu_app_id
        api_key = settings.baidu_api_key
        secret_key = settings.baidu_secret_key
        
        if not app_id or not api_key or not secret_key:
            print('[后端-OCR] [FAIL] 百度API密钥未配置')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            return
        
        if app_id == '您的App_ID':
            print('[后端-OCR] [FAIL] 百度API密钥未设置，请在.env文件中配置真实密钥')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            return
        
        try:
            self.baidu_client = AipOcr(app_id, api_key, secret_key)
            print('[后端-OCR] [OK] 百度OCR 初始化成功')
            print('[后端-OCR] ============== 百度OCR 初始化完成 ==============\n')
        except Exception as e:
            print('[后端-OCR] [FAIL] 百度OCR 初始化失败:', str(e))
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')

    def recognize(self, image_data: str) -> dict:
        print('[后端-OCR] ============== OCR 识别开始 ==============')
        print('[后端-OCR] 输入数据长度:', len(image_data), '字符')
        
        if not self.baidu_client:
            print('[后端-OCR] [FAIL] 百度OCR客户端未初始化')
            return self._fallback_recognize(image_data)
        
        return self._recognize_with_baidu(image_data)
    
    def _recognize_with_baidu(self, image_data: str) -> dict:
        try:
            image_bytes = self._decode_image_bytes(image_data)
            print('[后端-OCR] [百度OCR] 图片解码成功，字节数:', len(image_bytes))
            
            result = self.baidu_client.basicGeneral(image_bytes)
            print('[后端-OCR] [百度OCR] API调用成功')
            
            text = ''
            all_words = []
            if 'words_result' in result:
                text_lines = []
                for i, word_info in enumerate(result['words_result']):
                    if 'words' in word_info:
                        word = word_info['words']
                        text_lines.append(word)
                        all_words.append(word)
                        if i < 10:
                            print('[后端-OCR] [百度OCR] 文字块', i+1, ':', word)
                text = '\n'.join(text_lines)
            
            print('[后端-OCR] [百度OCR] 识别完成，文字长度:', len(text))
            
            parsed_result = self._parse_text(all_words)
            parsed_result['raw_text'] = text
            
            print('[后端-OCR] ============== OCR 识别成功 ==============\n')
            return parsed_result
            
        except Exception as e:
            print('[后端-OCR] [FAIL] 百度OCR 识别失败:', str(e))
            import traceback
            print('[后端-OCR] 错误堆栈:\n', traceback.format_exc())
            return self._fallback_recognize(image_data)
    
    def _decode_image_bytes(self, image_data: str) -> bytes:
        if image_data.startswith('data:image/'):
            print('[后端-OCR] [解码] 检测到 data URL，提取 base64 数据')
            image_data = image_data.split(',')[1]
        return base64.b64decode(image_data)
    
    def _parse_text(self, all_words: list) -> dict:
        print('[后端-OCR] [解析] 开始解析识别文本')
        print('[后端-OCR] [解析] 识别到', len(all_words), '个文字块')
        
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
            'steps': []
        }
        
        step_keywords = ['铣削', '车削', '钻孔', '攻丝', '铰孔', '镗孔', '磨削', '倒角', '开槽', '精铣', '粗铣']
        equipment_keywords = ['铣床', '车床', '磨床', '加工中心', '钻床', '镗床']
        material_keywords = ['铸件', '钢', '铁', '铝', '铜', '合金', '不锈钢', '碳钢']
        control_system_keywords = ['Fanuc', 'fanuc', 'SIEMENS', 'Siemens', 'siemens', 'FANUC', 'CNC']
        tool_keywords = ['铣刀', '钻头', '丝锥', '铰刀', '镗刀', '砂轮', '刀片']
        
        numbers = []
        texts = []
        
        for word in all_words:
            if word.replace('.', '').isdigit() and word.count('.') <= 1:
                numbers.append(word)
            else:
                texts.append(word)
        
        print('[后端-OCR] [解析] 数字:', numbers)
        print('[后端-OCR] [解析] 文本:', texts)
        
        merged_line = ' '.join(all_words)
        print('[后端-OCR] [解析] 合并文本:', merged_line)
        
        for word in texts:
            if not extracted['process_name']:
                for kw in step_keywords:
                    if kw in word:
                        extracted['process_name'] = kw
                        print(f'[后端-OCR] [解析] 字段[process_name] = [{kw}]')
                        break
            
            if not extracted['equipment']:
                for kw in equipment_keywords:
                    if kw in word:
                        extracted['equipment'] = kw
                        print(f'[后端-OCR] [解析] 字段[equipment] = [{kw}]')
                        break
            
            if not extracted['material']:
                for kw in material_keywords:
                    if kw in word:
                        extracted['material'] = kw
                        print(f'[后端-OCR] [解析] 字段[material] = [{kw}]')
                        break
            
            if not extracted['control_system']:
                for kw in control_system_keywords:
                    if kw in word:
                        extracted['control_system'] = kw
                        print(f'[后端-OCR] [解析] 字段[control_system] = [{kw}]')
                        break
            
            if not extracted['tool_name']:
                for kw in tool_keywords:
                    if kw in word:
                        extracted['tool_name'] = kw
                        print(f'[后端-OCR] [解析] 字段[tool_name] = [{kw}]')
                        break
        
        if numbers:
            extracted['process_number'] = numbers[0]
            
            for num in numbers:
                try:
                    val = float(num)
                    if 0.1 <= val <= 50 and not extracted['tool_diameter']:
                        extracted['tool_diameter'] = val
                        print(f'[后端-OCR] [解析] 字段[tool_diameter] = [{val}]')
                    elif val > 100 and val <= 5000 and not extracted['tool_length']:
                        extracted['tool_length'] = val
                        print(f'[后端-OCR] [解析] 字段[tool_length] = [{val}]')
                except:
                    pass
        
        extracted['steps'] = self._extract_steps(all_words)
        
        return extracted

    def _extract_steps(self, all_words: list) -> list:
        steps = []
        
        step_keywords = ['铣削', '车削', '钻孔', '攻丝', '铰孔', '镗孔', '磨削', '倒角', '开槽', '精铣', '粗铣']
        numbers = []
        detected_steps = []
        
        for word in all_words:
            if word.replace('.', '').isdigit():
                numbers.append(word)
            else:
                for kw in step_keywords:
                    if kw in word:
                        detected_steps.append(kw)
        
        for i, step_content in enumerate(detected_steps):
            steps.append({
                'sequence': i + 1,
                'content': step_content,
                'parameters': '',
                'equipment': '',
                'remark': '',
                'drawing_ref': ''
            })
        
        if not steps and numbers:
            for i in range(min(3, len(numbers))):
                steps.append({
                    'sequence': i + 1,
                    'content': '铣削',
                    'parameters': '',
                    'equipment': '',
                    'remark': '',
                    'drawing_ref': ''
                })
        
        return steps

    def _fallback_recognize(self, image_data: str) -> dict:
        print('[后端-OCR] [备用] 百度OCR不可用')
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
            'steps': [],
            'raw_text': '',
            'error': '百度OCR服务不可用，请先配置百度API密钥'
        }

def ocr_recognize(image_data: str) -> dict:
    print('[后端-OCR] [入口] 调用 ocr_recognize 函数')
    processor = OCRProcessor()
    return processor.recognize(image_data)