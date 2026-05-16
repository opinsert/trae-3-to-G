import json
import aiohttp
from app.models.schemas import ProcessCard, ToolInfo, Operation
from app.utils.config import settings

REQUIRED_FIELDS = [
    'product_name', 'process_name', 'process_number', 'version',
    'equipment', 'control_system', 'fixture', 'material',
    'tool_name', 'tool_length', 'tool_diameter'
]

class ParameterExtractor:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_url = settings.deepseek_api_url
    
    async def extract(self, text: str) -> dict:
        if not self.api_key:
            return self._fallback_extract(text)
        
        try:
            return await self._extract_with_deepseek(text)
        except Exception as e:
            print(f"DeepSeek API调用失败，使用本地解析: {e}")
            return self._fallback_extract(text)
    
    async def _extract_with_deepseek(self, text: str) -> dict:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        prompt = f"""
你是一个专业的机加工编程师，请从以下文本中提取工序卡信息：

文本内容：
{text}

请按照以下JSON格式输出，确保所有字段都被提取：
{{
  "product_name": "产品名称",
  "process_name": "工序名称",
  "process_number": "工序编号",
  "version": "版本号",
  "equipment": "设备名称",
  "control_system": "数控系统",
  "fixture": "夹具名称",
  "material": "材料名称",
  "tool_name": "刀具名称",
  "tool_length": 刀具长度（数字）,
  "tool_diameter": 刀具直径（数字）,
  "operations": [
    {{
      "sequence": 序号,
      "content": "操作内容",
      "parameters": "工艺参数/要求",
      "equipment": "设备/工具",
      "remark": "备注"
    }}
  ]
}}

如果某个字段无法从文本中提取到，请保持为空字符串或0。
"""
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的数据提取助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(self.api_url, headers=headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()
        
        content = result['choices'][0]['message']['content']
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._fallback_extract(text)
    
    def _fallback_extract(self, text: str) -> dict:
        import re
        result = {field: '' for field in REQUIRED_FIELDS}
        result['operations'] = []
        
        field_patterns = {
            'product_name': [r'产品名称[：:]\s*([^|，。\n]+)', r'\*\*产品名称\*\*[^\|]*\|([^\|]+)'],
            'process_name': [r'工序名称[：:]\s*([^|，。\n]+)', r'\*\*工序名称\*\*[^\|]*\|([^\|]+)'],
            'process_number': [r'工序编号[：:]\s*([^|，。\n]+)', r'\*\*工序编号\*\*[^\|]*\|([^\|]+)'],
            'version': [r'版本号[：:]\s*([^|，。\n]+)', r'\*\*版本号\*\*[^\|]*\|([^\|]+)', r'[-]\s*版本号[：:]\s*([^|，。\n]+)'],
            'equipment': [r'设备名称[：:]\s*([^|，。\n]+)', r'\*\*设备名称\*\*[^\|]*\|([^\|]+)'],
            'control_system': [r'数控系统[：:]\s*([^|，。\n]+)', r'\*\*数控系统\*\*[^\|]*\|([^\|]+)'],
            'fixture': [r'夹具名称[：:]\s*([^|，。\n]+)', r'\*\*夹具名称\*\*[^\|]*\|([^\|]+)', r'[-]\s*夹具名称[：:]\s*([^|，。\n]+)'],
            'material': [r'材料名称[：:]\s*([^|，。\n]+)', r'\*\*材料名称\*\*[^\|]*\|([^\|]+)'],
            'tool_name': [r'刀具名称[：:]\s*([^|，。\n]+)', r'名称[：:]\s*([^|<br>]+)', r'\*\*刀具\*\*[^\|]*\|([^\|]+)'],
            'tool_length': [r'长度[：:]\s*([^|，。\nmm]+)', r'\*\*长度\*\*[^\|]*\|([^\|]+)'],
            'tool_diameter': [r'直径[：:]\s*([^|，。\nmm]+)', r'\*\*直径\*\*[^\|]*\|([^\|]+)']
        }
        
        for field, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match and match.group(1):
                    value = match.group(1).strip()
                    if value and (not result[field] or len(value) > len(result[field])):
                        result[field] = value
        
        result['operations'] = self._extract_operations(text)
        
        try:
            result['tool_length'] = float(result['tool_length']) if result['tool_length'] else 0
            result['tool_diameter'] = float(result['tool_diameter']) if result['tool_diameter'] else 0
        except ValueError:
            result['tool_length'] = 0
            result['tool_diameter'] = 0
        
        return result
    
    def _extract_value(self, text: str, start_idx: int) -> str:
        end_chars = ['：', ':', '，', ',', '。', '.', '\n', ' ', '、']
        value = ''
        i = start_idx
        
        while i < len(text):
            if text[i] in end_chars:
                break
            value += text[i]
            i += 1
        
        return value.strip()
    
    def _extract_operations(self, text: str) -> list:
        operations = []
        lines = text.split('\n')
        
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.',
                                       '1、', '2、', '3、', '4、', '5、', '6、', '7、', '8、', '9、', '10、')):
                parts = line.split('、') if '、' in line else line.split('.')
                if len(parts) >= 2:
                    try:
                        seq = int(parts[0].strip())
                        content = parts[1].strip()
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
    
    def validate_parameters(self, params: dict) -> tuple:
        missing = []
        for field in REQUIRED_FIELDS:
            value = params.get(field, '')
            if not value:
                missing.append(field)
        
        return len(missing) == 0, missing
    
    def to_process_card(self, params: dict) -> ProcessCard:
        return ProcessCard(
            product_name=params.get('product_name', ''),
            process_name=params.get('process_name', ''),
            process_number=params.get('process_number', ''),
            version=params.get('version', ''),
            equipment=params.get('equipment', ''),
            control_system=params.get('control_system', ''),
            fixture=params.get('fixture', ''),
            material=params.get('material', ''),
            tool_info=ToolInfo(
                name=params.get('tool_name', ''),
                length=params.get('tool_length', 0),
                diameter=params.get('tool_diameter', 0)
            )
        )
    
    def to_operations(self, ops_data: list) -> list:
        operations = []
        for idx, op in enumerate(ops_data, 1):
            operations.append(Operation(
                sequence=op.get('sequence', idx),
                content=op.get('content', ''),
                parameters=op.get('parameters', ''),
                equipment=op.get('equipment', ''),
                remark=op.get('remark', '')
            ))
        return operations

async def extract_parameters(text: str) -> dict:
    extractor = ParameterExtractor()
    return await extractor.extract(text)

def validate_and_convert(params: dict) -> tuple:
    extractor = ParameterExtractor()
    valid, missing = extractor.validate_parameters(params)
    if not valid:
        return None, missing
    
    process_card = extractor.to_process_card(params)
    operations = extractor.to_operations(params.get('operations', []))
    return (process_card, operations), None
