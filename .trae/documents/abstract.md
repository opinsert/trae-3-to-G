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
│   │   │   ├── gcode_generator.py        # G代码生成器(型腔/斜坡/壁面精修)
│   │   │   ├── gcode_validator.py        # G代码验证器
│   │   │   ├── ocr_processor.py          # OCR处理器(Tesseract)
│   │   │   ├── stl_analyzer.py           # STL几何分析器(trimesh,六方向)
│   │   │   ├── process_planner.py        # DeepSeek工艺规划器
│   │   │   └── example_manager.py        # 示例管理器
│   │   ├── models/                       # 数据模型
│   │   │   └── schemas.py                # Pydantic模型
│   │   ├── utils/                       # 工具配置
│   │   │   ├── config.py                # 配置管理
│   │   │   └── conversion.py            # 共享转换工具
│   │   ├── data/                        # 本地数据存储
│   │   │   └── examples.json            # 示例数据
│   │   └── main.py                      # 应用入口
│   ├── tests/                            # 单元测试
│   │   ├── conftest.py                   # pytest配置
│   │   ├── test_gcode_generator.py       # G代码生成器测试
│   │   ├── test_parameter_extractor.py   # 参数提取器测试
│   │   ├── test_schemas.py               # 数据模型测试
│   │   └── test_example_manager.py       # 示例管理器测试
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
- 请求体: `{"stl_file": "base64编码的STL", "process_card": {...}, "generate_gcode": false, "direction": "+Z"}`
- 返回: 包含工序列表或G代码（根据generate_gcode参数）
- direction参数可选，指定加工方向(+Z/-Z/+X/-X/+Y/-Y)

### STL六方向规划
- **POST** `/api/v1/stl/plan-directions`
- 请求体: `{"stl_file": "base64编码的STL", "process_card": {...}}`
- 返回: 六方向几何分析、DeepSeek推荐加工顺序、各方向尺寸

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
12. **单元测试覆盖**: 139个单元测试用例，覆盖G代码生成器、参数提取器、数据模型、示例管理器等核心模块
13. **STL几何解析**: 使用trimesh解析STL网格，提取包围盒、截面、法向分布、边界环等特征
14. **DeepSeek工艺规划**: 将几何分析数据送入DeepSeek，智能推荐工序顺序和加工策略
15. **六方向加工**: 零件自动旋转到6个装夹方向分别生成G代码，DeepSeek推荐加工顺序
16. **型腔铣削安全策略**: 斜坡进刀（禁止直插）、分层粗加工留余量、单次壁面精修消除层痕、底面光刀

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

- [x] 完整的DeepSeek API集成（自然语言提取 + STL工艺规划）
- [x] STL文件解析与路径规划（trimesh几何解析 + 型腔铣削刀路）
- [ ] G代码在线仿真预览（已有ncviewer跳转验证）
- [ ] 批量处理功能
- [x] 导出功能(CSV工序表下载)

## 十一、修改记录

| 日期 | 修改人 | 修改内容 | Git提交ID | 目的 | 影响范围 |
|------|--------|----------|-----------|------|----------|
| 2026-05-15 | AI Assistant | 增强G代码转换器功能：1) 添加自然语言输入时的参数状态实时显示；2) 创建独立的G代码和工序信息弹窗；3) 添加G代码在线验证功能 | - | 提升用户体验，让用户更清晰了解参数完整性，提供更好的结果展示和验证方式 | NaturalLanguageInput.vue, GCodeModal.vue, ProcessCardModal.vue, App.vue, natural_language.py |
| 2026-05-16 | AI Assistant | 修复参数识别bug：1) 使用正则表达式更灵活匹配各种格式；2) 支持**和|分隔符；3) 优化参数提取逻辑 | - | 修复参数无法正确识别的问题 | NaturalLanguageInput.vue |
| 2026-05-16 | AI Assistant | 更新后端参数提取和添加调试日志：1) 更新后端正则匹配逻辑；2) 添加详细调试日志 | - | 修复后端参数提取问题，便于调试 | parameter_extractor.py, natural_language.py, NaturalLanguageInput.vue |
| 2026-05-16 | AI Assistant | OCR引擎替换与功能增强：1) 将PaddleOCR替换为Tesseract OCR解决兼容性问题；2) 添加详细的日志打印功能（前后端）；3) 修复React数组渲染错误（#185）；4) 增强操作步骤验证逻辑；5) 添加多种加工方式支持（平面铣削、轮廓铣削、钻孔、攻丝等10种） | - | 解决PaddleOCR安装问题，提升OCR识别稳定性，增强代码质量和可维护性 | ocr_processor.py, DrawingUpload.vue, gcode_generator.py |
| 2026-06-24 | AI Assistant | 错误处理增强：1) 将ocr_processor.py中8处裸异常捕获替换为具体异常类型；2) 修复parameter_extractor.py中DeepSeek回退静默丢失错误上下文问题；3) API端点异常处理添加类型信息和堆栈跟踪；4) 前端添加FileReader.onerror处理和错误详情反馈 | - | 消除静默失败，确保错误正确传播和反馈给用户 | ocr_processor.py, parameter_extractor.py, drawing.py, stl.py, natural_language.py, advance.py, DrawingUpload.vue, StlUpload.vue, NaturalLanguageInput.vue, AdvanceView.vue |
| 2026-06-24 | AI Assistant | 消除重复代码：1) 提取 process_card_to_params 和 convert_params_to_gcode 共享工具；2) 提取 _add_tool_change_block 和 _extract_card_params 消除 gcode_generator.py 中6处重复的换刀序列和8处参数提取；3) 提取 _empty_ocr_result 工厂函数消除 ocr_processor.py 中3处重复的结果字典初始化；4) 简化 API 路由处理器使用共享工具 | - | 减少代码重复，提升可维护性 | conversion.py, gcode_generator.py, ocr_processor.py, natural_language.py, drawing.py, stl.py |
| 2026-06-24 | AI Assistant | 安全增强：1) CORS 限制从通配符改为白名单模式；2) HTTP 方法限制为 GET/POST；3) 请求头限制为 Content-Type/Authorization；4) 生产环境关闭 /docs 和 /redoc 文档 | - | 修复安全漏洞，防止未授权访问和敏感信息泄露 | main.py |
| 2026-06-25 | AI Assistant | STL文件BUG修复：1) STL文件大小写后缀不支持（.STL被过滤）；2) 工序图组件表单默认值清空改为placeholder灰色提示文字 | - | 修复STL上传无响应问题，优化工序图表单用户体验 | StlUpload.vue, DrawingUpload.vue |
| 2026-06-25 | AI Assistant | STL后端BUG修复：1) conversion.py中validation=None导致Pydantic ValidationError（根因）；2) parameter_extractor.py中if not value把0误判为缺失；3) 前端StlUpload.vue的catch块无声吞错加alert反馈 | - | 修复STL上传后无法生成G代码的根本原因 | conversion.py, parameter_extractor.py, StlUpload.vue |
| 2026-06-25 | AI Assistant | STL组件功能增强：1) G代码面板添加"在线验证"按钮跳转ncviewer.com；2) 工序表格添加复制(TSV)和下载CSV功能 | - | 提升STL组件实用性和用户体验 | StlUpload.vue |
| 2026-06-25 | AI Assistant | STL几何解析与DeepSeek智能工艺规划（核心重构）：1) 新建stl_analyzer.py用trimesh解析STL网格（包围盒、截面分析、法向分布、边界环检测）；2) 新建process_planner.py用DeepSeek分析几何特征并规划工序顺序；3) GCodeGenerator新增型腔铣削、斜坡进刀、壁面精修、底面光刀等安全策略；4) stl.py替换硬编码假工序为真实几何分析 | - | 实现真正的STL→G代码智能转换，从硬编码假数据升级为真实几何分析+AI工艺规划 | stl_analyzer.py(新), process_planner.py(新), gcode_generator.py, stl.py |
| 2026-06-25 | AI Assistant | 六方向加工支持：1) stl_analyzer.py新增6方向旋转矩阵和各方向独立分析；2) plan-directions端点返回六方向几何数据+DeepSeek推荐加工顺序；3) 前端StlUpload.vue新增分方向tab面板显示各方向G代码 | - | 支持多面装夹加工，每个方向独立生成G代码 | stl_analyzer.py, stl.py, StlUpload.vue, api/index.js |
| 2026-06-25 | AI Assistant | 批量生产标准优化：1) 型腔粗加工留0.3mm壁面余量；2) 删除每层壁面精修（从22次减为1次最终精修消除层痕）；3) 底面精加工改为斜坡进刀消除直插风险；4) 粗加工边界缩小减少空切；5) G代码行数从773行优化至544行 | - | 消除加工时间浪费和断刀风险，达到批量生产标准 | stl_analyzer.py, gcode_generator.py |

## 十二、注意事项

1. 需要配置 `.env` 文件中的 DeepSeek API 密钥
2. 前端依赖安装需使用 `--cache ".npm_cache"` 参数避免系统权限问题
3. 数据文件存放在 `backend/app/data/` 目录，确保有读写权限
4. Tesseract OCR 已配置在 `C:\Users\21242\AppData\Local\Programs\Tesseract-OCR`，已包含简体中文语言包
5. 所有API接口都有详细的日志输出，便于调试和问题排查
