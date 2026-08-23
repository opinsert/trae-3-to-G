from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Literal, Optional


class MachineProfile(BaseModel):
    name: str = Field("三轴加工中心（仿真）", description="机床配置名称")
    simulation_mode: bool = Field(True, description="是否为仿真配置")
    controller_family: str = Field("FANUC-compatible", description="控制器指令子集")
    length_unit: Literal["mm"] = Field("mm", description="长度单位")
    feed_mode: Literal["G94"] = Field("G94", description="进给模式，单位为mm/min")
    x_min: float = Field(0.0, description="工件坐标X下限(mm)")
    x_max: float = Field(200.0, description="工件坐标X上限(mm)")
    y_min: float = Field(0.0, description="工件坐标Y下限(mm)")
    y_max: float = Field(200.0, description="工件坐标Y上限(mm)")
    z_min: float = Field(-100.0, description="工件坐标Z下限(mm)")
    z_max: float = Field(100.0, description="工件坐标Z上限(mm)")
    safe_z: float = Field(5.0, description="安全高度(mm)")
    retract_z: float = Field(50.0, description="退刀高度(mm)")
    default_spindle_rpm: float = Field(3000.0, description="默认主轴转速(r/min)")
    max_spindle_rpm: float = Field(12000.0, description="最大主轴转速(r/min)")
    default_cutting_feed: float = Field(200.0, description="默认切削进给(mm/min)")
    default_plunge_feed: float = Field(100.0, description="默认下刀进给(mm/min)")
    default_positioning_feed: float = Field(500.0, description="默认定位进给(mm/min)")
    max_cutting_feed: float = Field(5000.0, description="最大切削进给(mm/min)")

    @model_validator(mode="after")
    def validate_ranges(self):
        for lower, upper, axis in (
            (self.x_min, self.x_max, "X"),
            (self.y_min, self.y_max, "Y"),
            (self.z_min, self.z_max, "Z"),
        ):
            if lower > upper:
                raise ValueError(f"{axis}轴下限不能大于上限")
        if not self.z_min <= self.safe_z <= self.z_max:
            raise ValueError("安全高度必须位于Z轴范围内")
        if not self.z_min <= self.retract_z <= self.z_max:
            raise ValueError("退刀高度必须位于Z轴范围内")
        return self


class ToolInfo(BaseModel):
    name: str = Field(..., description="刀具名称")
    length: float = Field(..., description="刀具长度")
    diameter: float = Field(..., description="刀具直径")


class DrawingStep(BaseModel):
    step: int = Field(..., description="工步号")
    step_content: str = Field(..., description="工步内容")
    parameters: Optional[str] = Field("", description="加工几何参数，长度单位为mm")
    tooling: Optional[str] = Field("", description="工艺装备")
    spindle_speed: Optional[float] = Field(None, description="主轴转速(r/min)")
    cutting_speed: Optional[float] = Field(None, description="切削速度(mm/min)")
    feed_rate: Optional[float] = Field(None, description="每转进给(mm/r)")
    feed_rate_mm_min: Optional[float] = Field(None, description="换算后的进给速度(mm/min)")
    depth_of_cut: Optional[float] = Field(None, description="每刀切深(mm)")
    feed_count: Optional[int] = Field(None, description="进给次数")
    machine_time: Optional[float] = Field(None, description="机动工时")
    auxiliary_time: Optional[float] = Field(None, description="辅助工时")
    remark: Optional[str] = Field("", description="备注")

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
    workshop: Optional[str] = Field("", description="车间")
    process_card_number: Optional[str] = Field("", description="工序号")
    material_grade: Optional[str] = Field("", description="材料牌号")
    blank_type: Optional[str] = Field("", description="毛坯种类")
    blank_size: Optional[str] = Field("", description="毛坯外形尺寸")
    blank_available_pieces: Optional[int] = Field(None, description="毛坯还可制件数")
    pieces_per_machine: Optional[int] = Field(None, description="每台件数")
    equipment_model: Optional[str] = Field("", description="设备型号")
    equipment_no: Optional[str] = Field("", description="设备编号")
    simultaneous_pieces: Optional[int] = Field(None, description="同时加工件数")
    fixture_no: Optional[str] = Field("", description="夹具编号")
    cutting_fluid: Optional[str] = Field("", description="切削液")
    station_tool_no: Optional[str] = Field("", description="工位器具编号")
    station_tool_name: Optional[str] = Field("", description="工位器具名称")
    preparation_time: Optional[float] = Field(None, description="准终工时")
    unit_time: Optional[float] = Field(None, description="单件工时")


class Operation(BaseModel):
    sequence: int = Field(..., description="序号")
    content: str = Field(..., description="操作内容")
    parameters: str = Field(..., description="工艺参数/要求")
    equipment: str = Field(..., description="设备/工具")
    remark: Optional[str] = Field("", description="备注")


class NaturalLanguageStatus(BaseModel):
    status: Literal["needs_input", "ready_for_confirmation", "generated", "blocked"]
    revision: int = Field(0, ge=0)
    digest: str = ""


class MissingField(BaseModel):
    path: str
    label: str
    scope: Literal["process_card", "operation", "machine"]
    code: str
    reason: str


class NaturalLanguageDraft(BaseModel):
    process_card: Dict[str, Any] = Field(default_factory=dict)
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    field_sources: Dict[str, Literal["user", "ai_suggested", "system_default"]] = Field(default_factory=dict)


class NaturalLanguagePrecheckRequest(BaseModel):
    message: str = ""
    draft: Optional[Dict[str, Any]] = None
    revision: int = Field(0, ge=0)
    digest: str = ""


class NaturalLanguagePrecheckResponse(BaseModel):
    success: bool = True
    status: Literal["needs_input", "ready_for_confirmation"]
    revision: int = Field(0, ge=0)
    digest: str = ""
    draft: NaturalLanguageDraft
    machine_profile: MachineProfile = Field(default_factory=MachineProfile)
    filled_fields: List[str] = Field(default_factory=list)
    missing_fields: List[MissingField] = Field(default_factory=list)
    unconfirmed_fields: List[str] = Field(default_factory=list)
    message: str = ""


class NaturalLanguageConfirmRequest(BaseModel):
    confirmed: bool = False
    draft: NaturalLanguageDraft
    revision: int = Field(..., ge=0)
    digest: str


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
    operations: List[Operation] = Field([], description="操作步骤")
    drawing_steps: List[DrawingStep] = Field([], description="工步步骤")
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
    machine_profile: MachineProfile = Field(default_factory=MachineProfile, description="机床仿真配置")


class NaturalLanguageConfirmResponse(BaseModel):
    success: bool
    status: Literal["generated", "blocked"]
    message: str
    data: Optional[ConvertData] = None
    errors: List[MissingField] = Field(default_factory=list)


class GCodeValidateResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: ValidationResult = Field(..., description="验证结果")

class ExampleItem(BaseModel):
    id: int = Field(..., description="示例ID")
    name: str = Field(..., description="示例名称")
    description: str = Field(..., description="示例描述")
    category: str = Field(..., description="示例分类")
    card_data: ProcessCard = Field(..., description="工序卡数据")
    operations_data: List[Operation] = Field([], description="操作步骤数据")
    drawing_steps_data: List[DrawingStep] = Field([], description="工步步骤数据")
    gcode: Optional[str] = Field("", description="参考G代码")

class ExampleListResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: List[ExampleItem] = Field(..., description="示例列表")

class AdvanceResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: dict = Field(..., description="返回数据")