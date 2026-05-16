from fastapi import APIRouter, HTTPException
from app.models.schemas import GCodeValidateRequest, GCodeValidateResponse
from app.core.gcode_validator import validate_gcode

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
        raise HTTPException(status_code=500, detail=str(e))
