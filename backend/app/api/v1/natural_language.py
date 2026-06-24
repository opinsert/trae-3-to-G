import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.parameter_extractor import extract_parameters, REQUIRED_FIELDS
from app.models.schemas import ConvertResponse
from app.utils.conversion import convert_params_to_gcode

logger = logging.getLogger(__name__)

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
        logger.exception("precheck failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

@router.post("/convert", response_model=ConvertResponse)
async def convert_natural_language(request: NaturalLanguageRequest):
    try:
        params = await extract_parameters(request.text)
        return convert_params_to_gcode(params)
    except Exception as e:
        logger.exception("conversion failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')
