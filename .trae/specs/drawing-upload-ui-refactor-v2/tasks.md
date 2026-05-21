# 工序图转换UI重构（V2）- Implementation Plan

## [ ] Task 1: 更新后端数据模型（schemas.py）
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 更新ProcessCard模型，新增字段：workshop, process_number_v2, material_grade, blank_type, blank_size, blank_count, parts_per_blank, equipment_model, equipment_number, simultaneous_parts, fixture_number, cutting_fluid, tool_number, tool_name, standard_time, unit_time
  - 更新DrawingStep模型，新增字段：spindle_speed, cutting_speed, feed_rate, depth_of_cut, feed_count, machine_time, auxiliary_time
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic`: 验证新增字段的数据类型和默认值
- **Notes**: 保持向后兼容，新增字段设为可选

## [ ] Task 2: 重构前端DrawingUpload.vue的UI布局
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 保持左栏图片上传区域不变
  - 将右栏重构为工序卡表格样式
  - 创建4行4列的基本信息表格
  - 创建工位器具和工时信息区域
  - 重新设计工步表格，包含所有必要的列
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `human-judgment`: 验证UI布局与工序图2.png一致
- **Notes**: 使用TailwindCSS保持响应式设计

## [ ] Task 3: 更新前端表单数据结构
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 更新form reactive对象，包含所有新增字段
  - 更新工步steps数据结构，包含所有新增的工步字段
  - 保持原有默认值和兼容性
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4
- **Test Requirements**:
  - `programmatic`: 验证表单数据结构完整

## [ ] Task 4: 更新OCR识别逻辑（ocr_processor.py）
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 更新OCR解析逻辑，提取所有新增字段
  - 更新工步数据解析，包含所有新增的工步参数
  - 保持表格识别功能
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic`: 验证OCR能识别和提取新增字段

## [ ] Task 5: 更新前端OCR数据填充逻辑
- **Priority**: P0
- **Depends On**: Task 3, Task 4
- **Description**: 
  - 更新extractFromImage函数，处理并填充所有新增字段
  - 更新工步数据的映射逻辑
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `programmatic`: 验证OCR数据能正确填充到表单

## [ ] Task 6: 更新后端API接口（drawing.py）
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 更新convert接口，接收新的数据结构
  - 保持向后兼容，确保G代码生成能正常工作
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `programmatic`: 验证API能正常接收和返回数据

## [ ] Task 7: 整体功能测试
- **Priority**: P1
- **Depends On**: Task 2, Task 3, Task 4, Task 5, Task 6
- **Description**: 
  - 测试完整的UI交互流程
  - 测试OCR识别功能
  - 测试G代码生成功能
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `human-judgment`: 验证整体功能正常
