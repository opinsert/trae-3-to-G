from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.schemas import ExampleListResponse
from app.core.example_manager import get_all_examples, get_example, get_examples_by_category

router = APIRouter()

@router.get("/", response_model=ExampleListResponse)
async def list_examples(category: Optional[str] = None):
    try:
        if category:
            examples = get_examples_by_category(category)
        else:
            examples = get_all_examples()
        return ExampleListResponse(
            success=True,
            data=examples
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{example_id}")
async def get_example_endpoint(example_id: int):
    try:
        example = get_example(example_id)
        if not example:
            raise HTTPException(status_code=404, detail="示例不存在")
        return {
            "success": True,
            "data": example
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    try:
        categories = ["铣削", "钻孔", "轮廓"]
        return {
            "success": True,
            "data": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
