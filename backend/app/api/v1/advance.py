import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import AdvanceResponse, ProcessCard

logger = logging.getLogger(__name__)

router = APIRouter()

class GenerateDrawingRequest(BaseModel):
    input_type: str
    input_data: str
    process_card: ProcessCard = None

@router.post("/generate-drawing", response_model=AdvanceResponse)
async def generate_drawing(request: GenerateDrawingRequest):
    try:
        drawings = []
        
        if request.process_card:
            operations = [
                {
                    'sequence': 1,
                    'content': '快速定位',
                    'parameters': 'X=0, Y=0, Z=50',
                    'equipment': 'CNC加工中心'
                },
                {
                    'sequence': 2,
                    'content': '加工操作',
                    'parameters': 'X=100, Y=100, Z=-5, F=120',
                    'equipment': request.process_card.tool_info.name if request.process_card.tool_info else ''
                },
                {
                    'sequence': 3,
                    'content': '返回安全高度',
                    'parameters': 'Z=50',
                    'equipment': 'CNC加工中心'
                }
            ]
            
            for idx, op in enumerate(operations, 1):
                try:
                    parts = op['parameters'].split(',')
                    x_val = parts[0].split('=')[1] if len(parts) > 0 and '=' in parts[0] else '0'
                    y_val = parts[1].split('=')[1] if len(parts) > 1 and '=' in parts[1] else '0'
                    z_val = parts[2].split('=')[1] if len(parts) > 2 and '=' in parts[2] else '0'
                except (IndexError, KeyError) as e:
                    print(f'[绘图生成] 工步{idx}参数解析失败: {e}，使用默认值')
                    x_val, y_val, z_val = '0', '0', '0'
                gcode_segment = f"G00 X{x_val} Y{y_val}\nG01 Z{z_val} F120"
                
                drawings.append({
                    'step': idx,
                    'drawing': f"data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iIzI1MjUyNSIvPjxyZWN0IHdpZHRoPSIxODAiIGhlaWdodD0iMTMwIiB4PSIxMCIgeT0iMTAiIGZpbGw9IiNmZmYiLz48c3Ryb2tlIHdpZHRoPSIyIiB4PSIxMCIgeT0iNzAiIHdpZHRoPSIxODAiIGZpbGw9IiMwMDAiLz48c3Ryb2tlIHdpZHRoPSIyIiB4PSIxMCIgeT0iMTAwIiB3aWR0aD0iMTgwIiBmaWxsPSIjMDAwIi8+PHBhdGggZD0iTTUwLDgwIDgxLjYsODAgODEuNiwxMDEuNiA1MCwxMDEuNiA1MCw4MFoiIGZpbGw9IiMwMDAiIHN0cm9rZT0iIzAwMCIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48cGF0aCBkPSJNMTMwLDgwIDE1MS42LDgwIDE1MS42LDEwMS42IDEzMCwxMDEuNiAxMzAsODBaIiBmaWxsPSIjMDAwIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMS41Ii8+PHRleHQgeD0iMTAwIiB5PSIyNSIgZm9udC1zaXplPSIyMCIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjMDAwIj5TdGVwLjE6IEFjdGlvbiBhdCBQYXRoPC90ZXh0Pjwvc3ZnPg==",
                    'gcode_segment': gcode_segment,
                    'operation_content': op['content']
                })
        
        return AdvanceResponse(
            success=True,
            data={
                'drawings': drawings
            }
        )
    except Exception as e:
        logger.exception("generate drawing failed: %s", e)
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')
