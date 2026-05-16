import base64
import io
import os
import subprocess
import re
from PIL import Image
import cv2
import numpy as np

class OCRProcessor:
    def __init__(self, lang='chi_sim+eng'):
        self.lang = lang
        self.tesseract_path = r'C:\Users\21242\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        print('[后端-OCR] ============== Tesseract 检查开始 ==============')
        print(f'[后端-OCR] 期望路径: {self.tesseract_path}')
        
        if not os.path.exists(self.tesseract_path):
            print(f'[后端-OCR] ✗ Tesseract 未安装在预期位置')
            try:
                result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.tesseract_path = result.stdout.strip().split('\n')[0]
                    print(f'[后端-OCR] ✓ 通过 where 命令找到: {self.tesseract_path}')
                    print('[后端-OCR] ============== Tesseract 检查完成 ==============\n')
                    return True
            except Exception as e:
                print(f'[后端-OCR] ✗ 通过 where 命令查找失败: {str(e)}')
                print('[后端-OCR] ============== Tesseract 检查失败 ==============\n')
                return False
        else:
            print(f'[后端-OCR] ✓ Tesseract 存在于预期位置')
            print('[后端-OCR] ============== Tesseract 检查完成 ==============\n')
            return True

    def recognize(self, image_data: str) -> dict:
        print('[后端-OCR] ============== OCR 识别开始 ==============')
        print(f'[后端-OCR] 输入数据长度: {len(image_data)} 字符')
        print(f'[后端-OCR] 输入数据前缀: {image_data[:80]}...')
        
        if not self.tesseract_available:
            print('[后端-OCR] ✗ Tesseract 不可用，使用备用方案')
            result = self._fallback_recognize(image_data)
            print('[后端-OCR] ============== OCR 识别完成(备用) ==============\n')
            return result
        
        try:
            print('[后端-OCR] 步骤1: 解码图片数据')
            temp_path = self._decode_and_preprocess_image(image_data)
            print(f'[后端-OCR] ✓ 图片已保存到: {temp_path}')
            
            print('[后端-OCR] 步骤2: 运行 Tesseract OCR')
            text = self._run_tesseract(temp_path)
            print(f'[后端-OCR] ✓ OCR 识别完成，识别文字长度: {len(text)} 字符')
            
            print('[后端-OCR] 步骤3: 清理临时文件')
            try:
                os.remove(temp_path)
                print('[后端-OCR] ✓ 临时文件已删除')
            except Exception as e:
                print(f'[后端-OCR] ⚠ 删除临时文件失败: {str(e)}')
            
            print('[后端-OCR] 步骤4: 解析识别结果')
            result = self._parse_text(text)
            print('[后端-OCR] ✓ 结果解析完成')
            
            print('[后端-OCR] 识别结果摘要:')
            print(f"  ├─ 产品名称: {result['product_name'] or '(空)'}")
            print(f"  ├─ 工序名称: {result['process_name'] or '(空)'}")
            print(f"  ├─ 设备名称: {result['equipment'] or '(空)'}")
            print(f"  ├─ 刀具直径: {result['tool_diameter'] or '(空)'}")
            print(f"  ├─ 操作步骤数量: {len(result['operations'])}")
            if result['raw_text']:
                print(f"  └─ 原始文本预览: {result['raw_text'][:100]}...")
            else:
                print(f"  └─ 原始文本: (空)")
            
            print('[后端-OCR] ============== OCR 识别成功 ==============\n')
            return result
            
        except Exception as e:
            print(f'[后端-OCR] ✗ OCR 识别过程出错: {str(e)}')
            import traceback
            print(f'[后端-OCR] 错误堆栈:\n{traceback.format_exc()}')
            result = self._fallback_recognize(image_data)
            print('[后端-OCR] ============== OCR 识别失败(备用) ==============\n')
            return result

    def _decode_and_preprocess_image(self, image_data: str) -> str:
        print('[后端-OCR] [解码] 开始解码图片')
        
        if image_data.startswith('data:image/'):
            print(f"[后端-OCR] [解码] 检测到 data URL，提取 base64 数据")
            image_data = image_data.split(',')[1]
        
        print(f"[后端-OCR] [解码] Base64 数据长度: {len(image_data)} 字符")
        
        try:
            image_bytes = base64.b64decode(image_data)
            print(f"[后端-OCR] [解码] 解码后字节数: {len(image_bytes)}")
        except Exception as e:
            print(f"[后端-OCR] [解码] ✗ Base64 解码失败: {str(e)}")
            raise
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            print(f"[后端-OCR] [解码] 图片格式: {image.format}")
            print(f"[后端-OCR] [解码] 图片尺寸: {image.width}x{image.height}")
        except Exception as e:
            print(f"[后端-OCR] [解码] ✗ 图片打开失败: {str(e)}")
            raise
        
        img_array = np.array(image)
        print(f"[后端-OCR] [解码] 图像数组形状: {img_array.shape}")
        
        if len(img_array.shape) == 3:
            print(f"[后端-OCR] [预处理] 转换为灰度图")
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            print(f"[后端-OCR] [预处理] 图片已是灰度图")
            gray = img_array
        
        print(f"[后端-OCR] [预处理] 颜色反转")
        gray = cv2.bitwise_not(gray)
        
        print(f"[后端-OCR] [预处理] OTSU二值化")
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        print(f"[后端-OCR] [预处理] 再次颜色反转")
        binary = cv2.bitwise_not(binary)
        
        print(f"[后端-OCR] [预处理] 形态学操作")
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        temp_dir = 'temp_ocr'
        if not os.path.exists(temp_dir):
            print(f"[后端-OCR] [解码] 创建临时目录: {temp_dir}")
            os.makedirs(temp_dir)
        
        temp_path = os.path.join(temp_dir, 'ocr_image.png')
        
        print(f"[后端-OCR] [解码] 保存处理后的图片到: {temp_path}")
        cv2.imwrite(temp_path, binary)
        
        file_size = os.path.getsize(temp_path)
        print(f"[后端-OCR] [解码] ✓ 图片保存成功，文件大小: {file_size} bytes")
        
        return temp_path

    def _run_tesseract(self, image_path: str) -> str:
        print(f"[后端-OCR] [Tesseract] 开始识别图片: {image_path}")
        print(f"[后端-OCR] [Tesseract] Tesseract 路径: {self.tesseract_path}")
        print(f"[后端-OCR] [Tesseract] 使用语言: {self.lang}")
        
        try:
            print(f"[后端-OCR] [Tesseract] 执行命令...")
            result = subprocess.run(
                [self.tesseract_path, image_path, 'stdout', '-l', self.lang],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )
            
            print(f"[后端-OCR] [Tesseract] 命令执行完成")
            print(f"[后端-OCR] [Tesseract] 返回码: {result.returncode}")
            
            if result.returncode != 0:
                print(f"[后端-OCR] [Tesseract] ✗ 命令执行失败")
                print(f"[后端-OCR] [Tesseract] 错误输出: {result.stderr}")
                return ''
            
            text = result.stdout
            print(f"[后端-OCR] [Tesseract] ✓ 识别成功")
            print(f"[后端-OCR] [Tesseract] 识别行数: {len(text.split(chr(10)))}")
            print(f"[后端-OCR] [Tesseract] 前100字符:\n{text[:100]}")
            
            return text
            
        except subprocess.TimeoutExpired:
            print(f"[后端-OCR] [Tesseract] ✗ 命令执行超时(60秒)")
            return ''
        except Exception as e:
            print(f"[后端-OCR] [Tesseract] ✗ 执行异常: {str(e)}")
            import traceback
            print(f"[后端-OCR] [Tesseract] 错误堆栈:\n{traceback.format_exc()}")
            return ''

    def _parse_text(self, text: str) -> dict:
        print('[后端-OCR] [解析] 开始解析识别文本')
        print(f'[后端-OCR] [解析] 文本总长度: {len(text)} 字符')
        
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
            'raw_text': text
        }
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        print(f'[后端-OCR] [解析] 有效行数: {len(lines)}')
        
        if lines:
            print(f'[后端-OCR] [解析] 前5行:')
            for i, line in enumerate(lines[:5]):
                print(f'  {i+1}: {line}')
        
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
            'tool_diameter': ['直径', '刀径', '直径']
        }
        
        print('[后端-OCR] [解析] 搜索关键词...')
        
        for field, keys in keywords.items():
            found = False
            for key in keys:
                for line in lines:
                    if key in line:
                        value = self._extract_value_from_line(line, key)
                        if value and (not extracted[field] or len(value) > len(str(extracted[field]))):
                            print(f'  → 找到 {field}: "{value}" (关键词: {key})')
                            extracted[field] = value
                            found = True
                            break
                if found:
                    break
        
        print('[后端-OCR] [解析] 提取数值参数...')
        try:
            numbers = re.findall(r'\d+\.?\d*', str(extracted['tool_length']))
            if numbers:
                extracted['tool_length'] = float(numbers[0])
                print(f'  → 刀具长度: {extracted["tool_length"]}')
        except:
            extracted['tool_length'] = 0
            print(f'  → 刀具长度解析失败，设为0')

        try:
            numbers = re.findall(r'\d+\.?\d*', str(extracted['tool_diameter']))
            if numbers:
                extracted['tool_diameter'] = float(numbers[0])
                print(f'  → 刀具直径: {extracted["tool_diameter"]}')
        except:
            extracted['tool_diameter'] = 0
            print(f'  → 刀具直径解析失败，设为0')

        print('[后端-OCR] [解析] 提取操作步骤...')
        extracted['operations'] = self._extract_operations(lines)
        print(f'  → 找到 {len(extracted["operations"])} 个操作步骤')
        
        if extracted['operations']:
            print('  操作步骤列表:')
            for op in extracted['operations']:
                print(f'    - 序号{op["sequence"]}: {op["content"]}')
        
        print('[后端-OCR] [解析] ✓ 解析完成')
        return extracted

    def _extract_value_from_line(self, line: str, key: str) -> str:
        end_chars = ['：', ':', '，', ',', '。', '.', '\n', ' ', '、', '=', '\r']
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
        
        print('[后端-OCR] [步骤提取] 开始提取操作步骤')
        
        patterns = [
            r'^\d+[.、]',
            r'^工步\d+',
            r'^步骤\d+',
            r'^操作\d+'
        ]
        
        match_count = 0
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            matched_pattern = None
            for pattern in patterns:
                if re.match(pattern, line_stripped):
                    matched_pattern = pattern
                    break
            
            if matched_pattern:
                match_count += 1
                numbers = re.findall(r'\d+', line_stripped)
                if numbers:
                    seq = int(numbers[0])
                    content = re.sub(r'^\d+[.、]\s*', '', line_stripped)
                    content = re.sub(r'^(工步|步骤|操作)\d+', '', content).strip()
                    
                    if content:
                        op = {
                            'sequence': seq,
                            'content': content,
                            'parameters': '',
                            'equipment': '',
                            'remark': ''
                        }
                        operations.append(op)
                        print(f'    [步骤{seq}]: "{content}"')
        
        print(f'[后端-OCR] [步骤提取] 共匹配 {match_count} 行，找到 {len(operations)} 个有效步骤')
        return operations

    def _fallback_recognize(self, image_data: str) -> dict:
        print('[后端-OCR] [备用] 使用备用识别方案')
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
    print('[后端-OCR] [入口] 调用 ocr_recognize 函数')
    processor = OCRProcessor()
    return processor.recognize(image_data)