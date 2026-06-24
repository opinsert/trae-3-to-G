import base64
import json
import os
import re
import requests
import traceback

from app.utils.config import settings

class OCRProcessor:
    def __init__(self):
        self.baidu_api_key = None
        self.baidu_secret_key = None
        self.access_token = None
        self.vision_ocr_api_key = settings.vision_ocr_api_key
        self.vision_ocr_base_url = settings.vision_ocr_base_url.rstrip('/')
        self.vision_ocr_model = settings.vision_ocr_model
        self.vision_ocr_timeout = settings.vision_ocr_timeout
        self.vision_ocr_enabled = settings.vision_ocr_enabled
        self._init_baidu_ocr()

    def _init_baidu_ocr(self):
        print('[后端-OCR] ============== 百度OCR 初始化开始 ==============')
        
        self.baidu_api_key = settings.baidu_api_key
        self.baidu_secret_key = settings.baidu_secret_key
        
        if not self.baidu_api_key or not self.baidu_secret_key:
            print('[后端-OCR] [FAIL] 百度API密钥未配置')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            return
        
        if self.baidu_api_key == '您的API_Key':
            print('[后端-OCR] [FAIL] 百度API密钥未设置，请在.env文件中配置真实密钥')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            return
        
        # 获取访问令牌
        print('[后端-OCR] [OK] 正在获取百度OCR访问令牌...')
        self.access_token = self._get_access_token()
        
        if self.access_token:
            print('[后端-OCR] [OK] 百度OCR 初始化成功')
            print('[后端-OCR] ============== 百度OCR 初始化完成 ==============\n')
        else:
            print('[后端-OCR] [FAIL] 获取访问令牌失败')
            print('[后端-OCR] ============== 百度OCR 初始化失败 ==============\n')
            self.baidu_client = None

    def _get_access_token(self):
        """获取百度OCR访问令牌"""
        url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.baidu_api_key,
            'client_secret': self.baidu_secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get('access_token')
            else:
                print('[后端-OCR] [FAIL] 获取Token失败，状态码:', response.status_code)
                return None
        except Exception as e:
            print('[后端-OCR] [FAIL] 获取Token异常:', str(e))
            return None

    def recognize(self, image_data: str) -> dict:
        print('[后端-OCR] ============== OCR 识别开始 ==============')
        print('[后端-OCR] 输入数据长度:', len(image_data), '字符')

        vision_ocr_configured = (
            self.vision_ocr_enabled
            and self.vision_ocr_api_key
            and self.vision_ocr_api_key != '您的_OpenClawPlan_API_Key'
            and self.vision_ocr_model
        )

        if vision_ocr_configured:
            print('[后端-OCR] [视觉模型] 尝试使用 OpenClawPlan 视觉OCR...')
            vision_result = self._recognize_with_vision_model(image_data)
            if self._has_valid_ocr_data(vision_result):
                print('[后端-OCR] ============== OCR 识别成功 (OpenClawPlan视觉模型) ==============\n')
                return vision_result
            print('[后端-OCR] [视觉模型] 未获得有效结构化数据，切换到百度OCR')
        elif self.vision_ocr_api_key == '您的_OpenClawPlan_API_Key':
            print('[后端-OCR] [视觉模型] API Key仍是示例占位符，跳过')
        else:
            print('[后端-OCR] [视觉模型] 未启用或未配置API Key/模型名，跳过')

        if not self.access_token:
            print('[后端-OCR] [FAIL] 百度OCR访问令牌未获取')
            return self._fallback_recognize(image_data)

        return self._recognize_with_baidu(image_data)

    def _recognize_with_vision_model(self, image_data: str) -> dict:
        try:
            image_url = image_data if image_data.startswith('data:image/') else f'data:image/png;base64,{image_data}'
            url = f'{self.vision_ocr_base_url}/v1/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.vision_ocr_api_key}'
            }
            data = {
                'model': self.vision_ocr_model,
                'messages': [
                    {
                        'role': 'system',
                        'content': '你是专业的机械加工工序卡OCR与结构化信息提取助手，只输出JSON。'
                    },
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': self._build_vision_prompt()},
                            {'type': 'image_url', 'image_url': {'url': image_url}}
                        ]
                    }
                ],
                'temperature': 0.1,
                'response_format': {'type': 'json_object'}
            }

            print('[后端-OCR] [视觉模型] 请求URL:', url)
            print('[后端-OCR] [视觉模型] 使用模型:', self.vision_ocr_model)
            response = requests.post(url, headers=headers, json=data, timeout=self.vision_ocr_timeout)

            if response.status_code >= 400 and 'response_format' in data:
                print('[后端-OCR] [视觉模型] 带response_format请求失败，状态码:', response.status_code)
                print('[后端-OCR] [视觉模型] 重试不带response_format参数')
                data.pop('response_format', None)
                response = requests.post(url, headers=headers, json=data, timeout=self.vision_ocr_timeout)

            if response.status_code != 200:
                print('[后端-OCR] [视觉模型] 请求失败，状态码:', response.status_code)
                print('[后端-OCR] [视觉模型] 响应内容:', response.text[:500])
                return {}

            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                print('[后端-OCR] [视觉模型] 响应中未找到message.content')
                return {}

            parsed = self._extract_json_from_model_response(content)
            normalized = self._normalize_vision_result(parsed)
            normalized['raw_text'] = content
            normalized['table_data'] = None
            normalized['table_error'] = None

            print('[后端-OCR] [视觉模型] 识别结果汇总:')
            self._print_parsed_result(normalized)
            return normalized
        except Exception as e:
            print('[后端-OCR] [视觉模型] 识别异常:', str(e))
            return {}

    def _build_vision_prompt(self) -> str:
        return '''请识别图片中的机械加工工序卡/工艺卡表格，并只返回一个合法JSON对象。不要输出Markdown、解释或代码块。

字段必须包含：
{
  "product_name": "",
  "process_name": "",
  "process_number": "",
  "version": "",
  "equipment": "",
  "control_system": "",
  "fixture": "",
  "material": "",
  "tool_name": "",
  "tool_length": 0,
  "tool_diameter": 0,
  "workshop": "",
  "process_card_number": "",
  "material_grade": "",
  "blank_type": "",
  "blank_size": "",
  "blank_available_pieces": null,
  "pieces_per_machine": null,
  "equipment_model": "",
  "equipment_no": "",
  "simultaneous_pieces": null,
  "fixture_no": "",
  "cutting_fluid": "",
  "station_tool_no": "",
  "station_tool_name": "",
  "preparation_time": null,
  "unit_time": null,
  "drawing_steps": [
    {
      "step": 1,
      "step_content": "",
      "tooling": "",
      "spindle_speed": null,
      "cutting_speed": null,
      "feed_rate": null,
      "depth_of_cut": null,
      "feed_count": null,
      "machine_time": null,
      "auxiliary_time": null,
      "remark": ""
    }
  ],
  "steps": []
}

要求：
1. 保持字段名完全一致。
2. 未识别的文本字段填空字符串。
3. 未识别的数字字段填null；tool_length和tool_diameter未识别时填0。
4. drawing_steps按工步表逐行提取，数值字段只保留数字，不要带单位。
5. steps保留为空数组即可，除非图片中有旧格式工步信息。
6. 不要猜测图片中没有的信息。'''

    def _extract_json_from_model_response(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', content)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError as e:
                print('[后端-OCR] [视觉模型] JSON截取解析失败:', str(e))

        print('[后端-OCR] [视觉模型] 未能从响应中解析JSON')
        return {}

    def _has_valid_ocr_data(self, parsed: dict) -> bool:
        if not isinstance(parsed, dict):
            return False
        drawing_steps = parsed.get('drawing_steps', [])
        return any([
            parsed.get('process_name'),
            parsed.get('process_card_number'),
            parsed.get('material_grade'),
            parsed.get('equipment'),
            parsed.get('equipment_model'),
            isinstance(drawing_steps, list) and len(drawing_steps) > 0
        ])

    def _normalize_vision_result(self, parsed: dict) -> dict:
        if not isinstance(parsed, dict):
            parsed = {}

        normalized = self._ensure_full_fields(parsed)
        normalized['tool_length'] = self._to_number(normalized.get('tool_length'), 0)
        normalized['tool_diameter'] = self._to_number(normalized.get('tool_diameter'), 0)

        nullable_number_fields = [
            'blank_available_pieces', 'pieces_per_machine', 'simultaneous_pieces',
            'preparation_time', 'unit_time'
        ]
        for field in nullable_number_fields:
            normalized[field] = self._to_number(normalized.get(field), None)

        normalized['drawing_steps'] = self._normalize_drawing_steps(normalized.get('drawing_steps'))
        if not isinstance(normalized.get('steps'), list):
            normalized['steps'] = []

        return normalized

    def _normalize_drawing_steps(self, steps: list) -> list:
        if not isinstance(steps, list):
            return []

        normalized_steps = []
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            normalized_step = {
                'step': self._to_int(step.get('step'), index + 1),
                'step_content': str(step.get('step_content') or step.get('content') or ''),
                'tooling': str(step.get('tooling') or step.get('equipment') or ''),
                'spindle_speed': self._to_number(step.get('spindle_speed'), None),
                'cutting_speed': self._to_number(step.get('cutting_speed'), None),
                'feed_rate': self._to_number(step.get('feed_rate'), None),
                'depth_of_cut': self._to_number(step.get('depth_of_cut'), None),
                'feed_count': self._to_number(step.get('feed_count'), None),
                'machine_time': self._to_number(step.get('machine_time'), None),
                'auxiliary_time': self._to_number(step.get('auxiliary_time'), None),
                'remark': str(step.get('remark') or '')
            }
            if any(normalized_step.get(field) not in (None, '') for field in normalized_step if field != 'step'):
                normalized_steps.append(normalized_step)
        return normalized_steps

    def _to_number(self, value, default=None):
        if value is None or value == '':
            return default
        if isinstance(value, (int, float)):
            return value
        try:
            text = str(value).strip()
            match = re.search(r'-?\d+(?:\.\d+)?', text)
            if not match:
                return default
            number = float(match.group(0))
            return int(number) if number.is_integer() else number
        except (ValueError, TypeError):
            return default

    def _to_int(self, value, default=0):
        number = self._to_number(value, default)
        try:
            return int(number)
        except (ValueError, TypeError):
            return default

    def _recognize_with_baidu(self, image_data: str) -> dict:
        try:
            image_bytes = self._decode_image_bytes(image_data)
            print('[后端-OCR] [百度OCR] 图片解码成功，字节数:', len(image_bytes))
            
            # 主要调用表格识别V2
            print('[后端-OCR] [百度OCR] [主要] 开始表格识别V2...')
            table_result = self._call_table_recognition_v2(image_bytes)
            print('[后端-OCR] [百度OCR] [主要] 表格识别API调用完成')
            
            # 检查表格识别是否成功
            table_has_error = table_result.get('error_code') is not None
            if table_has_error:
                print('[后端-OCR] [百度OCR] [主要] 表格识别失败! 错误码:', table_result.get('error_code'), 
                      '错误信息:', table_result.get('error_msg', ''))
                
                # 表格识别失败，回退到通用识别
                print('[后端-OCR] [百度OCR] [回退] 表格识别失败，调用通用文字识别...')
                return self._recognize_with_general_fallback(image_bytes, table_result)
            
            # 表格识别成功，解析表格数据
            print('[后端-OCR] [百度OCR] [主要] 表格识别成功，开始解析数据...')
            table_parsed = self._parse_table_data(table_result)
            
            # 检查表格解析是否有有效数据
            new_fields = ['workshop', 'process_card_number', 'material_grade', 'blank_type', 
                         'blank_size', 'blank_available_pieces', 'pieces_per_machine', 
                         'equipment_model', 'equipment_no', 'simultaneous_pieces', 
                         'fixture_no', 'cutting_fluid', 'station_tool_no', 
                         'station_tool_name', 'preparation_time', 'unit_time', 'drawing_steps']
            
            table_has_valid_data = any([
                table_parsed.get('process_number'),
                table_parsed.get('material'),
                table_parsed.get('equipment'),
                table_parsed.get('control_system'),
                len(table_parsed.get('steps', [])) > 0,
                len(table_parsed.get('drawing_steps', [])) > 0
            ] + [table_parsed.get(field) for field in new_fields if table_parsed.get(field)])
            
            if table_has_valid_data:
                print('[后端-OCR] [百度OCR] [主要] 表格识别有有效数据，使用表格识别结果')
                
                # 完善表格结果，确保所有字段都存在
                parsed_result = self._ensure_full_fields(table_parsed)
                parsed_result['raw_text'] = ''
                parsed_result['table_data'] = table_result
                parsed_result['table_error'] = None
                
                print('[后端-OCR] [百度OCR] [主要] 表格识别结果汇总:')
                self._print_parsed_result(parsed_result)
                
                print('[后端-OCR] ============== OCR 识别成功 (表格识别V2) ==============\n')
                return parsed_result
            else:
                print('[后端-OCR] [百度OCR] [回退] 表格识别无有效数据，调用通用文字识别补充...')
                return self._recognize_with_general_fallback(image_bytes, table_result)
            
        except Exception as e:
            print('[后端-OCR] [FAIL] 百度OCR 识别失败:', str(e))
            print('[后端-OCR] 错误堆栈:\n', traceback.format_exc())
            return self._fallback_recognize(image_data)
    
    def _call_table_recognition_v2(self, image_bytes: bytes) -> dict:
        """直接调用百度表格文字识别V2 API"""
        url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/table'
        
        # 图片base64编码
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 使用表单编码发送请求
        data = {
            'image': image_base64,
            'access_token': self.access_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print('[后端-OCR] [ERROR] 表格识别V2请求失败，状态码:', response.status_code)
                return {'error_code': response.status_code, 'error_msg': 'HTTP请求失败'}
        except Exception as e:
            print('[后端-OCR] [ERROR] 表格识别V2请求异常:', str(e))
            return {'error_code': -1, 'error_msg': str(e)}
    
    def _recognize_with_general_fallback(self, image_bytes: bytes, table_result: dict = None) -> dict:
        """表格识别失败时的回退处理，调用通用文字识别"""
        try:
            print('[后端-OCR] [百度OCR] [回退] 调用通用文字识别...')
            
            # 直接调用百度通用文字识别API
            url = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
            
            # 图片base64编码
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 使用表单编码发送请求
            data = {
                'image': image_base64,
                'access_token': self.access_token
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=data, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print('[后端-OCR] [ERROR] 通用文字识别请求失败，状态码:', response.status_code)
                return self._fallback_recognize(base64.b64encode(image_bytes).decode('utf-8'))
            
            general_result = response.json()
            print('[后端-OCR] [百度OCR] [回退] 通用文字识别API调用完成')
            
            # 解析通用识别结果
            text = ''
            all_words = []
            if 'words_result' in general_result:
                text_lines = []
                for i, word_info in enumerate(general_result['words_result']):
                    if isinstance(word_info, dict) and 'words' in word_info:
                        text_lines.append(word_info['words'])
                        all_words.append(word_info['words'])
                text = '\n'.join(text_lines)
            
            print('[后端-OCR] [百度OCR] [回退] 通用识别完成，文字长度:', len(text))
            
            # 解析通用识别结果
            text_parsed = self._parse_text(all_words)
            
            # 如果有表格结果，尝试从表格中提取能提取的字段作为补充
            if table_result and not table_result.get('error_code'):
                print('[后端-OCR] [百度OCR] [回退] 尝试从表格识别中补充字段...')
                try:
                    table_parsed = self._parse_table_data(table_result)
                    # 表格有的字段用表格结果覆盖
                    for key in text_parsed.keys():
                        if table_parsed.get(key):
                            text_parsed[key] = table_parsed[key]
                except Exception as e:
                    print('[后端-OCR] [百度OCR] [回退] 补充表格数据失败:', str(e))
            
            text_parsed['raw_text'] = text
            text_parsed['table_data'] = table_result
            text_parsed['table_error'] = '表格识别失败，使用通用识别' if table_result and table_result.get('error_code') else None
            
            print('[后端-OCR] [百度OCR] [回退] 通用识别结果汇总:')
            self._print_parsed_result(text_parsed)
            
            print('[后端-OCR] ============== OCR 识别成功 (通用识别回退) ==============\n')
            return text_parsed
            
        except Exception as e:
            print('[后端-OCR] [百度OCR] [回退] 通用识别也失败:', str(e))
            print('[后端-OCR] 错误堆栈:\n', traceback.format_exc())
            fallback = self._fallback_recognize(base64.b64encode(image_bytes).decode())
            fallback['ocr_error'] = f'百度OCR识别失败: {type(e).__name__}: {e}'
            return fallback
    
    def _ensure_full_fields(self, parsed: dict) -> dict:
        """确保返回结果包含所有必需字段"""
        result = {
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
            'workshop': '',
            'process_card_number': '',
            'material_grade': '',
            'blank_type': '',
            'blank_size': '',
            'blank_available_pieces': '',
            'pieces_per_machine': '',
            'equipment_model': '',
            'equipment_no': '',
            'simultaneous_pieces': '',
            'fixture_no': '',
            'cutting_fluid': '',
            'station_tool_no': '',
            'station_tool_name': '',
            'preparation_time': '',
            'unit_time': '',
            'drawing_steps': []
        }
        
        # 用解析结果填充
        for key, value in parsed.items():
            if key in result and value is not None:
                result[key] = value
        
        return result
    
    def _print_parsed_result(self, parsed: dict):
        """打印解析结果汇总"""
        print('[后端-OCR]  - 产品名称:', parsed.get('product_name', ''))
        print('[后端-OCR]  - 工序名称:', parsed.get('process_name', ''))
        print('[后端-OCR]  - 设备名称:', parsed.get('equipment', ''))
        print('[后端-OCR]  - 数控系统:', parsed.get('control_system', ''))
        print('[后端-OCR]  - 材料名称:', parsed.get('material', ''))
        print('[后端-OCR]  - 工序编号:', parsed.get('process_number', ''))
        print('[后端-OCR]  - 工步数量:', len(parsed.get('steps', [])))
        print('[后端-OCR]  - DrawingStep数量:', len(parsed.get('drawing_steps', [])))
        # 打印部分新字段
        if parsed.get('workshop'):
            print('[后端-OCR]  - 车间:', parsed.get('workshop'))
        if parsed.get('material_grade'):
            print('[后端-OCR]  - 材料牌号:', parsed.get('material_grade'))
        if parsed.get('equipment_model'):
            print('[后端-OCR]  - 设备型号:', parsed.get('equipment_model'))
    
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
            'steps': [],
            'workshop': '',
            'process_card_number': '',
            'material_grade': '',
            'blank_type': '',
            'blank_size': '',
            'blank_available_pieces': '',
            'pieces_per_machine': '',
            'equipment_model': '',
            'equipment_no': '',
            'simultaneous_pieces': '',
            'fixture_no': '',
            'cutting_fluid': '',
            'station_tool_no': '',
            'station_tool_name': '',
            'preparation_time': '',
            'unit_time': '',
            'drawing_steps': []
        }
        
        step_keywords = ['铣削', '车削', '钻孔', '攻丝', '铰孔', '镗孔', '磨削', '倒角', '开槽', '精铣', '粗铣']
        equipment_keywords = ['铣床', '车床', '磨床', '加工中心', '钻床', '镗床']
        material_keywords = ['铸件', '钢', '铁', '铝', '铜', '合金', '不锈钢', '碳钢']
        control_system_keywords = ['Fanuc', 'fanuc', 'SIEMENS', 'Siemens', 'siemens', 'FANUC', 'CNC']
        tool_keywords = ['铣刀', '钻头', '丝锥', '铰刀', '镗刀', '砂轮', '刀片']
        
        new_field_patterns = {
            'workshop': ['车间'],
            'process_card_number': ['工序号'],
            'process_name': ['工序名称'],
            'material_grade': ['材料牌号', '材料号'],
            'blank_type': ['毛坯种类'],
            'blank_size': ['毛坯外形尺寸', '外形尺寸'],
            'blank_available_pieces': ['毛坯还可制件数', '还可制件数', '每毛坯可制件数'],
            'pieces_per_machine': ['每台件数'],
            'equipment': ['设备名称'],
            'equipment_model': ['设备型号'],
            'equipment_no': ['设备编号'],
            'simultaneous_pieces': ['同时加工件数'],
            'fixture_no': ['夹具编号'],
            'fixture': ['夹具名称'],
            'cutting_fluid': ['切削液'],
            'station_tool_no': ['工位器具编号'],
            'station_tool_name': ['工位器具名称'],
            'preparation_time': ['准终工时', '准终'],
            'unit_time': ['单件工时', '单件']
        }
        
        label_blacklist = [
            '车间', '工序号', '工序名称', '材料牌号', '材料号', '毛坯种类', '毛坯外形尺寸',
            '外形尺寸', '毛坯还可制件数', '还可制件数', '每毛坯可制件数', '每台件数',
            '设备名称', '设备型号', '设备编号', '同时加工件数', '夹具编号', '夹具名称',
            '切削液', '工序工时', '工位器具编号', '工位器具名称', '准终', '单件',
            '工步', '工步内', '工步内容', '工艺装备', '主轴转速',
            '切削速度', '进给量', '被吃刀量', '工时', '次数', '机动', '辅助',
            '设计', '校对', '审核', '标准化', '会签', '工序名称材料号', '工序号工序名称材料号',
            '毛坯种类外形尺寸', '夹具编号夹具名称', '设备名称设备型号', '每台件数切削液'
        ]
        
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
        
        print(f'[后端-OCR] [解析] 尝试智能配对标签和值...')
        
        # 特殊处理合并标签：工序号工序名称材料号
        for i, word in enumerate(all_words):
            if '工序号工序名称材料号' in word:
                # 找到合并标签后，向后找三个值分别给工序号、工序名称和材料牌号
                values_found = []
                for j in range(i + 1, len(all_words)):
                    candidate = all_words[j].strip()
                    if candidate and candidate not in label_blacklist:
                        # 跳过可能是图纸尺寸的小数字（小于100的数字）
                        if candidate.replace('.', '').isdigit():
                            try:
                                num_val = float(candidate)
                                if num_val < 100 and num_val != 0:
                                    print(f'[后端-OCR] [解析] 跳过图纸尺寸: [{candidate}]')
                                    continue
                            except:
                                pass
                        values_found.append(candidate)
                        if len(values_found) == 3:
                            break
                
                if len(values_found) >= 1:
                    extracted['process_card_number'] = values_found[0]
                    print(f'[后端-OCR] [解析] 合并标签处理(工序号工序名称材料号): 工序号 = [{values_found[0]}]')
                if len(values_found) >= 2:
                    extracted['process_name'] = values_found[1]
                    print(f'[后端-OCR] [解析] 合并标签处理(工序号工序名称材料号): 工序名称 = [{values_found[1]}]')
                if len(values_found) >= 3:
                    extracted['material_grade'] = values_found[2]
                    print(f'[后端-OCR] [解析] 合并标签处理(工序号工序名称材料号): 材料牌号 = [{values_found[2]}]')
        
        # 特殊处理合并标签：工序名称材料号
        for i, word in enumerate(all_words):
            if '工序名称材料号' in word and not extracted['process_name'] and not extracted['material_grade']:
                # 找到合并标签后，向后找两个值分别给工序名称和材料牌号
                values_found = []
                for j in range(i + 1, len(all_words)):
                    candidate = all_words[j].strip()
                    if candidate and candidate not in label_blacklist:
                        values_found.append(candidate)
                        if len(values_found) == 2:
                            break
                
                if len(values_found) >= 1:
                    extracted['process_name'] = values_found[0]
                    print(f'[后端-OCR] [解析] 合并标签处理(工序名称材料号): 工序名称 = [{values_found[0]}]')
                if len(values_found) >= 2:
                    extracted['material_grade'] = values_found[1]
                    print(f'[后端-OCR] [解析] 合并标签处理(工序名称材料号): 材料牌号 = [{values_found[1]}]')
        
        label_positions = {}
        for i, word in enumerate(all_words):
            for field, keywords in new_field_patterns.items():
                for kw in keywords:
                    if kw in word:
                        label_positions[field] = i
                        print(f'[后端-OCR] [解析] 发现标签[{kw}]在位置{i}')
                        break
        
        # 定义需要优先选择非数字值的字段
        prefer_non_numeric_fields = ['workshop', 'process_name', 'material', 'equipment', 'control_system']
        
        for field, pos in label_positions.items():
            if not extracted[field]:
                value = None
                numeric_value = None
                
                for i in range(pos + 1, len(all_words)):
                    candidate = all_words[i].strip()
                    if candidate and candidate not in label_blacklist:
                        if candidate.replace('.', '').isdigit():
                            if not numeric_value:
                                numeric_value = candidate
                        else:
                            value = candidate
                            break
                
                # 如果需要优先非数字值但没找到，使用数字值
                if not value and numeric_value and field not in prefer_non_numeric_fields:
                    value = numeric_value
                
                if value:
                    extracted[field] = value
                    print(f'[后端-OCR] [解析] 字段[{field}] = [{value}] (从位置{pos}向后找到)')
                else:
                    print(f'[后端-OCR] [解析] 跳过字段[{field}]，未找到有效值')
        
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
                except (ValueError, TypeError):
                    print(f'[后端-OCR] [解析] 无法将 [{num}] 转换为数字，跳过')
        
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

    def _parse_table_data(self, table_result: dict) -> dict:
        """解析百度表格识别V2结果"""
        print('[后端-OCR] [表格解析] ===== 开始解析表格识别数据 =====')
        
        result = {
            'product_name': '',
            'process_name': '',
            'process_number': '',
            'equipment': '',
            'control_system': '',
            'fixture': '',
            'material': '',
            'tool_name': '',
            'tool_length': 0,
            'tool_diameter': 0,
            'steps': [],
            'workshop': '',
            'process_card_number': '',
            'material_grade': '',
            'blank_type': '',
            'blank_size': '',
            'blank_available_pieces': '',
            'pieces_per_machine': '',
            'equipment_model': '',
            'equipment_no': '',
            'simultaneous_pieces': '',
            'fixture_no': '',
            'cutting_fluid': '',
            'station_tool_no': '',
            'station_tool_name': '',
            'preparation_time': '',
            'unit_time': '',
            'drawing_steps': []
        }
        
        # 打印表格识别完整结果（用于调试）
        print('[后端-OCR] [表格解析] 表格识别原始结果:', str(table_result)[:600])
        
        # 尝试不同的表格数据结构 - 百度表格识别V2可能的返回格式
        tables = []
        
        # 百度表格识别V2常见路径
        if 'result' in table_result:
            result_data = table_result.get('result', {})
            if isinstance(result_data, list):
                tables = result_data
            elif isinstance(result_data, dict) and 'tables' in result_data:
                tables = result_data.get('tables', [])
            elif isinstance(result_data, dict) and 'table' in result_data:
                tables = [result_data.get('table', {})]
            print('[后端-OCR] [表格解析] 使用result路径，表格数量:', len(tables))
        elif 'tables' in table_result:
            tables = table_result.get('tables', [])
            print('[后端-OCR] [表格解析] 使用tables路径，表格数量:', len(tables))
        elif 'table' in table_result:
            tables = [table_result.get('table', {})]
            print('[后端-OCR] [表格解析] 使用table路径')
        elif 'table_result' in table_result:
            tables = [table_result.get('table_result', {})]
            print('[后端-OCR] [表格解析] 使用table_result路径')
        else:
            print('[后端-OCR] [表格解析] 无法识别表格数据结构')
            return result
        
        if not tables:
            print('[后端-OCR] [表格解析] 未找到表格数据')
            return result
        
        print(f'[后端-OCR] [表格解析] 发现 {len(tables)} 个表格')
        
        # 遍历所有表格
        for table_idx, table in enumerate(tables):
            print(f'\n[后端-OCR] [表格解析] -------- 处理表格 {table_idx + 1} --------')
            
            # 尝试不同的单元格数据结构
            rows = []
            
            if 'body' in table:
                rows = table.get('body', [])
                print(f'[后端-OCR] [表格解析] 表格{table_idx + 1} 有 {len(rows)} 行 (body格式)')
            elif 'rows' in table:
                rows = table.get('rows', [])
                print(f'[后端-OCR] [表格解析] 表格{table_idx + 1} 有 {len(rows)} 行 (rows格式)')
            elif 'data' in table:
                rows = table.get('data', [])
                print(f'[后端-OCR] [表格解析] 表格{table_idx + 1} 有 {len(rows)} 行 (data格式)')
            elif 'cells' in table:
                # 可能是扁平的单元格数组
                rows = self._flat_cells_to_rows(table.get('cells', []))
                print(f'[后端-OCR] [表格解析] 表格{table_idx + 1} 有 {len(rows)} 行 (扁平单元格格式)')
            else:
                print(f'[后端-OCR] [表格解析] 表格{table_idx + 1} 无法识别行数据')
                continue
            
            # 先收集所有行的数据
            all_rows_texts = []
            for row_idx, row in enumerate(rows):
                cells = []
                
                # 尝试不同的单元格结构
                if 'cells' in row:
                    cells = row.get('cells', [])
                elif isinstance(row, list):
                    cells = row
                elif 'row' in row:
                    cells = row.get('row', [])
                
                # 获取单元格文本
                cell_texts = self._extract_cell_texts(cells)
                
                if len(cell_texts) > 0:
                    print(f'[后端-OCR] [表格解析] 行 {row_idx + 1}: {cell_texts}')
                    all_rows_texts.append(cell_texts)
            
            # 使用两行配对解析：奇数行作为标签，偶数行作为内容
            print(f'\n[后端-OCR] [表格解析] ===== 开始两行配对解析 =====')
            print(f'[后端-OCR] [表格解析] 总共有 {len(all_rows_texts)} 行数据')
            
            # 收集所有识别到的标签-值对（先不输出，配对完成后再处理）
            label_value_pairs = []
            
            # 按行配对处理（标签行 + 内容行）
            for i in range(0, len(all_rows_texts) - 1, 2):
                label_row = all_rows_texts[i]
                value_row = all_rows_texts[i + 1]
                
                print(f'\n[后端-OCR] [表格解析] 配对 {i//2 + 1}:')
                print(f'[后端-OCR] [表格解析]   标签行: {label_row}')
                print(f'[后端-OCR] [表格解析]   内容行: {value_row}')
                
                # 同一列的标签和内容配对
                min_cols = min(len(label_row), len(value_row))
                for col_idx in range(min_cols):
                    label = label_row[col_idx].strip()
                    value = value_row[col_idx].strip()
                    
                    if label and value:
                        print(f'[后端-OCR] [表格解析]     列{col_idx + 1}: [{label}] = [{value}]')
                        label_value_pairs.append((label, value))
                    elif label:
                        print(f'[后端-OCR] [表格解析]     列{col_idx + 1}: [{label}] = (空值)')
                    elif value:
                        print(f'[后端-OCR] [表格解析]     列{col_idx + 1}: (无标签) = [{value}]')
            
            # 处理奇数行的情况（最后一行没有配对）
            if len(all_rows_texts) % 2 == 1:
                last_row = all_rows_texts[-1]
                print(f'\n[后端-OCR] [表格解析] 最后一行无配对，单独处理: {last_row}')
            
            # 所有行扫描完成后，统一处理标签-值对
            print(f'\n[后端-OCR] [表格解析] ===== 开始处理标签-值对 =====')
            print(f'[后端-OCR] [表格解析] 共收集到 {len(label_value_pairs)} 对标签-值')
            
            for label, value in label_value_pairs:
                self._extract_field_from_label_value(label, value, result)
            
            print(f'[后端-OCR] [表格解析] 标签-值对处理完成')
        
        print(f'\n[后端-OCR] [表格解析] ===== 解析完成 =====')
        print('[后端-OCR] [表格解析] 提取到的工序编号:', result.get('process_number', ''))
        print('[后端-OCR] [表格解析] 提取到的工步数量:', len(result.get('steps', [])))
        print('[后端-OCR] [表格解析] 提取到的DrawingStep数量:', len(result.get('drawing_steps', [])))
        
        return result
    
    def _flat_cells_to_rows(self, flat_cells: list) -> list:
        """将扁平的单元格数组转换为行结构"""
        rows_dict = {}
        for cell in flat_cells:
            row = cell.get('row', 0)
            if row not in rows_dict:
                rows_dict[row] = []
            rows_dict[row].append(cell)
        
        rows = []
        for row_idx in sorted(rows_dict.keys()):
            rows.append({'cells': rows_dict[row_idx]})
        
        return rows
    
    def _extract_cell_texts(self, cells: list) -> list:
        """从单元格列表中提取文本内容"""
        cell_texts = []
        for cell in cells:
            if isinstance(cell, dict):
                if 'word' in cell:
                    cell_texts.append(cell.get('word', ''))
                elif 'words' in cell:
                    cell_texts.append(cell.get('words', ''))
                elif 'text' in cell:
                    cell_texts.append(cell.get('text', ''))
                elif 'word_result' in cell:
                    # 百度表格识别V2可能的字段
                    word_result = cell.get('word_result', {})
                    if 'words' in word_result:
                        cell_texts.append(word_result.get('words', ''))
                    elif 'word' in word_result:
                        cell_texts.append(word_result.get('word', ''))
            elif isinstance(cell, str):
                cell_texts.append(cell)
        return cell_texts
    
    def _extract_field_from_label_value(self, label: str, value: str, result: dict):
        """根据标签和值配对提取字段"""
        # 标准工序卡字段映射 - 增强版本，支持更多标签变体
        field_mappings = {
            'workshop': ['车间'],
            'process_card_number': ['工序号', '工序', '工步号'],
            'process_name': ['工序名称', '工序名', '工步内容', '铣削', '车削', '钻孔', '攻丝'],
            'material_grade': ['材料牌号', '材料号', '材料', '材料名称'],
            'blank_type': ['毛坯种类', '毛坯类型', '铸件'],
            'blank_size': ['毛坯外形尺寸', '毛坯尺寸', '外形尺寸'],
            'blank_available_pieces': ['毛坯还可制件数', '还可制件数', '每毛坯可制件数'],
            'pieces_per_machine': ['每台件数'],
            'equipment': ['设备名称', '设备', '铣床', '车床', '磨床', '加工中心', '钻床'],
            'equipment_model': ['设备型号', '型号', 'Fanuc', 'fanuc', 'SIEMENS', 'Siemens'],
            'equipment_no': ['设备编号', '设备号'],
            'simultaneous_pieces': ['同时加工件数', '同时加工'],
            'fixture_no': ['夹具编号', '夹具号'],
            'fixture': ['夹具名称', '夹具'],
            'cutting_fluid': ['切削液'],
            'station_tool_no': ['工位器具编号', '工位器具号'],
            'station_tool_name': ['工位器具名称', '工位器具'],
            'preparation_time': ['准终工时', '准终'],
            'unit_time': ['单件工时', '单件'],
            'product_name': ['产品名称', '产品'],
            'process_number': ['工序编号', '工序号'],
            'version': ['版本'],
            'control_system': ['数控系统', '系统', 'CNC'],
            'material': ['材料名称', '材料', '碳钢', '不锈钢', '铝合金']
        }
        
        # 数字类型字段列表（设备编号保持字符串，因为可能包含前导零）
        numeric_fields = ['process_card_number', 'blank_available_pieces', 'pieces_per_machine', 
                          'simultaneous_pieces', 'preparation_time', 'unit_time', 
                          'tool_length', 'tool_diameter']
        
        # 尝试匹配字段
        for field, keywords in field_mappings.items():
            for kw in keywords:
                if kw in label and not result.get(field):
                    # 根据字段类型转换数据
                    if field in numeric_fields:
                        try:
                            result[field] = float(value) if '.' in value else int(value)
                        except (ValueError, TypeError):
                            result[field] = value
                    else:
                        result[field] = value
                    print(f'[后端-OCR] [表格解析]     → 提取字段: [{field}] = [{result[field]}] (类型: {type(result[field]).__name__})')
                    return
        
        # 如果没有匹配到已知字段，记录到日志供调试
        print(f'[后端-OCR] [表格解析]     → 未匹配字段: [{label}] = [{value}]')
    
    def _parse_table_data_enhanced(self, table_result: dict) -> dict:
        """增强版表格解析，专门处理工序图右上角的表格格式"""
        print('[后端-OCR] [表格解析] ===== 开始增强版表格解析 =====')
        
        result = {
            'product_name': '',
            'process_name': '',
            'process_number': '',
            'equipment': '',
            'control_system': '',
            'fixture': '',
            'material': '',
            'tool_name': '',
            'tool_length': 0,
            'tool_diameter': 0,
            'steps': [],
            'workshop': '',
            'process_card_number': '',
            'material_grade': '',
            'blank_type': '',
            'blank_size': '',
            'blank_available_pieces': '',
            'pieces_per_machine': '',
            'equipment_model': '',
            'equipment_no': '',
            'simultaneous_pieces': '',
            'fixture_no': '',
            'cutting_fluid': '',
            'station_tool_no': '',
            'station_tool_name': '',
            'preparation_time': '',
            'unit_time': '',
            'drawing_steps': []
        }
        
        tables = []
        if 'result' in table_result:
            result_data = table_result.get('result', {})
            if isinstance(result_data, list):
                tables = result_data
            elif isinstance(result_data, dict) and 'tables' in result_data:
                tables = result_data.get('tables', [])
            elif isinstance(result_data, dict) and 'table' in result_data:
                tables = [result_data.get('table', {})]
        elif 'tables' in table_result:
            tables = table_result.get('tables', [])
        elif 'table' in table_result:
            tables = [table_result.get('table', {})]
        
        if not tables:
            print('[后端-OCR] [表格解析] 未找到表格数据，使用标准解析')
            return self._parse_table_data(table_result)
        
        print(f'[后端-OCR] [表格解析] 发现 {len(tables)} 个表格')
        
        # 收集所有单元格文本
        all_cells = []
        
        for table in tables:
            rows = []
            if 'body' in table:
                rows = table.get('body', [])
            elif 'rows' in table:
                rows = table.get('rows', [])
            elif 'data' in table:
                rows = table.get('data', [])
            
            for row in rows:
                cells = []
                if 'cells' in row:
                    cells = row.get('cells', [])
                elif isinstance(row, list):
                    cells = row
                
                cell_texts = self._extract_cell_texts(cells)
                if cell_texts:
                    all_cells.extend(cell_texts)
        
        print(f'[后端-OCR] [表格解析] 收集到 {len(all_cells)} 个单元格文本')
        print(f'[后端-OCR] [表格解析] 单元格文本列表: {all_cells}')
        
        # 定义字段提取规则（支持多个标签对应一个字段）
        extraction_rules = [
            # (字段名, 标签列表, 是否数字)
            ('workshop', ['车间'], False),
            ('process_card_number', ['工序号', '工序'], True),
            ('process_name', ['工序名称', '铣削', '车削', '钻孔', '攻丝'], False),
            ('material_grade', ['材料牌号', '材料号', '材料'], False),
            ('blank_type', ['毛坯种类', '铸件'], False),
            ('equipment', ['设备名称', '铣床', '车床', '磨床'], False),
            ('equipment_model', ['设备型号', 'Fanuc', 'fanuc', '-0iM'], False),
            ('fixture', ['夹具名称'], False),
            ('cutting_fluid', ['切削液'], False),
        ]
        
        # 智能配对：寻找标签后面的值
        for i, cell_text in enumerate(all_cells):
            cell_text = cell_text.strip()
            
            for field_name, labels, is_numeric in extraction_rules:
                if result.get(field_name):
                    continue  # 字段已填充，跳过
                
                for label in labels:
                    if label in cell_text:
                        # 找到标签，向后查找值
                        value_found = None
                        for j in range(i + 1, min(i + 5, len(all_cells))):
                            candidate = all_cells[j].strip()
                            # 跳过空值和其他标签
                            if candidate and not any(l in candidate for l in ['车间', '工序号', '工序名称', '材料', '毛坯', '设备', '夹具', '切削']):
                                value_found = candidate
                                break
                        
                        if value_found:
                            if is_numeric:
                                try:
                                    result[field_name] = int(value_found) if value_found.isdigit() else float(value_found)
                                except:
                                    result[field_name] = value_found
                            else:
                                result[field_name] = value_found
                            print(f'[后端-OCR] [表格解析] 智能配对: [{label}] → [{field_name}] = [{result[field_name]}]')
                            break
        
        # 特殊处理：如果找到"铣削"等工步内容但没找到工序名称，设置为工序名称
        if not result['process_name']:
            for cell in all_cells:
                if any(kw in cell for kw in ['铣削', '车削', '钻孔', '攻丝', '铰孔', '镗孔']):
                    result['process_name'] = cell.strip()
                    print(f'[后端-OCR] [表格解析] 设置工序名称: {result["process_name"]}')
                    break
        
        # 特殊处理：设备型号中的Fanuc
        if not result['equipment_model']:
            for cell in all_cells:
                if 'Fanuc' in cell or 'fanuc' in cell or '-0iM' in cell:
                    result['equipment_model'] = cell.strip()
                    print(f'[后端-OCR] [表格解析] 设置设备型号: {result["equipment_model"]}')
                    break
        
        # 特殊处理：材料牌号中的数字
        if not result['material_grade']:
            for cell in all_cells:
                if cell.isdigit() and 1 <= int(cell) <= 100:
                    result['material_grade'] = cell
                    print(f'[后端-OCR] [表格解析] 设置材料牌号: {result["material_grade"]}')
                    break
        
        print(f'\n[后端-OCR] [表格解析] ===== 增强版解析完成 =====')
        return result

    def _extract_from_table_row(self, cell_texts: list, result: dict):
        """从单行表格数据中提取字段"""
        if len(cell_texts) == 0:
            return
        
        # 将所有单元格文字合并成一行便于匹配
        combined_text = ' '.join(cell_texts)
        
        # 标准工序卡字段映射（成对提取：第一列1和2是标签，列3和4是值）
        field_mappings = {
            'workshop': ['车间'],
            'process_card_number': ['工序号'],
            'process_name': ['工序名称'],
            'material_grade': ['材料牌号', '材料号'],
            'blank_type': ['毛坯种类'],
            'blank_size': ['毛坯外形尺寸', '毛坯尺寸'],
            'blank_available_pieces': ['毛坯还可制件数', '还可制件数'],
            'pieces_per_machine': ['每台件数'],
            'equipment': ['设备名称'],
            'equipment_model': ['设备型号'],
            'equipment_no': ['设备编号'],
            'simultaneous_pieces': ['同时加工件数'],
            'fixture_no': ['夹具编号'],
            'fixture': ['夹具名称'],
            'cutting_fluid': ['切削液'],
            'station_tool_no': ['工位器具编号'],
            'station_tool_name': ['工位器具名称'],
            'preparation_time': ['准终工时'],
            'unit_time': ['单件工时']
        }
        
        # 成对提取（标准工序卡格式：标签和值成对出现）
        for i in range(0, len(cell_texts) - 1, 2):
            if i + 1 < len(cell_texts):
                label = cell_texts[i].strip()
                value = cell_texts[i + 1].strip()
                if label and value:
                    for field, keywords in field_mappings.items():
                        for kw in keywords:
                            if kw in label and not result.get(field):
                                # 根据字段类型转换数据
                                if field in ['blank_available_pieces', 'pieces_per_machine', 'simultaneous_pieces', 'preparation_time', 'unit_time']:
                                    # 数字类型字段
                                    try:
                                        result[field] = float(value) if '.' in value else int(value)
                                    except (ValueError, TypeError):
                                        result[field] = value
                                else:
                                    result[field] = value
                                print(f'[后端-OCR] [表格解析] 找到{kw}: {value}')
        
        # 单列检查（向后看）
        for i, text in enumerate(cell_texts):
            for field, keywords in field_mappings.items():
                for kw in keywords:
                    if kw in text and i + 1 < len(cell_texts) and not result.get(field):
                        value = cell_texts[i + 1].strip()
                        # 根据字段类型转换数据
                        if field in ['blank_available_pieces', 'pieces_per_machine', 'simultaneous_pieces', 'preparation_time', 'unit_time']:
                            # 数字类型字段
                            try:
                                result[field] = float(value) if '.' in value else int(value)
                            except (ValueError, TypeError):
                                result[field] = value
                        else:
                            result[field] = value
                        print(f'[后端-OCR] [表格解析] 找到{kw}: {value}')
        
        # 检查DrawingStep工步（表格中包含工步相关列）
        if cell_texts and len(cell_texts) >= 2:
            first_cell = cell_texts[0].strip()
            
            # 检查是否是工步序号（数字或包含数字）
            if first_cell.isdigit() or any(c.isdigit() for c in first_cell):
                # 提取序号
                sequence = int(''.join([c for c in first_cell if c.isdigit()]))
                
                # 避免重复添加相同的工步
                existing_sequences = [s.get('sequence') for s in result.get('steps', [])]
                if sequence not in existing_sequences:
                    # 工步内容通常在第二列
                    content = cell_texts[1].strip() if len(cell_texts) > 1 else ''
                    
                    # 工艺装备可能在第三列
                    tooling = cell_texts[2].strip() if len(cell_texts) > 2 else ''
                    
                    # 提取切削参数
                    spindle_speed = None
                    if len(cell_texts) > 3 and cell_texts[3].strip():
                        try:
                            spindle_speed = float(cell_texts[3].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 主轴转速解析失败，值=[{cell_texts[3].strip()}]')
                    
                    cutting_speed = None
                    if len(cell_texts) > 4 and cell_texts[4].strip():
                        try:
                            cutting_speed = float(cell_texts[4].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 切削速度解析失败，值=[{cell_texts[4].strip()}]')
                    
                    feed_rate = None
                    if len(cell_texts) > 5 and cell_texts[5].strip():
                        try:
                            feed_rate = float(cell_texts[5].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 进给量解析失败，值=[{cell_texts[5].strip()}]')
                    
                    depth_of_cut = None
                    if len(cell_texts) > 6 and cell_texts[6].strip():
                        try:
                            depth_of_cut = float(cell_texts[6].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 被吃刀量解析失败，值=[{cell_texts[6].strip()}]')
                    
                    feed_count = None
                    if len(cell_texts) > 7 and cell_texts[7].strip():
                        try:
                            feed_count = int(cell_texts[7].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 进给次数解析失败，值=[{cell_texts[7].strip()}]')
                    
                    machine_time = None
                    if len(cell_texts) > 8 and cell_texts[8].strip():
                        try:
                            machine_time = float(cell_texts[8].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 机动工时解析失败，值=[{cell_texts[8].strip()}]')
                    
                    auxiliary_time = None
                    if len(cell_texts) > 9 and cell_texts[9].strip():
                        try:
                            auxiliary_time = float(cell_texts[9].strip())
                        except (ValueError, TypeError):
                            print(f'[后端-OCR] [表格解析] 工步{sequence}: 辅助工时解析失败，值=[{cell_texts[9].strip()}]')
                    
                    # 添加到steps（兼容旧格式）
                    result['steps'].append({
                        'sequence': sequence,
                        'content': content,
                        'parameters': '',
                        'equipment': tooling,
                        'remark': '',
                        'drawing_ref': ''
                    })
                    print(f'[后端-OCR] [表格解析] 添加工步 {sequence}: {content}')
                    
                    # 添加DrawingStep数据（新格式）
                    drawing_step = {
                        'step': sequence,
                        'step_content': content,
                        'tooling': tooling,
                        'spindle_speed': spindle_speed,
                        'cutting_speed': cutting_speed,
                        'feed_rate': feed_rate,
                        'depth_of_cut': depth_of_cut,
                        'feed_count': feed_count,
                        'machine_time': machine_time,
                        'auxiliary_time': auxiliary_time
                    }
                    
                    existing_drawing_steps = [s.get('step') for s in result.get('drawing_steps', [])]
                    if drawing_step['step'] not in existing_drawing_steps:
                        result['drawing_steps'].append(drawing_step)
                        print(f'[后端-OCR] [表格解析] 添加DrawingStep {drawing_step["step"]}: {drawing_step["step_content"]}')
        
        # 检查是否是工步标题行
        if any('工步' in text for text in cell_texts):
            print('[后端-OCR] [表格解析] 找到工步标题行')

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
            'workshop': '',
            'process_card_number': '',
            'material_grade': '',
            'blank_type': '',
            'blank_size': '',
            'blank_available_pieces': '',
            'pieces_per_machine': '',
            'equipment_model': '',
            'equipment_no': '',
            'simultaneous_pieces': '',
            'fixture_no': '',
            'cutting_fluid': '',
            'station_tool_no': '',
            'station_tool_name': '',
            'preparation_time': '',
            'unit_time': '',
            'drawing_steps': [],
            'raw_text': '',
            'error': '百度OCR服务不可用，请先配置百度API密钥'
        }

def ocr_recognize(image_data: str) -> dict:
    print('[后端-OCR] [入口] 调用 ocr_recognize 函数')
    processor = OCRProcessor()
    return processor.recognize(image_data)