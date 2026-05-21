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
            
            # 先调用表格识别
            print('[后端-OCR] [百度OCR] 开始表格识别...')
            table_result = self.baidu_client.tableRecognition(image_bytes)
            print('[后端-OCR] [百度OCR] 表格识别API调用成功')
            
            # 再调用通用文字识别
            print('[后端-OCR] [百度OCR] 开始通用文字识别...')
            general_result = self.baidu_client.basicGeneral(image_bytes)
            print('[后端-OCR] [百度OCR] 通用文字识别API调用成功')
            
            # 解析通用识别结果
            text = ''
            all_words = []
            if 'words_result' in general_result:
                text_lines = []
                for i, word_info in enumerate(general_result['words_result']):
                    if 'words' in word_info:
                        word = word_info['words']
                        text_lines.append(word)
                        all_words.append(word)
                        if i < 10:
                            print('[后端-OCR] [百度OCR] 文字块', i+1, ':', word)
                text = '\n'.join(text_lines)
            
            print('[后端-OCR] [百度OCR] 通用识别完成，文字长度:', len(text))
            
            # 解析表格识别结果
            print('[后端-OCR] [百度OCR] 开始解析表格数据...')
            table_parsed = self._parse_table_data(table_result)
            
            # 解析通用识别结果
            text_parsed = self._parse_text(all_words)
            
            # 合并结果：优先使用表格识别结果，表格没有的用通用识别补充
            parsed_result = text_parsed.copy()
            
            # 只有当表格解析有实际数据时才覆盖
            new_fields = ['workshop', 'process_card_number', 'material_grade', 'blank_type', 
                         'blank_size', 'blank_available_pieces', 'pieces_per_machine', 
                         'equipment_model', 'equipment_no', 'simultaneous_pieces', 
                         'fixture_no', 'cutting_fluid', 'station_tool_no', 
                         'station_tool_name', 'preparation_time', 'unit_time', 'drawing_steps']
            
            table_has_data = any([
                table_parsed.get('process_number'),
                table_parsed.get('material'),
                table_parsed.get('equipment'),
                table_parsed.get('control_system'),
                len(table_parsed.get('steps', [])) > 0
            ] + [table_parsed.get(field) for field in new_fields])
            
            if table_has_data:
                print('[后端-OCR] [百度OCR] 表格识别有数据，使用表格结果')
                # 只更新表格有的字段
                for key in ['process_number', 'material', 'equipment', 'control_system', 'steps'] + new_fields:
                    if table_parsed.get(key):
                        parsed_result[key] = table_parsed[key]
            else:
                print('[后端-OCR] [百度OCR] 表格识别无数据，使用通用识别结果')
            
            parsed_result['raw_text'] = text
            parsed_result['table_data'] = table_result
            parsed_result['table_error'] = '表格识别权限不足' if table_result.get('error_code') else None
            
            print('[后端-OCR] [百度OCR] 最终识别结果:')
            print('[后端-OCR]  - 产品名称:', parsed_result.get('product_name', ''))
            print('[后端-OCR]  - 工序名称:', parsed_result.get('process_name', ''))
            print('[后端-OCR]  - 设备名称:', parsed_result.get('equipment', ''))
            print('[后端-OCR]  - 数控系统:', parsed_result.get('control_system', ''))
            print('[后端-OCR]  - 材料名称:', parsed_result.get('material', ''))
            print('[后端-OCR]  - 工序编号:', parsed_result.get('process_number', ''))
            print('[后端-OCR]  - 工步数量:', len(parsed_result.get('steps', [])))
            print('[后端-OCR]  - DrawingStep数量:', len(parsed_result.get('drawing_steps', [])))
            # 打印部分新字段
            if parsed_result.get('workshop'):
                print('[后端-OCR]  - 车间:', parsed_result.get('workshop'))
            if parsed_result.get('material_grade'):
                print('[后端-OCR]  - 材料牌号:', parsed_result.get('material_grade'))
            if parsed_result.get('equipment_model'):
                print('[后端-OCR]  - 设备型号:', parsed_result.get('equipment_model'))
            
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
            'material_grade': ['材料牌号', '材料号'],
            'blank_type': ['毛坯种类'],
            'blank_size': ['毛坯外形尺寸', '毛坯尺寸'],
            'blank_available_pieces': ['毛坯还可制件数', '还可制件数'],
            'pieces_per_machine': ['每台件数'],
            'equipment_model': ['设备型号'],
            'equipment_no': ['设备编号'],
            'simultaneous_pieces': ['同时加工件数'],
            'fixture_no': ['夹具编号'],
            'cutting_fluid': ['切削液'],
            'station_tool_no': ['工位器具编号'],
            'station_tool_name': ['工位器具名称'],
            'preparation_time': ['准终工时'],
            'unit_time': ['单件工时']
        }
        
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
        
        for i, word in enumerate(all_words):
            for field, keywords in new_field_patterns.items():
                for kw in keywords:
                    if kw in word and not extracted[field]:
                        if i + 1 < len(all_words):
                            value = all_words[i + 1].strip()
                            extracted[field] = value
                            print(f'[后端-OCR] [解析] 字段[{field}] = [{value}]')
        
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

    def _parse_table_data(self, table_result: dict) -> dict:
        """解析表格识别结果"""
        print('[后端-OCR] [表格解析] 开始解析表格数据')
        
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
        print('[后端-OCR] [表格解析] 表格识别原始结果:', str(table_result)[:500])
        
        # 尝试不同的表格数据结构
        tables = []
        
        # 常见的表格识别结果结构
        if 'result' in table_result:
            tables = table_result.get('result', [])
            print('[后端-OCR] [表格解析] 使用result路径，表格数量:', len(tables))
        elif 'tables' in table_result:
            tables = table_result.get('tables', [])
            print('[后端-OCR] [表格解析] 使用tables路径，表格数量:', len(tables))
        elif 'table_result' in table_result:
            tables = [table_result.get('table_result', {})]
            print('[后端-OCR] [表格解析] 使用table_result路径')
        else:
            print('[后端-OCR] [表格解析] 无法识别表格数据结构')
            return result
        
        # 遍历所有表格
        for table_idx, table in enumerate(tables):
            print(f'[后端-OCR] [表格解析] 处理表格 {table_idx + 1}')
            
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
            
            # 遍历表格行
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
                cell_texts = []
                for cell in cells:
                    if isinstance(cell, dict):
                        if 'word' in cell:
                            cell_texts.append(cell.get('word', ''))
                        elif 'words' in cell:
                            cell_texts.append(cell.get('words', ''))
                        elif 'text' in cell:
                            cell_texts.append(cell.get('text', ''))
                    elif isinstance(cell, str):
                        cell_texts.append(cell)
                
                if len(cell_texts) > 0:
                    print(f'[后端-OCR] [表格解析] 行 {row_idx + 1}: {cell_texts}')
                    
                    # 尝试从表格中提取字段
                    self._extract_from_table_row(cell_texts, result)
        
        print('[后端-OCR] [表格解析] 解析完成')
        print('[后端-OCR] [表格解析] 提取到的工序编号:', result.get('process_number', ''))
        print('[后端-OCR] [表格解析] 提取到的工步数量:', len(result.get('steps', [])))
        
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
                                result[field] = value
                                print(f'[后端-OCR] [表格解析] 找到{kw}: {value}')
        
        # 单列检查（向后看）
        for i, text in enumerate(cell_texts):
            for field, keywords in field_mappings.items():
                for kw in keywords:
                    if kw in text and i + 1 < len(cell_texts) and not result.get(field):
                        value = cell_texts[i + 1].strip()
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
                        except:
                            pass
                    
                    cutting_speed = None
                    if len(cell_texts) > 4 and cell_texts[4].strip():
                        try:
                            cutting_speed = float(cell_texts[4].strip())
                        except:
                            pass
                    
                    feed_rate = None
                    if len(cell_texts) > 5 and cell_texts[5].strip():
                        try:
                            feed_rate = float(cell_texts[5].strip())
                        except:
                            pass
                    
                    depth_of_cut = None
                    if len(cell_texts) > 6 and cell_texts[6].strip():
                        try:
                            depth_of_cut = float(cell_texts[6].strip())
                        except:
                            pass
                    
                    feed_count = None
                    if len(cell_texts) > 7 and cell_texts[7].strip():
                        try:
                            feed_count = int(cell_texts[7].strip())
                        except:
                            pass
                    
                    machine_time = None
                    if len(cell_texts) > 8 and cell_texts[8].strip():
                        try:
                            machine_time = float(cell_texts[8].strip())
                        except:
                            pass
                    
                    auxiliary_time = None
                    if len(cell_texts) > 9 and cell_texts[9].strip():
                        try:
                            auxiliary_time = float(cell_texts[9].strip())
                        except:
                            pass
                    
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