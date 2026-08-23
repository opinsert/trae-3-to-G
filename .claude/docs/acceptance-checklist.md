# 功能验收清单模板

本清单用于验证 CNC 自然语言转换项目的功能实现是否满足安全与质量标准。

## 后端 API 验收

### 自然语言转换 API (`/api/v1/natural-language`)

- [ ] `/precheck` 接收不完整输入时返回 `status: "needs_input"` 和 `missing_fields`
- [ ] `/precheck` 接收完整输入时返回 `status: "ready_for_confirmation"` 和完整的 `draft`
- [ ] `/precheck` 多轮调用时正确合并 `draft`（保留旧值，覆盖新值）
- [ ] `/precheck` 返回的 `digest` 与 `draft` 内容一致（SHA256 哈希）
- [ ] `/confirm` 在 `digest` 不匹配时返回 409 错误
- [ ] `/confirm` 在工序卡不完整时返回 `status: "blocked"` 和 `errors`
- [ ] `/confirm` 成功时返回 `status: "generated"` 和完整的 `data`（含 G 代码）
- [ ] `/confirm` 生成的 G 代码通过验证器检查（`validation.valid = true`）
- [ ] `/convert` 端点返回 409 错误并提示使用新流程

### G 代码生成器 (`gcode_generator.py`)

- [ ] 生成的 G 代码包含必需的初始化指令（G90 G54 G21 G94）
- [ ] 切削前已启动主轴（M03）和冷却液（M08）
- [ ] 快速移动（G00）前已提升到安全高度（Z ≥ 50.0）
- [ ] 所有坐标值在机床范围内（X/Y 0..200，Z 0..100）
- [ ] 程序以 M30 结束并关闭主轴/冷却液
- [ ] 支持键槽加工工序（识别 X_END, Y_END 参数）
- [ ] 型腔加工工序正确生成（无重复定义）

### G 代码验证器 (`gcode_validator.py`)

- [ ] 检测坐标超限（E003）- X/Y/Z 超出 0..200/0..200/0..100
- [ ] 检测主轴未启动（E004）- 切削前无 M03/M04
- [ ] 检测冷却液未启动（E005）- 切削前无 M08
- [ ] 检测缺少单位/进给模式（E006）- 无 G21 或 G94
- [ ] 检测不安全快速移动（E007）- G00 时 Z < 5.0
- [ ] 检测进给速度超限（E009）- F > 5000
- [ ] 检测主轴转速超限（E010）- S > 12000
- [ ] 允许工件坐标系内的所有 Z 值（0..100）

## 前端交互验收

### 自然语言输入页面 (`NaturalLanguageInput.vue`)

- [ ] 用户输入不完整时显示"已识别字段"和"需要补充"
- [ ] 用户输入完整时弹出工序卡确认弹窗
- [ ] 工序卡弹窗显示所有工序卡字段和操作步骤
- [ ] 点击"返回补充"时关闭弹窗并允许继续输入
- [ ] 点击"确认并生成 G 代码"时调用 `/confirm` 并显示结果
- [ ] 生成成功时触发 `convert` 事件并传递完整数据
- [ ] 生成失败时显示错误信息
- [ ] 清空按钮正确清除所有状态（包括 sessionStorage）

### 工序卡确认弹窗 (`ProcessCardModal.vue`)

- [ ] 显示完整的工序卡基本信息（8 个字段）
- [ ] 显示刀具与冷却信息（4 个字段）
- [ ] 显示操作步骤表格（序号、操作内容、工艺参数、刀具、工艺说明）
- [ ] "返回补充"按钮触发 `back` 事件
- [ ] "确认并生成 G 代码"按钮触发 `confirm` 事件
- [ ] 生成中时按钮显示"生成中..."并禁用

### 高级页面 (`AdvanceView.vue`)

- [ ] 自然语言输入类型时显示提示：返回主页面使用工序卡补全流程
- [ ] STL 输入类型正常工作（不受影响）
- [ ] 不再调用 `/natural-language/convert`

## 数据一致性验收

### 多轮对话状态

- [ ] `revision` 每次 `/precheck` 调用后递增
- [ ] `digest` 与 `draft` 内容完全对应
- [ ] `draft` 保留上一轮所有已填字段
- [ ] `draft.operations` 正确合并（按 sequence 匹配）
- [ ] `draft.field_sources` 记录每个字段的来源（"user" 或其他）

### 工序参数提取

- [ ] 正确识别工序类型（钻孔、铣削、键槽等）
- [ ] 正确提取几何参数（X, Y, Z, X_END, Y_END, F 等）
- [ ] 正确提取刀具参数（name, length, diameter）
- [ ] 正确提取工艺参数（cutting_fluid, equipment 等）

## 安全验收

### G 代码安全

- [ ] Z 坐标在允许范围内（-100..100，负值用于切削）
- [ ] X/Y 坐标在允许范围内（0..200）
- [ ] 无超速指令（F ≤ 5000, S ≤ 12000）
- [ ] 切削前已启动主轴和冷却液
- [ ] 快速移动前已提升到安全高度

### 输入验证

- [ ] 空输入被拒绝（422 错误）
- [ ] 不完整工序卡无法确认生成
- [ ] digest 不匹配时拒绝确认（409 错误）
- [ ] 几何参数缺失时无法生成 G 代码

## 回归测试验收

- [ ] `pytest backend/tests/test_parameter_extractor.py -q` 全部通过
- [ ] `pytest backend/tests/test_gcode_generator.py -q` 全部通过
- [ ] `pytest backend/tests/test_gcode_validator.py -q` 全部通过
- [ ] `pytest backend/tests/test_natural_language_api.py -q` 全部通过
- [ ] `pytest backend/tests/test_schemas.py -q` 全部通过
- [ ] 前端构建无错误（`npm run build`）

## 文档验收

- [ ] `.claude/docs/cnc-safety-rules.md` 已更新并反映当前规则
- [ ] `.claude/skills/product-development-workflow/SKILL.md` 已创建并包含完整工作流
- [ ] 提交信息遵循 Conventional Commits 规范
- [ ] 提交信息包含 `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`

## 验收通过标准

- 所有"后端 API 验收"项通过
- 所有"前端交互验收"项通过
- 所有"安全验收"项通过
- 所有"回归测试验收"项通过
- 至少 90% 的"数据一致性验收"项通过

## 验收失败处理

如任一关键项（标记为"必需"）失败：

1. 记录失败原因与复现步骤
2. 修复代码并重新运行相关测试
3. 重新执行完整验收流程

如非关键项失败但不影响核心功能：

1. 创建 Issue 跟踪
2. 标记为"已知问题"
3. 在后续迭代中修复
