from pydantic import BaseModel, Field
from typing import List, Optional

class ToolInfo(BaseModel):
    name: str = Field(..., description="刀具名称")
    length: float = Field(..., description="刀具长度")
    diameter: float = Field(..., description="刀具直径")

class ProcessCard(BaseModel):
    product_name: str = Field(..., description="产品名称")
    process_name: str = Field(..., description="工序名称")
    process_number: str = Field(..., description="工序编号")
    version: str = Field(..., description="版本号")
    equipment: str = Field(..., description="设备名称")
    control_system: str = Field(..., description="数控系统")
    fixture: str = Field(..., description="夹具名称")
    material: str = Field(..., description="材料名称")
    tool_info: ToolInfo = Field(..., description="刀具信息")

class Operation(BaseModel):
    sequence: int = Field(..., description="序号")
    content: str = Field(..., description="操作内容")
    parameters: str = Field(..., description="工艺参数/要求")
    equipment: str = Field(..., description="设备/工具")
    remark: Optional[str] = Field("", description="备注")

class ValidationError(BaseModel):
    line: int = Field(..., description="行号")
    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误信息")
    suggestion: Optional[str] = Field("", description="建议")

class ValidationWarning(BaseModel):
    line: int = Field(..., description="行号")
    message: str = Field(..., description="警告信息")

class ValidationResult(BaseModel):
    valid: bool = Field(..., description="是否通过验证")
    errors: List[ValidationError] = Field([], description="错误列表")
    warnings: List[ValidationWarning] = Field([], description="警告列表")

class ConvertResult(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    missing_fields: Optional[List[str]] = Field([], description="缺失的字段")

class ConvertData(BaseModel):
    process_card: ProcessCard = Field(..., description="工序卡信息")
    operations: List[Operation] = Field(..., description="操作步骤")
    gcode: str = Field(..., description="生成的G代码")
    validation: ValidationResult = Field(..., description="验证结果")

class ConvertResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    data: Optional[ConvertData] = Field(None, description="转换数据")
    missing_fields: Optional[List[str]] = Field([], description="缺失的字段")

class GCodeValidateRequest(BaseModel):
    gcode: str = Field(..., description="G代码内容")
    process_card: Optional[ProcessCard] = Field(None, description="工序卡信息")

class GCodeValidateResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: ValidationResult = Field(..., description="验证结果")

class ExampleItem(BaseModel):
    id: int = Field(..., description="示例ID")
    name: str = Field(..., description="示例名称")
    description: str = Field(..., description="示例描述")
    category: str = Field(..., description="示例分类")
    card_data: ProcessCard = Field(..., description="工序卡数据")
    operations_data: List[Operation] = Field(..., description="操作步骤数据")
    gcode: Optional[str] = Field("", description="参考G代码")

class ExampleListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: List[ExampleItem] = Field(..., description="示例列表")

class DrawingStep(BaseModel):
    step: int = Field(..., description="步骤序号")
    drawing: str = Field(..., description="工序图(base64)")
    gcode_segment: str = Field(..., description="对应的G代码片段")
    operation_content: str = Field(..., description="操作内容")

class AdvanceResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: dict = Field(..., description="返回数据")
