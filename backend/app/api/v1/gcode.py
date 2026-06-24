import logging

from fastapi import APIRouter, HTTPException
from app.models.schemas import GCodeValidateRequest, GCodeValidateResponse
from app.core.gcode_validator import validate_gcode

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/validate", response_model=GCodeValidateResponse)
async def validate_gcode_endpoint(request: GCodeValidateRequest):
    try:
        validation = validate_gcode(request.gcode)
        return GCodeValidateResponse(
            success=True,
            data=validation
        )
    except Exception as e:
        logger.exception("gcode validation failed")
        raise HTTPException(status_code=500, detail="G代码验证失败，请稍后重试")
