from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.parameter_extractor import extract_parameters, validate_and_convert, REQUIRED_FIELDS
from app.core.gcode_generator import generate_gcode
from app.core.gcode_validator import validate_gcode
from app.models.schemas import ConvertResponse, ConvertData

router = APIRouter()

class NaturalLanguageRequest(BaseModel):
    text: str

class PrecheckResponse(BaseModel):
    success: bool = True
    extracted_parameters: dict = {}
    filled_fields: list = []
    missing_fields: list = []

@router.post("/precheck", response_model=PrecheckResponse)
async def precheck_natural_language(request: NaturalLanguageRequest):
    try:
        params = await extract_parameters(request.text)
        
        filled_fields = []
        missing_fields = []
        
        for field in REQUIRED_FIELDS:
            value = params.get(field, '')
            if value and str(value).strip() != '':
                filled_fields.append(field)
            else:
                missing_fields.append(field)
        
        return PrecheckResponse(
            success=True,
            extracted_parameters=params,
            filled_fields=filled_fields,
            missing_fields=missing_fields
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert", response_model=ConvertResponse)
async def convert_natural_language(request: NaturalLanguageRequest):
    try:
        print(f"收到转换请求: {request.text}")
        params = await extract_parameters(request.text)
        print(f"提取的参数: {params}")
        
        result, missing = validate_and_convert(params)
        if missing:
            print(f"参数不完整，缺失: {missing}")
            return ConvertResponse(
                success=False,
                message="参数不完整",
                missing_fields=missing
            )
        
        process_card, operations = result
        print(f"工序卡: {process_card}")
        print(f"操作步骤: {operations}")
        
        gcode = generate_gcode(process_card, operations)
        print(f"生成的G代码: {gcode}")
        
        validation = validate_gcode(gcode)
        print(f"验证结果: {validation}")
        
        return ConvertResponse(
            success=True,
            message="转换成功",
            data=ConvertData(
                process_card=process_card,
                operations=operations,
                gcode=gcode,
                validation=validation
            )
        )
    except Exception as e:
        print(f"转换异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))