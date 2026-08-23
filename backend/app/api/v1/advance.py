import base64
import html
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.stl import generate_operations_from_stl
from app.models.schemas import AdvanceResponse, ProcessCard

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateDrawingRequest(BaseModel):
    input_type: Literal['stl', 'natural']
    input_data: str
    process_card: ProcessCard = None


@router.post("/generate-drawing", response_model=AdvanceResponse)
async def generate_drawing(request: GenerateDrawingRequest):
    if request.input_type == 'natural':
        raise HTTPException(
            status_code=409,
            detail={
                'code': 'CONFIRMATION_REQUIRED',
                'message': '自然语言输入请使用主页面的工序卡补全和确认流程。',
            },
        )
    try:
        operations = await generate_operations_from_stl(request.input_data, request.process_card)
        drawings = [_make_drawing(step, operation) for step, operation in enumerate(operations, 1)]
        return AdvanceResponse(success=True, data={'drawings': drawings})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("generate drawing failed")
        raise HTTPException(status_code=500, detail='工序图生成失败，请稍后重试')


def _make_drawing(step: int, operation: dict) -> dict:
    content = html.escape(operation['content'])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="240" '
        'viewBox="0 0 400 240">'
        '<rect width="400" height="240" fill="#f8fafc"/>'
        '<rect x="20" y="20" width="360" height="200" fill="white" stroke="#334155"/>'
        '<path d="M50 160H350M80 160V80H320V160" fill="none" stroke="#2563eb" stroke-width="3"/>'
        f'<text x="200" y="50" text-anchor="middle" font-size="18" fill="#0f172a">工步{step}: {content}</text>'
        '</svg>'
    )
    return {
        'step': step,
        'drawing': 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode()).decode(),
        'gcode_segment': '',
        'operation_content': operation['content'],
        'parameters': operation.get('parameters', ''),
    }
