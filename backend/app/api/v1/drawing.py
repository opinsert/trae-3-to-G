import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ocr_processor import ocr_recognize
from app.models.schemas import ConvertResponse, DrawingStep, ProcessCard
from app.utils.conversion import process_card_to_params, convert_params_to_gcode

logger = logging.getLogger(__name__)

router = APIRouter()

class DrawingRequest(BaseModel):
    image: str

class DrawingConvertRequest(BaseModel):
    process_card: ProcessCard
    steps: list[DrawingStep]

@router.post("/convert", response_model=ConvertResponse)
async def convert_drawing(request: DrawingConvertRequest):
    try:
        params = process_card_to_params(request.process_card, request.steps)
        return convert_params_to_gcode(params)
    except Exception as e:
        logger.exception("drawing convert failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

@router.post("/ocr-extract")
async def ocr_extract(request: DrawingRequest):
    try:
        extracted_data = await ocr_recognize(request.image)
        
        return {
            "success": True,
            "message": "OCR识别成功",
            "data": extracted_data
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("OCR extract failed: %s", e)
        raise HTTPException(status_code=502, detail=f'视觉 OCR 请求失败: {type(e).__name__}: {e}')

@router.post("/ocr-convert", response_model=ConvertResponse)
async def ocr_convert(request: DrawingRequest):
    try:
        extracted_data = await ocr_recognize(request.image)
        return convert_params_to_gcode(extracted_data, fail_message="OCR识别完成，但参数不完整")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("OCR convert failed: %s", e)
        raise HTTPException(status_code=502, detail=f'视觉 OCR 请求失败: {type(e).__name__}: {e}')
