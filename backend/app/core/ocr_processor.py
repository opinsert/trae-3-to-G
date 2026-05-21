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
            table_has_data = any([
                table_parsed.get('process_number'),
                table_parsed.get('material'),
                table_parsed.get('equipment'),
                table_parsed.get('control_system'),
                len(table_parsed.get('steps', [])) > 0
            ])
            
            if table_has_data:
                print('[后端-OCR] [百度OCR] 表格识别有数据，使用表格结果')
                # 只更新表格有的字段
                for key in ['process_number', 'material', 'equipment', 'control_system', 'steps']:
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
            'steps': []
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
        
        # 关键词匹配
        process_keywords = ['车间', '工序号', '工序名称', '材料号', '材料名称', '毛坯种类']
        equipment_keywords = ['设备名称', '设备型号', '数控系统']
        fixture_keywords = ['夹具名称', '夹具编号']
        material_keywords = ['铸件', '钢', '铁', '铝', '合金']
        
        # 检查工序相关字段
        for i, text in enumerate(cell_texts):
            # 工序号
            if '工序号' in text and i + 1 < len(cell_texts):
                result['process_number'] = cell_texts[i + 1].strip()
                print(f'[后端-OCR] [表格解析] 找到工序号: {result["process_number"]}')
            
            # 材料号
            if '材料号' in text and i + 1 < len(cell_texts):
                result['material'] = cell_texts[i + 1].strip()
                print(f'[后端-OCR] [表格解析] 找到材料号: {result["material"]}')
            
            # 设备名称
            if '设备名称' in text and i + 1 < len(cell_texts):
                result['equipment'] = cell_texts[i + 1].strip()
                print(f'[后端-OCR] [表格解析] 找到设备名称: {result["equipment"]}')
            
            # 设备型号
            if '设备型号' in text and i + 1 < len(cell_texts):
                result['control_system'] = cell_texts[i + 1].strip()
                print(f'[后端-OCR] [表格解析] 找到设备型号: {result["control_system"]}')
        
        # 检查工步（表格中第一个单元格是数字的行）
        if cell_texts and len(cell_texts) >= 2:
            first_cell = cell_texts[0].strip()
            
            # 检查是否是工步序号（数字或包含数字）
            if first_cell.isdigit() or any(c.isdigit() for c in first_cell):
                # 提取序号
                sequence = int(''.join([c for c in first_cell if c.isdigit()]))
                
                # 工步内容通常在第二列
                content = cell_texts[1].strip() if len(cell_texts) > 1 else ''
                
                # 工艺装备可能在第三列
                equipment = cell_texts[2].strip() if len(cell_texts) > 2 else ''
                
                # 避免重复添加相同的工步
                existing_sequences = [s.get('sequence') for s in result.get('steps', [])]
                if sequence not in existing_sequences:
                    result['steps'].append({
                        'sequence': sequence,
                        'content': content,
                        'parameters': '',
                        'equipment': equipment,
                        'remark': '',
                        'drawing_ref': ''
                    })
                    print(f'[后端-OCR] [表格解析] 添加工步 {sequence}: {content}')
        
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
            'raw_text': '',
            'error': '百度OCR服务不可用，请先配置百度API密钥'
        }

def ocr_recognize(image_data: str) -> dict:
    print('[后端-OCR] [入口] 调用 ocr_recognize 函数')
    processor = OCRProcessor()
    return processor.recognize(image_data)