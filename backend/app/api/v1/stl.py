from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.parameter_extractor import validate_and_convert
from app.core.gcode_generator import generate_gcode
from app.core.gcode_validator import validate_gcode
from app.models.schemas import ConvertResponse, ConvertData, ProcessCard

router = APIRouter()

class STLConvertRequest(BaseModel):
    stl_file: str
    process_card: ProcessCard

@router.post("/convert", response_model=ConvertResponse)
async def convert_stl(request: STLConvertRequest):
    try:
        params = {
            'product_name': request.process_card.product_name,
            'process_name': request.process_card.process_name,
            'process_number': request.process_card.process_number,
            'version': request.process_card.version,
            'equipment': request.process_card.equipment,
            'control_system': request.process_card.control_system,
            'fixture': request.process_card.fixture,
            'material': request.process_card.material,
            'tool_name': request.process_card.tool_info.name,
            'tool_length': request.process_card.tool_info.length,
            'tool_diameter': request.process_card.tool_info.diameter,
            'operations': []
        }
        
        operations = generate_operations_from_stl(request.stl_file)
        params['operations'] = operations
        
        result, missing = validate_and_convert(params)
        if missing:
            return ConvertResponse(
                success=False,
                message="参数不完整",
                missing_fields=missing
            )
        
        process_card, operations = result
        gcode = generate_gcode(process_card, operations)
        validation = validate_gcode(gcode)
        
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
        raise HTTPException(status_code=500, detail=str(e))

def generate_operations_from_stl(stl_base64: str) -> list:
    operations = [
        {
            'sequence': 1,
            'content': '快速定位到加工起点',
            'parameters': 'X=0, Y=0, Z=50',
            'equipment': 'CNC加工中心',
            'remark': ''
        },
        {
            'sequence': 2,
            'content': 'STL模型加工',
            'parameters': 'X=100, Y=100, Z=-5, F=120',
            'equipment': '立铣刀',
            'remark': '根据STL模型生成的加工路径'
        },
        {
            'sequence': 3,
            'content': '返回安全高度',
            'parameters': 'Z=50',
            'equipment': 'CNC加工中心',
            'remark': ''
        }
    ]
    return operations
