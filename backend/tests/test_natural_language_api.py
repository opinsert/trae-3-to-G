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


def test_digest_is_immune_to_float_integer_drift():
    """浏览器 JSON.stringify(50.0) → '50' 使后端收到 int，digest 必须不受数字形态漂移影响。

    回归背景：digest 曾对 float 50.0 与 int 50 产生不同哈希，导致 confirm 恒 409。
    """
    from app.utils.conversion import natural_draft_digest

    def js_drift(obj):
        if isinstance(obj, float) and obj.is_integer():
            return int(obj)
        if isinstance(obj, dict):
            return {k: js_drift(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [js_drift(v) for v in obj]
        return obj

    draft = {
        "process_card": {"product_name": "底板", "tool_info": {"name": "键槽铣刀", "length": 50.0, "diameter": 6.0}},
        "operations": [{"sequence": 1, "content": "粗铣", "parameters": "X=0", "equipment": "刀1", "remark": ""}],
        "field_sources": {},
    }
    # 后端原生 draft 与浏览器往返漂移后的 draft 必须产生相同 digest
    assert natural_draft_digest(draft) == natural_draft_digest(js_drift(draft))


def test_ai_completion_fills_synonym_fields_script_cannot():
    """近义词表述（刀径/键槽刀）脚本识别不出时，AI 补全应填上缺失字段。"""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app.core.parameter_extractor import ParameterExtractor, natural_language_missing_fields
    from app.core.parameter_extractor import ai_complete_missing_fields

    text = "产品名称：底板\n工序名称：键槽加工\n用刀径10的键槽刀在中心铣个槽"
    base = ParameterExtractor().extract(text)
    assert "tool_diameter" in natural_language_missing_fields(base)  # 脚本确实识别不出

    ai_result = {"tool_name": "键槽铣刀", "tool_diameter": 10, "tool_length": 75}
    with patch("app.utils.ai_gateway.request_chat_completion_json",
               new=AsyncMock(return_value=ai_result)) as mocked:
        extra = asyncio.run(ai_complete_missing_fields(text, base))
    assert extra["tool_diameter"] == 10.0
    assert extra["tool_name"] == "键槽铣刀"
    assert mocked.await_args.kwargs["timeout"] == 60


def test_ai_completion_failure_keeps_script_result():
    """AI 补全失败不得影响主流程：返回空，保留脚本提取结果。"""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app.core.parameter_extractor import ParameterExtractor, ai_complete_missing_fields

    text = "产品名称：底板\n工序名称：键槽加工"
    base = ParameterExtractor().extract(text)
    with patch("app.utils.ai_gateway.request_chat_completion_json",
               new=AsyncMock(side_effect=RuntimeError("upstream down"))):
        extra = asyncio.run(ai_complete_missing_fields(text, base))
    assert extra == {}


def test_ai_completion_not_triggered_when_only_operations_missing():
    """缺整个 operations（工步）属于工艺设计，不应触发 AI 补全（防编造与无谓耗时）。"""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from app.core.parameter_extractor import ParameterExtractor, ai_complete_missing_fields, natural_language_missing_fields

    text = (
        "产品名称：底板\n工序名称：键槽加工\n工序编号：02\n版本号：A\n"
        "设备：立式加工中心\n数控系统：FANUC\n夹具：平口钳\n材料：铝合金\n"
        "刀具名称：键槽铣刀，长度：50mm，直径：8mm\n冷却方式：油冷\n铣个槽"
    )
    base = ParameterExtractor().extract(text)
    missing = natural_language_missing_fields(base)
    assert missing == ["operations"]  # 唯一缺项是整体工步
    with patch("app.utils.ai_gateway.request_chat_completion_json",
               new=AsyncMock(return_value={"operations": [{"sequence": 1, "content": "铣槽"}]})) as mocked:
        extra = asyncio.run(ai_complete_missing_fields(text, base))
    assert extra == {}
    mocked.assert_not_awaited()
