# 工序图转换UI重构（V2）- Verification Checklist

## 数据模型验证
- [ ] ProcessCard模型新增字段正确添加（workshop, process_number_v2, material_grade, blank_type, blank_size, blank_count, parts_per_blank, equipment_model, equipment_number, simultaneous_parts, fixture_number, cutting_fluid, tool_number, tool_name, standard_time, unit_time）
- [ ] DrawingStep模型新增字段正确添加（spindle_speed, cutting_speed, feed_rate, depth_of_cut, feed_count, machine_time, auxiliary_time）
- [ ] 所有新增字段设为可选（Optional），保持向后兼容

## 前端UI验证
- [ ] 左栏图片上传区域保持不变
- [ ] 右栏工序卡基本信息为4行4列表格样式
- [ ] 第1行包含：车间、工序号、工序名称、材料牌号
- [ ] 第2行包含：毛坯种类、毛坯外形尺寸、毛坯还可制件数、每台件数
- [ ] 第3行包含：设备名称、设备型号、设备编号、同时加工件数
- [ ] 第4行包含：夹具编号、夹具名称、切削液
- [ ] 工位器具和工时区域包含：工位器具编号、工位器具名称、工序工时（准终、单件）
- [ ] 工步表格包含所有必要列：工步号、工步内容、工艺装备、主轴转速(r/min)、切削速度(m/min)、进给量(mm/r)、被吃刀量(mm)、进给次数、工时/min（机动、辅助）
- [ ] UI布局与工序图2.png一致
- [ ] UI保持响应式设计

## 表单数据验证
- [ ] form reactive对象包含所有新增字段
- [ ] 工步steps数据结构包含所有新增字段
- [ ] 默认值设置合理

## OCR识别验证
- [ ] OCR能正确识别并提取所有新增字段
- [ ] 工步数据解析包含所有新增参数
- [ ] 前端能正确填充OCR识别的数据到表单

## API接口验证
- [ ] convert接口能正确接收新的数据结构
- [ ] G代码生成功能正常工作

## 整体功能验证
- [ ] 完整的UI交互流程正常
- [ ] OCR识别功能正常
- [ ] G代码生成功能正常
