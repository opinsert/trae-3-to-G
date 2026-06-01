# G代码转换系统 - Agent 自动化流程规范

## 1. 代码修改管理流程

### 1.0 需求分析与开源搜索

**前置要求**：在开发新功能或进行非平凡修改之前，智能体必须执行此流程。简单bug修复、格式调整、文档更新等可跳过此步骤。

**执行步骤（按顺序）：**

1. **搜索开源资源**
   - 访问GitHub、Gitee等主流开源平台
   - 使用与用户需求相关的关键词进行搜索
   - 查找是否已有实现相同或类似功能的开源项目/代码库

2. **展示搜索结果**
   - 将找到的相关项目列表呈现给用户
   - 包含项目名称、简介、Star数、许可证类型等关键信息

3. **等待用户确认**
   - 必须获得用户明确同意后才能继续下一步
   - 用户可选择：使用开源项目 / 自行开发 / 混合方案

4. **执行安装（如用户同意使用开源项目）**
   - 优先检查项目中是否已有对应安装位置
   - 如有：在该位置进行集成安装
   - 如无：在沙箱环境中新建必要文件

**注意事项**：
- 搜索范围不限于完全匹配，也包括可借鉴的组件或工具
- 需评估开源项目的活跃度、维护状态和许可证兼容性

### 1.1 提交前检查

- 每次完成代码修改后，必须执行以下检查：
  - ✅ 代码通过所有必要的测试
  - ✅ 后端服务正常启动（在 `backend/` 目录下执行 `uvicorn app.main:app --host 0.0.0.0 --port 8000`）
  - ✅ 前端服务正常启动（`npm run dev`）
  - ✅ 确保没有敏感信息泄露（API密钥等）
  - ✅ 确保代码符合项目规范

### 1.2 Git 提交规范（Conventional Commits）

- **提交时机**：每次代码修改完成并通过检查后
- **提交信息格式**：
  ```
  <类型>(<范围>): <简短描述>
  
  <详细说明（可选）>
  
  - 修改内容
  - 涉及文件
  - 影响范围
  ```
- **提交类型**：
  - `feat`: 新功能（如新增加工方式支持）
  - `fix`: 错误修复（如OCR识别bug）
  - `refactor`: 代码重构（如优化参数提取逻辑）
  - `docs`: 文档更新（如API文档）
  - `style`: 格式调整（如前端样式）
  - `test`: 测试相关（如添加测试脚本）
  - `chore`: 杂项任务（如更新依赖、配置）

## 2. 修改记录文档管理

### 2.1 abstract.md 文件

- **位置**：`.trae/documents/abstract.md`
- **生成时机**：项目初始化阶段
- **更新时机**：每次代码修改完成并提交后

### 2.2 abstract.md 文档结构

```markdown
# G代码转换系统 - 修改记录

## 项目概述

本项目是一个G代码转换系统，支持从自然语言、工序图图片和STL文件生成CNC加工用G代码。

### 技术栈
- 前端：Vue3 + Vite + TailwindCSS
- 后端：FastAPI + Python
- OCR服务：百度智能云OCR
- 端口配置：后端8000，前端5175

## 修改记录

| 日期 | 修改人 | 修改内容 | Git提交ID | 目的 | 影响范围 |
|------|--------|----------|-----------|------|----------|
| YYYY-MM-DD | AI Assistant | 描述 | hash | 说明 | 影响 |
```

### 2.3 更新要求

- 更新内容必须包含：
  - 修改日期（YYYY-MM-DD 格式）
  - 修改人（AI Assistant）
  - 修改内容概述
  - Git 提交记录 ID
  - 修改目的
  - 影响范围

## 3. 执行要求

### 3.1 执行责任人

- **主要执行人**：AI Assistant (Agent)
- **监督人**：项目开发者

### 3.2 执行流程

1. **代码修改阶段**
   - 执行代码修改
   - 测试核心功能（OCR识别、G代码生成）
   - 运行前后端服务验证

2. **提交阶段**
   - 生成规范的提交信息（Conventional Commits）
   - 执行 git add 和 git commit
   - 获取提交 ID

3. **文档更新阶段**
   - 打开 `.trae/documents/abstract.md`
   - 添加新的修改记录条目
   - 更新可合并到功能提交中，或作为独立 `docs:` 提交（较大变更时）

## 4. 文件位置

| 文件/目录 | 路径 | 说明 |
|-----------|------|------|
| agent.md | `/agent.md` | 自动化流程规范 |
| abstract.md | `.trae/documents/abstract.md` | 修改记录文档 |
| 后端代码 | `backend/app/` | FastAPI应用 |
| 前端代码 | `frontend/src/` | Vue3组件 |
| 环境配置 | `backend/.env` | API密钥配置 |
| OCR处理器 | `backend/app/core/ocr_processor.py` | 百度OCR集成 |
| 参数提取器 | `backend/app/core/parameter_extractor.py` | DeepSeek AI + 正则提取 |
| G代码生成器 | `backend/app/core/gcode_generator.py` | G代码生成逻辑 |
| G代码验证器 | `backend/app/core/gcode_validator.py` | G代码语法验证 |
| 数据模型 | `backend/app/models/schemas.py` | Pydantic 数据模型 |
| API路由 | `backend/app/api/v1/` | 6组REST API端点 |
| 示例管理 | `backend/app/core/example_manager.py` | 内置示例管理 |
| 前端API层 | `frontend/src/api/index.js` | Axios API封装 |
| 前端组件 | `frontend/src/components/` | Vue3 SFC组件 |

## 5. 注意事项

- ⚠️ 所有 Git 操作需在项目根目录执行
- ⚠️ 提交信息应使用中文，保持一致性
- ⚠️ abstract.md 的更新作为独立提交，提交信息标注 `docs:`
- ⚠️ **敏感信息禁止提交**：API密钥、密码等应存储在 `.env` 文件中，且 `.env` 已加入 `.gitignore`
- ⚠️ OCR模型文件较大，如需提交需评估存储成本
- ⚠️ 测试图片（如 `test.jpg`）不应提交到仓库

## 6. 核心功能验证清单

每次修改后应验证以下功能：

| 功能 | 验证方式 | 预期结果 |
|------|----------|----------|
| 自然语言转换 | 输入工序卡文本 | 正确提取参数并生成G代码 |
| 工序图OCR识别 | 上传工序卡图片 | 正确识别文字并填充表单 |
| STL文件转换 | 上传STL模型 | ⚠️ 当前为桩代码，需后续实现 |
| G代码验证 | 生成的G代码 | 通过验证无语法错误 |
| 前后端通信 | 所有API调用 | 返回200状态码 |
| EasyOCR本地模型 | 本地OCR识别 | ⚠️ 模型已下载但代码中未调用 |

---

# 二、开发准则（12条规则）

These rules apply to every task in this project unless explicitly overridden.
Bias: caution over speed on non-trivial work. Use judgment on trivial tasks.

## Rule 1 - Think Before Coding

- State assumptions explicitly. If uncertain, ask rather than guess.
- Present multiple interpretations when ambiguity exists.
- Push back when a simpler approach exists
- Stop when confused. Name what's unclear.

## Rule 2 - Simplicity First

- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked. No abstractions for single-use code.
- Test: would a senior engineer say this is overcomplicated? If yes, simplify.

## Rule 3 - Surgical Changes

- Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor what isn't broken. Match existing style.

## Rule 4 - Goal-Driven Execution

- Define success criteria. Loop until verified.
- Don't follow steps. Define success and iterate.
- Strong success criteria let you loop independently.

## Rule 5 - Use the model only for judgment calls

- Use me for: classification, drafting, summarization, extraction.
- Do NOT use me for: routing, retries, deterministic transforms.
- If code can answer, code answers.

## Rule 6 - Token budgets are not advisory

- Per-task: 4,000 tokens. Per-session: 30,000 tokens.
- If approaching budget, summarize and start fresh.
- Surface the breach. Do not silently overrun.

## Rule 7 - Surface conflicts, don't average them

- If two patterns contradict, pick one (more recent / more tested).
- Explain why. Flag the other for cleanup.
- Don't blend conflicting patterns.

## Rule 8 - Read before you write

- Before adding code, read exports, immediate callers, shared utilities.
- "Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

## Rule 9 - Tests verify intent, not just behavior

- Tests must encode WHY behavior matters, not just WHAT it does.
- A test that can't fail when business logic changes is wrong.

## Rule 10 - Checkpoint after every significant step

- Summarize what was done, what's verified, what's left.
- Don't continue from a state you can't describe back.
- If you lose track, stop and restate.

## Rule 11 - Match the codebase's conventions, even if you disagree

- Conformance > taste inside the codebase
- If you genuinely think a convention is harmful, surface it. Don't fork silently.

## Rule 12 - Fail loud

- "Completed" is wrong if anything was skipped silently.
- "Tests pass" is wrong if any were skipped.
- Default to surfacing uncertainty, not hiding it.