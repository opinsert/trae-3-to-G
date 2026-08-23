---
description: CNC 自然语言转换项目开发与验收工作流
globs: []
name: product-development-workflow
skill_type: user-invocable
trigger_words: []
---

# CNC 自然语言转换项目开发与验收工作流

本 Skill 定义了项目的标准工作流程、安全规则与验收标准。

## 核心工作流

### 1. 需求接收与澄清

- 用户提出需求时，先使用 `/brainstorming` 与用户确认功能边界与期望结果
- 明确输入、输出格式与交互流程
- 确认是否涉及多轮对话、文件上传或外部服务调用

### 2. 代码实现

- **后端**：在 `backend/app/` 下修改或新增模块
- **前端**：在 `frontend/src/` 下修改组件或页面
- 遵循项目现有代码风格与命名规范
- 新增或修改 API 时同步更新前端 `api/index.js`

### 3. 测试验证

- 后端修改：运行相关测试（如 `pytest backend/tests/test_*.py`）
- 前端修改：手动验证交互流程或使用 `/webapp-testing`
- G代码生成器与验证器修改：必须运行 `test_gcode_generator.py` 和 `test_gcode_validator.py`

### 4. 提交与 PR

- 使用 `/git-commit` 生成规范的提交信息
- 提交信息末尾添加 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`
- 推送到新分支并创建 PR（除非用户明确要求直接推送到 main）

## 安全规则（CNC 代码生成）

参见 `.claude/docs/cnc-safety-rules.md` 获取完整规则。核心约束：

- **坐标范围**：X/Y 0..200mm，Z 0..100mm（绝对坐标系）
- **冷却液**：切削前必须启动 M08
- **主轴检查**：切削前必须确认主轴已启动（M03/M04）
- **安全高度**：快速移动前必须提升到安全 Z 高度
- **进给与转速**：切削进给 ≤ 5000mm/min，主轴转速 ≤ 12000rpm
- **零步距检测**：连续相同坐标指令会触发警告

## 验收标准

参见 `.claude/docs/acceptance-checklist.md` 获取完整清单。关键检查项：

- [ ] 后端 API 返回正确的状态码与错误信息
- [ ] 前端正确处理加载、错误与成功状态
- [ ] G代码通过验证器安全检查（无 E001/E003/E005 错误）
- [ ] 坐标值在机床范围内（X/Y 0..200，Z 0..100）
- [ ] 多轮交互保持状态一致性（revision、digest 校验）
- [ ] 回归测试通过（`pytest backend/tests/ -q`）

## 常见场景

### 修改 G 代码生成器

1. 修改 `backend/app/core/gcode_generator.py`
2. 运行 `pytest backend/tests/test_gcode_generator.py -q`
3. 确认新生成的 G 代码通过 `test_gcode_validator.py` 检查

### 新增自然语言转换 API

1. 在 `backend/app/api/v1/natural_language.py` 添加端点
2. 更新 `backend/app/models/schemas.py` 定义请求/响应模型
3. 在 `frontend/src/api/index.js` 封装 API 调用
4. 更新相关前端组件（如 `NaturalLanguageInput.vue`）
5. 编写单元测试（`backend/tests/test_natural_language_api.py`）

### 修改机床配置

1. 更新 `backend/app/models/schemas.py` 中的 `MachineProfile` 默认值
2. 同步修改 `backend/app/core/gcode_validator.py` 的验证逻辑
3. 运行 `test_gcode_validator.py` 确认坐标范围检查正确
4. 更新 `.claude/docs/cnc-safety-rules.md` 文档

## 相关文档

- `.claude/docs/cnc-safety-rules.md` - CNC 代码生成安全规则
- `.claude/docs/acceptance-checklist.md` - 功能验收清单模板
- `.claude/skills/testing-gcode-validator/SKILL.md` - G 代码验证器测试指南
