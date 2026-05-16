# G代码转换系统 - 项目摘要

## 一、项目概述

本项目是一个基于 Vue3 + FastAPI 的 G代码转换系统，支持将自然语言、工序图和 STL 文件转换为可使用的 G代码。系统采用本地文件存储，无需数据库。

## 二、技术栈

### 后端
- **框架**: FastAPI 0.104.1
- **语言**: Python 3.9+
- **数据存储**: 本地 JSON 文件
- **依赖**: uvicorn, pydantic, pydantic-settings, python-dotenv
- **OCR引擎**: Tesseract OCR 5.5.0

### 前端
- **框架**: Vue 3.4+
- **构建工具**: Vite 5.2+
- **样式**: TailwindCSS 3.4+
- **图标**: Lucide Vue Next
- **HTTP客户端**: Axios

## 三、核心功能模块

| 模块 | 功能描述 | 文件位置 |
|------|----------|----------|
| 自然语言转换 | 将自然语言描述转换为G代码 | `backend/app/api/v1/natural_language.py` |
| 工序图识别 | OCR识别工序图并生成G代码 | `backend/app/api/v1/drawing.py` |
| STL文件转换 | 将STL模型转换为加工G代码 | `backend/app/api/v1/stl.py` |
| G代码验证 | 语法检查、逻辑验证、坐标范围验证 | `backend/app/api/v1/gcode.py` |
| 示例管理 | 提供工序卡示例供用户参考 | `backend/app/api/v1/examples.py` |

## 四、项目结构

```
trae-3 to g/
├── backend/                              # 后端服务
│   ├── app/
│   │   ├── api/v1/                       # API路由
│   │   │   ├── natural_language.py       # 自然语言转换
│   │   │   ├── drawing.py                # 工序图转换
│   │   │   ├── stl.py                    # STL文件转换
│   │   │   ├── gcode.py                  # G代码验证
│   │   │   ├── examples.py               # 示例管理
│   │   │   └── advance.py                # 进阶功能
│   │   ├── core/                         # 核心模块
│   │   │   ├── parameter_extractor.py    # 参数提取器(DeepSeek API)
│   │   │   ├── gcode_generator.py        # G代码生成器
│   │   │   ├── gcode_validator.py        # G代码验证器
│   │   │   ├── ocr_processor.py          # OCR处理器(Tesseract)
│   │   │   └── example_manager.py        # 示例管理器
│   │   ├── models/                       # 数据模型
│   │   │   └── schemas.py                # Pydantic模型
│   │   ├── utils/                       # 工具配置
│   │   │   └── config.py                # 配置管理
│   │   ├── data/                        # 本地数据存储
│   │   │   └── examples.json            # 示例数据
│   │   └── main.py                      # 应用入口
│   └── requirements.txt                  # Python依赖
├── frontend/                             # 前端应用
│   ├── src/
│   │   ├── components/                   # 组件
│   │   │   ├── NaturalLanguageInput.vue  # 自然语言输入
│   │   │   ├── DrawingUpload.vue         # 工序图上传
│   │   │   ├── StlUpload.vue            # STL文件上传
│   │   │   ├── ExampleSelector.vue      # 示例选择器
│   │   │   ├── GCodeModal.vue           # G代码弹窗
│   │   │   └── ProcessCardModal.vue     # 工序卡弹窗
│   │   ├── views/
│   │   │   └── AdvanceView.vue         # 进阶功能视图
│   │   ├── api/
│   │   │   └── index.js                # API封装
│   │   ├── App.vue                     # 主应用
│   │   ├── main.js                     # 入口文件
│   │   └── style.css                   # 全局样式
│   ├── index.html                      # HTML模板
│   ├── vite.config.js                  # Vite配置
│   ├── tailwind.config.js              # TailwindCSS配置
│   ├── postcss.config.js               # PostCSS配置
│   └── package.json                    # 前端依赖
├── .trae/
│   ├── documents/                      # 项目文档
│   │   ├── abstract.md                 # 项目摘要
│   │   └── gcode_converter_plan.md     # 项目计划
│   └── rules/                         # 项目规则
│       └── 技术要求.md                 # 技术要求文档
└── agent.md                            # 自动化流程规范
```

## 五、API接口说明

### 自然语言转换
- **POST** `/api/v1/natural-language/convert`
- 请求体: `{"input_text": "自然语言描述"}`
- 返回: 包含G代码和工序卡信息

### 工序图转换
- **POST** `/api/v1/drawing/convert`
- 请求体: `{"process_card": {...}, "operations": [...]}`
- 返回: 包含识别结果和G代码

### OCR图片识别
- **POST** `/api/v1/drawing/ocr-extract`
- 请求体: `{"image": "base64编码的图片"}`
- 返回: 包含识别的工序卡信息

### STL文件转换
- **POST** `/api/v1/stl/convert`
- 请求体: `{"stl_data": "base64编码的STL文件"}`
- 返回: 包含加工路径和G代码

### G代码验证
- **POST** `/api/v1/gcode/validate`
- 请求体: `{"gcode": "G代码内容"}`
- 返回: 验证结果(valid, errors, warnings)

### 示例管理
- **GET** `/api/v1/examples/list` - 获取所有示例
- **GET** `/api/v1/examples/{id}` - 获取单个示例
- **POST** `/api/v1/examples/add` - 添加示例

## 六、数据存储方案

本项目采用**本地文件存储**，无需数据库：

1. **示例数据**: `backend/app/data/examples.json`
   - 存储工序卡示例
   - 包含产品信息、工序步骤、G代码模板

2. **配置文件**: `backend/.env`
   - DeepSeek API密钥
   - 应用配置参数

## 七、启动方式

### 后端服务
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端服务
```bash
cd frontend
npm install --cache ".npm_cache"
npm run dev
```

### 访问地址
- 前端应用: `http://localhost:5173`
- 后端API文档: `http://localhost:8000/docs`

## 八、核心功能特点

1. **自然语言处理**: 集成DeepSeek API，支持参数提取和验证
2. **G代码生成**: 根据工序卡参数自动生成多种加工操作的G代码
3. **G代码验证**: 语法检查、逻辑验证、坐标范围验证
4. **独立弹窗展示**: G代码与工序信息分别在独立弹窗中展示
5. **OCR图片识别**: 使用Tesseract OCR识别工序图图片
6. **参数状态实时显示**: 输入时实时显示已满足和缺失的参数
7. **在线验证**: 支持跳转到ncviewer.com验证G代码
8. **多种加工方式支持**: 平面铣削、轮廓铣削、钻孔、攻丝、铰孔、镗孔、倒角、螺纹铣削、深孔钻、往复铣削
9. **本地存储**: 使用文件存储，无需数据库
10. **响应式设计**: 支持多浏览器(Chrome、Firefox、Safari、Edge)
11. **详细日志系统**: 前后端都有完整的日志输出，便于调试

## 九、支持的加工方式

| 加工方式 | 关键词 | G代码特点 |
|----------|--------|----------|
| 平面铣削 | 铣平面、平面 | 往复走刀路径 |
| 轮廓铣削 | 轮廓、外形 | G01直线插补 |
| 圆孔铣削 | 圆孔、铣圆 | 螺旋插补G02/G03 |
| 钻孔 | 钻孔、打孔 | G81固定循环 |
| 攻丝 | 攻丝、攻牙 | G84攻丝循环 |
| 铰孔 | 铰孔 | G85铰孔循环 |
| 镗孔 | 镗孔 | G86镗孔循环 |
| 倒角 | 倒角 | G02圆弧插补 |
| 螺纹铣削 | 螺纹 | 螺旋插补路径 |
| 深孔钻 | 深孔、啄钻 | 分段进给 |
| 往复铣削 | 往复、来回 | 自定义步进 |

## 十、待完善功能

- [ ] 完整的DeepSeek API集成
- [ ] STL文件解析与路径规划
- [ ] G代码仿真预览
- [ ] 批量处理功能
- [ ] 导出功能(CSV, PDF)

## 十一、修改记录

| 日期 | 修改人 | 修改内容 | Git提交ID | 目的 | 影响范围 |
|------|--------|----------|-----------|------|----------|
| 2026-05-15 | AI Assistant | 增强G代码转换器功能：1) 添加自然语言输入时的参数状态实时显示；2) 创建独立的G代码和工序信息弹窗；3) 添加G代码在线验证功能 | - | 提升用户体验，让用户更清晰了解参数完整性，提供更好的结果展示和验证方式 | NaturalLanguageInput.vue, GCodeModal.vue, ProcessCardModal.vue, App.vue, natural_language.py |
| 2026-05-16 | AI Assistant | 修复参数识别bug：1) 使用正则表达式更灵活匹配各种格式；2) 支持**和|分隔符；3) 优化参数提取逻辑 | - | 修复参数无法正确识别的问题 | NaturalLanguageInput.vue |
| 2026-05-16 | AI Assistant | 更新后端参数提取和添加调试日志：1) 更新后端正则匹配逻辑；2) 添加详细调试日志 | - | 修复后端参数提取问题，便于调试 | parameter_extractor.py, natural_language.py, NaturalLanguageInput.vue |
| 2026-05-16 | AI Assistant | OCR引擎替换与功能增强：1) 将PaddleOCR替换为Tesseract OCR解决兼容性问题；2) 添加详细的日志打印功能（前后端）；3) 修复React数组渲染错误（#185）；4) 增强操作步骤验证逻辑；5) 添加多种加工方式支持（平面铣削、轮廓铣削、钻孔、攻丝等10种） | - | 解决PaddleOCR安装问题，提升OCR识别稳定性，增强代码质量和可维护性 | ocr_processor.py, DrawingUpload.vue, gcode_generator.py |

## 十二、注意事项

1. 需要配置 `.env` 文件中的 DeepSeek API 密钥
2. 前端依赖安装需使用 `--cache ".npm_cache"` 参数避免系统权限问题
3. 数据文件存放在 `backend/app/data/` 目录，确保有读写权限
4. Tesseract OCR 已配置在 `C:\Users\21242\AppData\Local\Programs\Tesseract-OCR`，已包含简体中文语言包
5. 所有API接口都有详细的日志输出，便于调试和问题排查
