# G代码转换系统项目计划

## 1. 需求分析

### 1.1 核心功能需求

根据用户需求，系统需要实现以下三种转换功能：

| 输入类型 | 处理方式 | 输出 |
|---------|---------|------|
| **自然语言** | 检查参数完整性，提取工序卡信息和操作步骤 | G代码 |
| **工序图** | 使用OCR识别提取工序卡参数和操作步骤 | G代码 |
| **STL文件** | 输入工序卡参数，自动生成操作步骤 | G代码 |

### 1.2 新增功能需求

| 序号 | 功能需求 | 优先级 | 说明 |
|------|---------|--------|------|
| 1 | 多浏览器兼容性 | 高 | 支持Chrome、Firefox、Safari、Edge最新版本 |
| 2 | G代码验证机制 | 高 | 语法检查和逻辑验证，确保准确性和可执行性 |
| 3 | 工序卡示例集成 | 中 | 基于论文内容设计详细示例，作为用户操作参考 |
| 4 | 双栏对照展示 | 高 | 左侧G代码，右侧工序内容，实时对应 |
| 5 | OCR图像识别 | 高 | 光学字符识别，提取工序图中的文本和参数 |
| 6 | DeepSeek API集成 | 高 | 自然语言理解处理，提升交互体验 |

### 1.3 自然语言参数要求

系统需要从用户输入中提取以下必填参数：
- 产品名称
- 工序名称
- 工序编号
- 版本号
- 设备名称
- 数控系统
- 夹具名称
- 材料名称
- 刀具尺寸（名称、长度、直径）
- 操作步骤表格

坐标范围：X(0,200), Y(0,200), Z(0,100)

### 1.4 进阶功能

- 将自然语言、STL文件转换成工序图
- 输出时实现工序图与G代码的一一对应

## 2. 技术方案

### 2.1 技术栈选择

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端框架 | Vue3 | 3.4.x | 现代化前端框架，响应式设计 |
| 构建工具 | Vite | 6.5.x | 快速构建工具，支持ES6+ |
| 样式框架 | TailwindCSS | 3.4.x | 原子化CSS框架，跨浏览器兼容 |
| 图标库 | Lucide Vue | 0.2.x | 轻量级图标库 |
| 代码编辑器 | CodeMirror | 6.x | 专业代码编辑器组件 |
| 后端语言 | Python | 3.11 | 自然语言处理和G代码生成 |
| API框架 | FastAPI | 0.104.x | 高性能API框架 |
| 数据库 | SQLite | 3.x | 轻量级嵌入式数据库 |
| OCR服务 | PaddleOCR | 2.7.x | 中文OCR识别引擎 |
| LLM集成 | DeepSeek API | - | 自然语言理解服务 |

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     前端界面 (Vue3)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 输入模块           │ 双栏对照展示                    │    │
│  │ 自然语言/OCR/STL   │ 左侧: G代码  │ 右侧: 工序内容  │    │
│  └──────────┬────────────────────┬─────────────────────┘    │
└─────────────┼────────────────────┼──────────────────────────┘
              │                    │
              ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     API层 (FastAPI)                         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  /api/v1/natural-language  (DeepSeek API)             │ │
│  │  /api/v1/drawing/convert   (OCR识别)                  │ │
│  │  /api/v1/stl/convert       (STL解析)                  │ │
│  │  /api/v1/gcode/validate    (G代码验证)                │ │
│  │  /api/v1/examples          (工序卡示例)               │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 参数提取器   │ │ G代码生成器  │ │ G代码验证器  │        │
│  │ (DeepSeek)  │ │              │ │              │        │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤        │
│  │ OCR识别器    │ │ 工序图生成器 │ │ 示例管理器   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 核心模块设计

#### 2.3.1 参数提取器模块（集成DeepSeek API）

**功能**：利用DeepSeek API进行自然语言理解，从用户输入中提取工序卡所需参数

**输入**：用户输入的自然语言文本

**输出**：结构化的参数对象或缺失参数列表

**工作流程**：
1. 用户输入自然语言指令
2. 调用DeepSeek API进行意图识别和参数提取
3. 解析返回结果，提取工序卡所需参数
4. 检查参数完整性，返回结果

#### 2.3.2 G代码生成器模块

**功能**：根据工序卡参数和操作步骤生成G代码

**支持的G代码命令**：
- G00: 快速定位
- G01: 直线插补
- G02/G03: 圆弧插补
- G90/G91: 绝对/增量模式
- M03/M05: 主轴启动/停止
- M08/M09: 冷却液开关

#### 2.3.3 G代码验证器模块

**功能**：对生成的G代码进行语法检查和逻辑验证

**验证规则**：
| 验证类型 | 检查内容 |
|----------|---------|
| 语法验证 | G/M代码格式、参数完整性、坐标范围 |
| 逻辑验证 | 运动轨迹合理性、刀具安全高度、指令顺序 |
| 安全验证 | 是否存在碰撞风险、超程检查 |

#### 2.3.4 OCR识别器模块

**功能**：使用PaddleOCR对工序图进行光学字符识别

**识别内容**：
- 工序卡标题信息（产品名称、工序名称、编号、版本）
- 设备信息（设备名称、数控系统、夹具名称）
- 材料和刀具信息
- 操作步骤表格

#### 2.3.5 示例管理器模块

**功能**：管理和展示工序卡示例，作为用户操作参考

**示例来源**：基于论文内容设计的详细工序卡示例

### 2.4 双栏对照展示设计

**左侧面板 - G代码区域**：
- CodeMirror代码编辑器
- 语法高亮显示
- 行号显示
- 错误标记（验证失败时）

**右侧面板 - 工序内容区域**：
- 工序卡信息展示
- 操作步骤表格
- 实时同步高亮对应行
- 参数详情展开

**同步机制**：
- 点击G代码行 → 右侧对应工序内容高亮
- 点击工序步骤 → 左侧对应G代码高亮

## 3. 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── natural_language.py  # 自然语言转换API(DeepSeek)
│   │   │   ├── drawing.py           # 工序图转换API(OCR)
│   │   │   ├── stl.py               # STL文件转换API
│   │   │   ├── gcode.py             # G代码验证API
│   │   │   ├── examples.py          # 工序卡示例API
│   │   │   └── advance.py           # 进阶功能API
│   ├── core/
│   │   ├── parameter_extractor.py   # 参数提取器(DeepSeek集成)
│   │   ├── gcode_generator.py       # G代码生成器
│   │   ├── gcode_validator.py       # G代码验证器
│   │   ├── ocr_processor.py         # OCR识别器
│   │   ├── drawing_generator.py     # 工序图生成器
│   │   └── example_manager.py       # 示例管理器
│   ├── models/
│   │   └── schemas.py               # 数据模型
│   ├── utils/
│   │   ├── helpers.py               # 工具函数
│   │   └── config.py                # 配置管理(DeepSeek API Key)
│   ├── main.py                      # 应用入口
│   └── requirements.txt             # 依赖列表

frontend/
├── src/
│   ├── components/
│   │   ├── NaturalLanguageInput.vue  # 自然语言输入组件
│   │   ├── DrawingUpload.vue         # 工序图上传组件(OCR)
│   │   ├── StlUpload.vue             # STL文件上传组件
│   │   ├── GCodeEditor.vue           # G代码编辑器(CodeMirror)
│   │   ├── ProcessCard.vue           # 工序卡展示组件
│   │   ├── DualPanel.vue             # 双栏对照展示组件
│   │   └── ExampleSelector.vue       # 示例选择组件
│   ├── views/
│   │   ├── HomeView.vue              # 首页
│   │   └── AdvanceView.vue           # 进阶功能页
│   ├── api/
│   │   └── index.js                  # API调用封装
│   ├── utils/
│   │   └── validator.js              # 前端验证工具
│   ├── App.vue
│   └── main.js
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 4. 数据库设计

### 4.1 工序卡表 (process_cards)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| product_name | VARCHAR(100) | NOT NULL | 产品名称 |
| process_name | VARCHAR(100) | NOT NULL | 工序名称 |
| process_number | VARCHAR(50) | NOT NULL | 工序编号 |
| version | VARCHAR(20) | NOT NULL | 版本号 |
| equipment | VARCHAR(100) | | 设备名称 |
| control_system | VARCHAR(50) | | 数控系统 |
| fixture | VARCHAR(100) | | 夹具名称 |
| material | VARCHAR(100) | | 材料名称 |
| tool_info | TEXT | | 刀具信息(JSON) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.2 操作步骤表 (operations)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| card_id | INTEGER | FOREIGN KEY | 关联工序卡ID |
| sequence | INTEGER | NOT NULL | 序号 |
| content | TEXT | NOT NULL | 操作内容 |
| parameters | TEXT | | 工艺参数(JSON) |
| equipment | VARCHAR(100) | | 使用设备/工具 |
| remark | VARCHAR(255) | | 备注 |

### 4.3 G代码结果表 (gcode_results)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| card_id | INTEGER | FOREIGN KEY | 关联工序卡ID |
| gcode | TEXT | NOT NULL | 生成的G代码 |
| validation_result | TEXT | | 验证结果(JSON) |
| drawing_data | TEXT | | 工序图数据(JSON) |
| input_type | VARCHAR(20) | NOT NULL | 输入类型(natural/drawing/stl) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.4 工序卡示例表 (examples)

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 主键 |
| name | VARCHAR(100) | NOT NULL | 示例名称 |
| description | TEXT | | 示例描述 |
| card_data | TEXT | NOT NULL | 工序卡数据(JSON) |
| operations_data | TEXT | NOT NULL | 操作步骤数据(JSON) |
| gcode | TEXT | | 参考G代码 |
| category | VARCHAR(50) | | 示例分类 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

## 5. API接口设计

### 5.1 自然语言转换接口（集成DeepSeek）

**POST** `/api/v1/natural-language/convert`

请求体：
```json
{
  "text": "string"  // 用户输入的自然语言文本
}
```

成功响应（参数完整）：
```json
{
  "success": true,
  "message": "参数提取成功",
  "data": {
    "process_card": {
      "product_name": "string",
      "process_name": "string",
      "process_number": "string",
      "version": "string",
      "equipment": "string",
      "control_system": "string",
      "fixture": "string",
      "material": "string",
      "tool_info": {
        "name": "string",
        "length": "number",
        "diameter": "number"
      }
    },
    "operations": [
      {
        "sequence": 1,
        "content": "string",
        "parameters": "string",
        "equipment": "string",
        "remark": "string"
      }
    ],
    "gcode": "string",
    "validation": {
      "valid": true,
      "errors": []
    }
  }
}
```

失败响应（参数缺失）：
```json
{
  "success": false,
  "message": "参数不完整",
  "missing_fields": ["product_name", "process_name"]
}
```

### 5.2 工序图转换接口（集成OCR）

**POST** `/api/v1/drawing/convert`

请求体：
```json
{
  "image": "base64 string"  // 工序图图片
}
```

响应格式同自然语言接口

### 5.3 STL文件转换接口

**POST** `/api/v1/stl/convert`

请求体：
```json
{
  "stl_file": "base64 string",
  "process_card": {
    "product_name": "string",
    "process_name": "string",
    "process_number": "string",
    "version": "string",
    "equipment": "string",
    "control_system": "string",
    "fixture": "string",
    "material": "string",
    "tool_info": {
      "name": "string",
      "length": "number",
      "diameter": "number"
    }
  }
}
```

响应格式同自然语言接口

### 5.4 G代码验证接口

**POST** `/api/v1/gcode/validate`

请求体：
```json
{
  "gcode": "string",
  "process_card": {}  // 可选，用于上下文验证
}
```

响应：
```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": [
      {
        "line": 5,
        "code": "E001",
        "message": "G代码格式错误",
        "suggestion": "请检查G代码指令格式"
      }
    ],
    "warnings": [
      {
        "line": 10,
        "message": "建议添加安全高度"
      }
    ]
  }
}
```

### 5.5 工序卡示例接口

**GET** `/api/v1/examples`

请求参数：
- `category`: 示例分类（可选）

响应：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "铣削加工示例",
      "description": "标准铣削加工工序卡示例",
      "category": "铣削",
      "card_data": {},
      "operations_data": [],
      "gcode": "string"
    }
  ]
}
```

**GET** `/api/v1/examples/{id}`

响应：返回单个示例详情

### 5.6 进阶功能接口

**POST** `/api/v1/advance/generate-drawing`

请求体：
```json
{
  "input_type": "natural|stl",
  "input_data": "string",
  "process_card": {}  // 可选，用于STL输入
}
```

响应：
```json
{
  "success": true,
  "data": {
    "drawings": [
      {
        "step": 1,
        "drawing": "base64 image",
        "gcode_segment": "string",
        "operation_content": "string"
      }
    ]
  }
}
```

## 6. 部署与运行

### 6.1 环境变量配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| DEEPSEEK_API_KEY | DeepSeek API密钥 | sk-xxx |
| DEEPSEEK_API_URL | DeepSeek API地址 | https://api.deepseek.com |
| DATABASE_URL | 数据库连接地址 | sqlite:///./app.db |
| PORT | 服务端口 | 8000 |

### 6.2 开发环境

**后端启动**：
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端启动**：
```bash
cd frontend
npm install
npm run dev
```

### 6.3 生产环境

使用Docker Compose部署：
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - DEEPSEEK_API_URL=https://api.deepseek.com
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 7. 风险与依赖

### 7.1 潜在风险

| 风险 | 影响 | 缓解措施 | 优先级 |
|------|------|---------|--------|
| DeepSeek API调用失败 | 自然语言解析不可用 | 增加重试机制和错误处理 | 高 |
| OCR识别精度不足 | 工序图参数提取错误 | 提供手动修正功能，增加置信度阈值 | 高 |
| G代码验证遗漏 | 生成的代码不可执行 | 完善验证规则，增加测试用例 | 高 |
| 浏览器兼容性问题 | 部分浏览器无法正常使用 | 使用TailwindCSS，进行多浏览器测试 | 中 |
| STL文件解析复杂 | 文件处理失败 | 使用成熟的STL解析库(trimesh) | 中 |

### 7.2 外部依赖

| 依赖名称 | 用途 | 版本 |
|----------|------|------|
| deepseek-chat | DeepSeek API客户端 | 最新 |
| paddleocr | OCR文字识别 | 2.7.x |
| trimesh | STL文件解析 | 3.22.x |
| spaCy | 自然语言处理 | 3.7.x |
| Pillow | 图像处理 | 10.2.x |
| matplotlib | 工序图绘制 | 3.8.x |
| pydantic | 数据验证 | 2.6.x |

## 8. 项目开发计划

### 8.1 开发阶段与优先级

| 阶段 | 任务 | 子任务 | 优先级 | 预估时间 | 负责人 |
|------|------|--------|--------|---------|--------|
| **第一阶段** | 项目初始化 | 后端框架搭建 | 高 | 2天 | 后端开发 |
| | | 前端框架搭建 | 高 | 2天 | 前端开发 |
| | | 数据库设计与初始化 | 高 | 1天 | 后端开发 |
| **第二阶段** | DeepSeek集成 | API接入与配置 | 高 | 2天 | 后端开发 |
| | | 参数提取器开发 | 高 | 3天 | 后端开发 |
| | | 自然语言转换API | 高 | 2天 | 后端开发 |
| **第三阶段** | OCR集成 | PaddleOCR配置 | 高 | 2天 | 后端开发 |
| | | OCR识别器开发 | 高 | 3天 | 后端开发 |
| | | 工序图转换API | 高 | 2天 | 后端开发 |
| **第四阶段** | G代码生成与验证 | G代码生成器开发 | 高 | 3天 | 后端开发 |
| | | G代码验证器开发 | 高 | 3天 | 后端开发 |
| | | 验证API开发 | 高 | 2天 | 后端开发 |
| **第五阶段** | 前端界面开发 | 输入模块组件 | 高 | 3天 | 前端开发 |
| | | 双栏对照展示组件 | 高 | 4天 | 前端开发 |
| | | 示例选择组件 | 中 | 2天 | 前端开发 |
| | | 响应式布局适配 | 高 | 2天 | 前端开发 |
| **第六阶段** | 示例管理 | 工序卡示例设计 | 中 | 3天 | 全栈 |
| | | 示例数据录入 | 中 | 2天 | 全栈 |
| | | 示例API开发 | 中 | 2天 | 后端开发 |
| **第七阶段** | 进阶功能 | STL解析模块 | 中 | 3天 | 后端开发 |
| | | 工序图生成器 | 中 | 3天 | 后端开发 |
| | | 进阶API开发 | 中 | 2天 | 后端开发 |
| **第八阶段** | 测试与优化 | 多浏览器兼容性测试 | 高 | 3天 | 测试 |
| | | G代码验证测试 | 高 | 2天 | 测试 |
| | | 性能优化 | 中 | 2天 | 全栈 |
| | | Bug修复 | 高 | 3天 | 全栈 |

### 8.2 里程碑与时间节点

| 里程碑 | 完成标准 | 预计时间 |
|--------|---------|---------|
| M1 | 项目基础架构搭建完成 | 第5天 |
| M2 | 自然语言转换功能完成 | 第12天 |
| M3 | OCR识别功能完成 | 第19天 |
| M4 | G代码生成与验证完成 | 第27天 |
| M5 | 前端界面开发完成 | 第36天 |
| M6 | 示例管理功能完成 | 第43天 |
| M7 | 进阶功能完成 | 第51天 |
| M8 | 测试完成，项目交付 | 第60天 |

### 8.3 资源分配

| 角色 | 人数 | 职责 |
|------|------|------|
| 后端开发 | 1 | API开发、核心模块实现 |
| 前端开发 | 1 | 界面开发、用户交互 |
| 测试人员 | 1 | 功能测试、兼容性测试 |
| 产品/设计 | 1 | 需求分析、UI设计 |

---

**计划版本**：v2.0  
**创建日期**：2026-05-15  
**最后更新**：2026-05-15