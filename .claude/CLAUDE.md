# G代码转换系统项目规范

## 项目概述

本项目使用 Vue 3、Vite、Tailwind CSS 与 FastAPI，将自然语言、工序图图片和 STL 文件转换为 CNC 加工用 G 代码，并提供工艺信息、刀路预览和 G 代码安全验证。

主要代码位置：

- 后端 API：`backend/app/api/v1/`
- 核心模块：`backend/app/core/`
- 数据模型：`backend/app/models/schemas.py`
- 共享工具：`backend/app/utils/`
- 后端测试：`backend/tests/`
- 前端源码：`frontend/src/`
- 项目计划：`.claude/docs/gcode_converter_plan.md`
- 功能规格：`.claude/specs/`
- 项目技能：`.claude/skills/`

## 开发流程

### 需求分析

非平凡新功能开始前：

1. 搜索 GitHub、Gitee 等开源资源。
2. 向用户展示项目简介、活跃度、许可证等关键信息。
3. 等待用户选择自行开发、复用开源项目或混合方案。
4. 仅在用户确认后安装或集成第三方项目。

简单 Bug 修复、格式调整和文档更新可跳过该流程。

### 编码原则

1. 动手前说明要改什么，以及为什么不能直接复用现有实现。
2. 修改前读取调用方、被调方和共享工具；不确定时先询问。
3. 只改任务必需内容，不顺手重构无关代码。
4. 使用解决问题所需的最少代码，不为假设需求添加抽象。
5. 遇到冲突模式时选择更新且有测试依据的一种，并指出待清理项。
6. 遵循代码库现有约定；认为约定有害时先说明，不自行分叉。
7. 测试名称表达业务意图，测试应在业务规则改变时失败。
8. 出错、跳过或不确定时明确报告，不把部分完成称为完成。
9. 每个重要阶段说明已完成、已验证和剩余事项。

### Windows 命令

当前环境是 Windows。PowerShell 中使用分号连接命令，不使用 `&&`；文档中的运行命令优先给出 Windows 可执行形式。

## 修改后验证

每次修改后按影响范围执行：

- 后端测试：在 `backend` 下运行 `python -m pytest`。
- 后端启动：在 `backend` 下运行 `uvicorn app.main:app --host 0.0.0.0 --port 8000`。
- 前端构建：在 `frontend` 下运行 `npm run build`。
- 前端开发服务：在 `frontend` 下运行 `npm run dev`。
- 检查 API 密钥、密码等敏感信息未进入版本控制。
- 修改 GCode validator 或 `/api/v1/gcode/validate` 时使用 `.claude/skills/testing-gcode-validator/SKILL.md`。

核心链路验证项：

- 自然语言参数提取与 G 代码生成。
- 工序图 OCR、表单填充与 G 代码生成。
- STL 真实几何解析、六方向分析与工艺规划。
- G 代码语法和安全验证。
- 前后端 API 通信。

## Git 规范

仅在用户明确要求时提交。提交信息遵循 Conventional Commits：

- `feat`：新功能
- `fix`：错误修复
- `refactor`：不改变行为的重构
- `docs`：文档更新
- `style`：格式调整
- `test`：测试变更
- `chore`：依赖或配置等杂项

格式：

```text
<类型>(<范围>): <中文简短描述>

<可选详细说明>
```

禁止提交 API key、密码和本地 `.env`；测试图片、PDF、OCR 模型等大文件提交前须单独确认。
