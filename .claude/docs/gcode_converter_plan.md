# G代码转换系统项目计划

## 1. 项目目标

系统支持将自然语言、工序图图片和 STL 文件转换为 CNC 加工用 G 代码，并提供工艺信息展示、刀路预览和 G 代码安全验证。所有生成结果均为待审核程序，只有通过系统验证并经技术人员确认后才能上机。

| 输入类型 | 处理方式 | 输出 |
|---------|---------|------|
| 自然语言 | AI 参数提取与本地规则回退 | 工序卡、工序、G 代码 |
| 工序图 | 视觉 GPT 结构化识别 | 工序卡、工序、G 代码 |
| STL 文件 | 网格几何分析与工艺规划 | 分方向工序、G 代码 |

## 2. 核心能力

- 自然语言工序卡参数提取与完整性检查
- 工序图 OCR 结构化提取和手动修正
- STL 网格加载、六方向几何分析和工艺规划
- G 代码生成、语法与安全检查
- G 代码本地刀路预览与外部查看
- 内置工序卡示例
- 基于输入工步生成工序图表格数据

## 3. 技术栈

| 分类 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 | 交互界面与状态管理 |
| 构建工具 | Vite | 前端开发与生产构建 |
| 样式 | Tailwind CSS | 界面样式 |
| 图标 | Lucide Vue | 图标组件 |
| 三维与刀路预览 | Three.js、gcode-preview | STL 与 G 代码可视化 |
| 后端 | FastAPI、Python | REST API 与业务逻辑 |
| STL 解析 | trimesh | 网格加载、旋转与几何分析 |
| 图像处理 | Pillow | 图片处理 |
| OCR | AI 中转站视觉模型 | 工序图结构化信息提取 |
| AI 工艺规划 | AI 中转站 `gpt-5.6-terra` | 自然语言参数提取与工艺规划 |
| 数据校验 | Pydantic | API 请求和响应模型 |

## 4. 架构

```text
Vue 3 前端
  ├── 自然语言输入
  ├── 工序图上传与 OCR
  ├── STL 上传与三维预览
  └── G 代码展示、验证与刀路预览
          │
          ▼
FastAPI API
  ├── /api/v1/natural-language
  ├── /api/v1/drawing
  ├── /api/v1/stl
  ├── /api/v1/gcode
  ├── /api/v1/examples
  └── /api/v1/advance
          │
          ▼
核心模块
  ├── parameter_extractor.py
  ├── ocr_processor.py
  ├── stl_analyzer.py
  ├── process_planner.py
  ├── gcode_generator.py
  ├── gcode_validator.py
  └── example_manager.py
```

## 5. API

| 接口 | 用途 |
|------|------|
| `POST /api/v1/natural-language/precheck` | 提取并检查自然语言参数 |
| `POST /api/v1/natural-language/convert` | 自然语言转换为 G 代码 |
| `POST /api/v1/drawing/ocr-extract` | 识别工序图信息 |
| `POST /api/v1/drawing/convert` | 根据工序卡与步骤生成 G 代码 |
| `POST /api/v1/stl/convert` | 指定加工方向的 STL 工序或 G 代码生成 |
| `POST /api/v1/stl/plan-directions` | STL 六方向分析与加工顺序建议 |
| `POST /api/v1/gcode/validate` | G 代码安全验证 |
| `GET /api/v1/examples` | 获取工序卡示例 |
| `POST /api/v1/advance/generate-drawing` | 根据输入工步生成工序图表格数据 |

## 6. 配置

后端通过 `backend/.env` 配置外部服务。当前自然语言、STL 工艺规划和视觉 OCR 共用 `VISION_OCR_*` 配置。

| 变量 | 用途 |
|------|------|
| `VISION_OCR_API_KEY` | 视觉与文本 AI API Key |
| `VISION_OCR_BASE_URL` | 视觉与文本 AI 中转站地址 |
| `VISION_OCR_MODEL` | 视觉与文本 AI 模型 |
| `CORS_ALLOWED_ORIGINS` | 允许访问后端的前端域名 |

## 7. 运行与验证

后端（PowerShell）：

```powershell
Set-Location backend
pip install -r app\requirements.txt
python -m pytest
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

前端（PowerShell）：

```powershell
Set-Location frontend
npm install
npm run build
npm run dev
```

关键验证项：

- 自然语言、OCR、STL 三条转换链路均返回有效响应。
- STL 在不同 `direction` 下按对应旋转方向分析。
- 生成 G 代码后调用 `/api/v1/gcode/validate`。
- 未配置 AI 服务时，系统明确返回配置错误；OCR 模型必须支持视觉输入。

**计划版本**：v3.0  
**最后更新**：2026-08-08
