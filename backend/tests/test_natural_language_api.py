import pytest
from unittest.mock import AsyncMock, patch

from app.core.parameter_extractor import ParameterExtractor, merge_natural_language_draft
from app.models.schemas import NaturalLanguagePrecheckRequest
from app.api.v1.natural_language import precheck_natural_language


COMPLETE_TEXT = """产品名称：底板
工序名称：键槽加工
工序编号：02
版本号：A
设备：立式加工中心
数控系统：FANUC-0iM
夹具：平口钳装夹
材料：铝合金6061
刀具名称：键槽铣刀
刀具长度：50mm
刀具直径：8mm
冷却方式：油冷
1. 粗铣键槽 刀具：键槽铣刀 X=0, Y=0, X_END=40, Y_END=10, Z=2, F=200 工艺说明：每层切深2mm
"""


@pytest.mark.asyncio
async def test_incomplete_process_card_returns_missing_fields_without_gcode():
    response = await precheck_natural_language(NaturalLanguagePrecheckRequest(message="产品名称：底板"))
    assert response.status == "needs_input"
    assert response.missing_fields
    assert all(field.path != "gcode" for field in response.missing_fields)


@pytest.mark.asyncio
async def test_complete_process_card_waits_for_confirmation():
    response = await precheck_natural_language(NaturalLanguagePrecheckRequest(message=COMPLETE_TEXT))
    assert response.status == "ready_for_confirmation"
    assert response.draft.process_card["product_name"] == "底板"
    assert response.draft.process_card["cutting_fluid"] == "油冷"


def test_incremental_draft_keeps_previous_fields_and_merges_steps():
    previous = {
        "product_name": "底板",
        "operations": [{"sequence": 1, "content": "粗铣", "parameters": "X=0", "equipment": "刀1", "remark": ""}],
    }
    incoming = {
        "material": "铝合金6061",
        "operations": [{"sequence": 1, "parameters": "X=0, Y=0", "remark": "单层加工"}],
    }
    merged = merge_natural_language_draft(previous, incoming)
    assert merged["product_name"] == "底板"
    assert merged["material"] == "铝合金6061"
    assert merged["operations"][0]["content"] == "粗铣"
    assert merged["operations"][0]["parameters"] == "X=0, Y=0"
