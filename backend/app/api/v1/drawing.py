from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.parameter_extractor import validate_and_convert
from app.core.gcode_generator import generate_gcode
from app.core.gcode_validator import validate_gcode
from app.core.ocr_processor import ocr_recognize
from app.models.schemas import ConvertResponse, ConvertData, ProcessCard, Operation

router = APIRouter()

class DrawingRequest(BaseModel):
    image: str

class DrawingConvertRequest(BaseModel):
    process_card: ProcessCard
    operations: list

@router.post("/convert", response_model=ConvertResponse)
async def convert_drawing(request: DrawingConvertRequest):
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
            'operations': request.operations
        }
        
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

@router.post("/ocr-extract")
async def ocr_extract(request: DrawingRequest):
    try:
        extracted_data = ocr_recognize(request.image)
        
        return {
            "success": True,
            "message": "OCR识别成功",
            "data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr-convert", response_model=ConvertResponse)
async def ocr_convert(request: DrawingRequest):
    try:
        extracted_data = ocr_recognize(request.image)
        
        result, missing = validate_and_convert(extracted_data)
        
        if missing:
            return ConvertResponse(
                success=False,
                message="OCR识别完成，但参数不完整",
                missing_fields=missing,
                data=ConvertData(
                    process_card=None,
                    operations=[],
                    gcode="",
                    validation=None
                )
            )
        
        process_card, operations = result
        gcode = generate_gcode(process_card, operations)
        validation = validate_gcode(gcode)
        
        return ConvertResponse(
            success=True,
            message="OCR识别并转换成功",
            data=ConvertData(
                process_card=process_card,
                operations=operations,
                gcode=gcode,
                validation=validation
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
