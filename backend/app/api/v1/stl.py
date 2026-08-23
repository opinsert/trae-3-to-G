import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models.schemas import ConvertResponse, ProcessCard
from app.utils.conversion import process_card_to_params, convert_params_to_gcode, validate_params
from app.core.stl_analyzer import analyze_stl, analyze_all_directions
from app.core.process_planner import plan_with_ai, plan_directions_with_ai

logger = logging.getLogger(__name__)

router = APIRouter()


class STLConvertRequest(BaseModel):
    stl_file: str
    process_card: ProcessCard
    generate_gcode: bool = False
    operations: list = Field(default_factory=list)
    direction: str = '+Z'


class DirectionPlanResponse(BaseModel):
    success: bool = True
    directions: dict = Field(default_factory=dict)
    recommended_order: list = Field(default_factory=list)
    skip_reasons: dict = Field(default_factory=dict)
    explanation: str = ''


@router.post("/convert", response_model=ConvertResponse)
async def convert_stl(request: STLConvertRequest):
    """Single-direction STL → G-code conversion."""
    try:
        ops = request.operations if request.operations else await generate_operations_from_stl(
            request.stl_file, request.process_card, request.direction
        )
        params = process_card_to_params(request.process_card, ops)

        if not request.generate_gcode:
            return validate_params(params)
        return convert_params_to_gcode(params)
    except ValueError as e:
        logger.warning("STL分析失败: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("STL convert failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')


@router.post("/plan-directions")
async def plan_directions(request: STLConvertRequest):
    """Analyze all 6 directions and return machining plan."""
    try:
        all_dirs = analyze_all_directions(request.stl_file)
        card_dict = _extract_card(request.process_card)
        tool_dia = _extract_tool_diameter(request.process_card)

        plan = await plan_directions_with_ai(all_dirs['directions'], card_dict, tool_dia)

        return {
            'success': True,
            'directions': all_dirs['directions'],
            'recommended_order': plan['recommended_order'],
            'skip_reasons': plan.get('skip_reasons', {}),
            'explanation': plan['explanation'],
            'source': plan['source'],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("方向规划失败: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')


async def generate_operations_from_stl(
    stl_base64: str, process_card: ProcessCard = None, direction: str = '+Z'
) -> list:
    """Analyze STL for one direction and generate operations."""
    geom = analyze_stl(stl_base64, direction)
    tool_dia = _extract_tool_diameter(process_card)
    card_dict = _extract_card(process_card)

    plan = await plan_with_ai(geom, card_dict, tool_dia)
    logger.info("工序生成: %d条 (%s) [%s]", len(plan['operations']), plan['source'], direction)
    return plan['operations']


def _extract_card(pc) -> dict:
    if pc is None:
        return {}
    return pc.model_dump() if hasattr(pc, 'model_dump') else (pc.dict() if hasattr(pc, 'dict') else {})


def _extract_tool_diameter(pc) -> float:
    if pc and pc.tool_info and pc.tool_info.diameter and pc.tool_info.diameter > 0:
        return float(pc.tool_info.diameter)
    raise ValueError("缺少刀具直径(mm)，无法生成STL刀路")
