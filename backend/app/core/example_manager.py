from app.models.schemas import ExampleItem, ProcessCard, ToolInfo, Operation

EXAMPLES = [
    {
        "id": 1,
        "name": "平面铣削加工",
        "description": "标准平面铣削加工工序卡示例，适用于铝合金材料的平面加工",
        "category": "铣削",
        "card_data": {
            "product_name": "铝合金外壳",
            "process_name": "平面铣削",
            "process_number": "OP001",
            "version": "V1.0",
            "equipment": "CNC加工中心",
            "control_system": "FANUC 0i-MF",
            "fixture": "真空吸盘",
            "material": "6061铝合金",
            "tool_info": {
                "name": "立铣刀",
                "length": 75,
                "diameter": 10
            }
        },
        "operations_data": [
            {
                "sequence": 1,
                "content": "快速定位到安全高度",
                "parameters": "X=0, Y=0, Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            },
            {
                "sequence": 2,
                "content": "铣削平面",
                "parameters": "X=100, Y=100, Z=-2, F=150",
                "equipment": "立铣刀D10",
                "remark": "进给速度150mm/min"
            },
            {
                "sequence": 3,
                "content": "抬刀返回",
                "parameters": "Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            }
        ],
        "gcode": "; 产品名称: 铝合金外壳\n; 工序名称: 平面铣削\n; 工序编号: OP001\n; 版本号: V1.0\n; 设备: CNC加工中心\n; 数控系统: FANUC 0i-MF\n; 夹具: 真空吸盘\n; 材料: 6061铝合金\n; 刀具: 立铣刀 (直径:10.000mm, 长度:75.000mm)\n\nG90 G54 G17 G40 G49 G80 G21\nM03 S3000\nG00 Z50.0\n\n; 步骤1: 快速定位到安全高度\n; 参数: X=0, Y=0, Z=50\nG00 X0.000 Y0.000 Z50.000\n\n; 步骤2: 铣削平面\n; 参数: X=100, Y=100, Z=-2, F=150\nG00 X100.000 Y100.000\nG01 Z-2.000 F150\nG00 Z50.0\n\n; 步骤3: 抬刀返回\n; 参数: Z=50\nG00 X0.000 Y0.000 Z50.000\n\nG00 Z100.0\nM05\nM30"
    },
    {
        "id": 2,
        "name": "钻孔加工",
        "description": "标准钻孔加工工序卡示例，适用于钢材钻孔加工",
        "category": "钻孔",
        "card_data": {
            "product_name": "钢制支架",
            "process_name": "钻孔加工",
            "process_number": "OP002",
            "version": "V1.0",
            "equipment": "CNC加工中心",
            "control_system": "SIEMENS 828D",
            "fixture": "虎钳",
            "material": "45号钢",
            "tool_info": {
                "name": "钻头",
                "length": 100,
                "diameter": 8
            }
        },
        "operations_data": [
            {
                "sequence": 1,
                "content": "定位到孔位",
                "parameters": "X=50, Y=50, Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            },
            {
                "sequence": 2,
                "content": "钻孔",
                "parameters": "X=50, Y=50, Z=-20, F=80",
                "equipment": "钻头D8",
                "remark": "通孔加工"
            },
            {
                "sequence": 3,
                "content": "退刀",
                "parameters": "Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            }
        ],
        "gcode": "; 产品名称: 钢制支架\n; 工序名称: 钻孔加工\n; 工序编号: OP002\n; 版本号: V1.0\n; 设备: CNC加工中心\n; 数控系统: SIEMENS 828D\n; 夹具: 虎钳\n; 材料: 45号钢\n; 刀具: 钻头 (直径:8.000mm, 长度:100.000mm)\n\nG90 G54 G17 G40 G49 G80 G21\nM03 S2000\nG00 Z50.0\n\n; 步骤1: 定位到孔位\n; 参数: X=50, Y=50, Z=50\nG00 X50.000 Y50.000 Z50.000\n\n; 步骤2: 钻孔\n; 参数: X=50, Y=50, Z=-20, F=80\nG00 X50.000 Y50.000\nG01 Z-20.000 F80\nG00 Z50.0\n\n; 步骤3: 退刀\n; 参数: Z=50\nG00 Z50.000\n\nG00 Z100.0\nM05\nM30"
    },
    {
        "id": 3,
        "name": "轮廓铣削",
        "description": "标准轮廓铣削加工工序卡示例，适用于零件外轮廓加工",
        "category": "铣削",
        "card_data": {
            "product_name": "铝制零件",
            "process_name": "轮廓铣削",
            "process_number": "OP003",
            "version": "V1.0",
            "equipment": "CNC加工中心",
            "control_system": "FANUC 0i-MF",
            "fixture": "专用夹具",
            "material": "7075铝合金",
            "tool_info": {
                "name": "球头铣刀",
                "length": 60,
                "diameter": 6
            }
        },
        "operations_data": [
            {
                "sequence": 1,
                "content": "快速定位",
                "parameters": "X=0, Y=0, Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            },
            {
                "sequence": 2,
                "content": "轮廓加工",
                "parameters": "X=80, Y=60, Z=-5, F=120",
                "equipment": "球头铣刀D6",
                "remark": "分层加工"
            },
            {
                "sequence": 3,
                "content": "返回安全高度",
                "parameters": "Z=50",
                "equipment": "CNC加工中心",
                "remark": ""
            }
        ],
        "gcode": "; 产品名称: 铝制零件\n; 工序名称: 轮廓铣削\n; 工序编号: OP003\n; 版本号: V1.0\n; 设备: CNC加工中心\n; 数控系统: FANUC 0i-MF\n; 夹具: 专用夹具\n; 材料: 7075铝合金\n; 刀具: 球头铣刀 (直径:6.000mm, 长度:60.000mm)\n\nG90 G54 G17 G40 G49 G80 G21\nM03 S4000\nG00 Z50.0\n\n; 步骤1: 快速定位\n; 参数: X=0, Y=0, Z=50\nG00 X0.000 Y0.000 Z50.000\n\n; 步骤2: 轮廓加工\n; 参数: X=80, Y=60, Z=-5, F=120\nG00 X80.000 Y60.000\nG01 Z-5.000 F120\nG00 Z50.0\n\n; 步骤3: 返回安全高度\n; 参数: Z=50\nG00 Z50.000\n\nG00 Z100.0\nM05\nM30"
    }
]

class ExampleManager:
    def get_all_examples(self) -> list:
        return EXAMPLES
    
    def get_example_by_id(self, example_id: int) -> dict:
        for example in EXAMPLES:
            if example['id'] == example_id:
                return example
        return None
    
    def get_examples_by_category(self, category: str) -> list:
        if not category:
            return EXAMPLES
        return [ex for ex in EXAMPLES if ex['category'] == category]
    
    def to_example_item(self, data: dict) -> ExampleItem:
        return ExampleItem(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            card_data=ProcessCard(**data['card_data']),
            operations_data=[Operation(**op) for op in data['operations_data']],
            gcode=data.get('gcode', '')
        )

def get_all_examples() -> list:
    manager = ExampleManager()
    return [manager.to_example_item(ex) for ex in manager.get_all_examples()]

def get_example(example_id: int) -> ExampleItem:
    manager = ExampleManager()
    data = manager.get_example_by_id(example_id)
    if data:
        return manager.to_example_item(data)
    return None

def get_examples_by_category(category: str) -> list:
    manager = ExampleManager()
    examples = manager.get_examples_by_category(category)
    return [manager.to_example_item(ex) for ex in examples]
