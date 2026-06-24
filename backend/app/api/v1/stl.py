import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import ConvertResponse, ProcessCard
from app.utils.conversion import process_card_to_params, convert_params_to_gcode, validate_params

logger = logging.getLogger(__name__)

router = APIRouter()

class STLConvertRequest(BaseModel):
    stl_file: str
    process_card: ProcessCard
    generate_gcode: bool = False
    operations: list = []

@router.post("/convert", response_model=ConvertResponse)
async def convert_stl(request: STLConvertRequest):
    try:
        ops = request.operations if request.operations else generate_operations_from_stl(request.stl_file)
        params = process_card_to_params(request.process_card, ops)

        if not request.generate_gcode:
            return validate_params(params)

        return convert_params_to_gcode(params)
    except Exception as e:
        logger.exception("STL convert failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

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
