import pytest

from app.api.v1.stl import _extract_tool_diameter
from app.models.schemas import ProcessCard, ToolInfo


def make_process_card(diameter):
    return ProcessCard(
        product_name="测试STL",
        process_name="STL加工",
        process_number="001",
        version="A",
        equipment="三轴加工中心（仿真）",
        control_system="FANUC-compatible",
        fixture="通用夹具（仿真）",
        material="未指定材料（仿真）",
        tool_info=ToolInfo(name="立铣刀", length=75, diameter=diameter),
    )


def test_stl_tool_diameter_is_required_because_it_changes_toolpath():
    with pytest.raises(ValueError, match="缺少刀具直径"):
        _extract_tool_diameter(make_process_card(0))


def test_stl_tool_diameter_uses_user_value_when_present():
    assert _extract_tool_diameter(make_process_card(8)) == 8
