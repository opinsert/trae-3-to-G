"""
DeepSeek-powered machining process planner.

Takes STL geometry analysis (from stl_analyzer) + process card info,
calls DeepSeek to reason about feature types and optimal machining sequence,
then produces operations compatible with the GCodeGenerator.

Falls back to rule-based planner when DeepSeek is unavailable.
"""
import json
import logging
import traceback

import aiohttp

from app.utils.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


async def plan_directions_with_deepseek(
    all_dirs: dict, process_card: dict, tool_diameter: float = 10.0
) -> dict:
    """Analyze all 6 directions and recommend machining order via DeepSeek.

    Returns:
        {'recommended_order': ['+Z', '-Y', ...],
         'skip_reasons': {'-Z': '底面为平面无需加工', ...},
         'explanation': '...'}
    """
    if not settings.deepseek_api_key:
        return _fallback_direction_plan(all_dirs)

    try:
        return await _call_deepseek_directions(all_dirs, process_card, tool_diameter)
    except Exception as e:
        logger.warning("DeepSeek方向分析失败(%s)，回退本地规则", type(e).__name__)
        return _fallback_direction_plan(all_dirs)


async def plan_with_deepseek(geom: dict, process_card: dict,
                             tool_diameter: float = 10.0) -> dict:
    """Main entry point: plan machining operations using DeepSeek.

    Args:
        geom: Geometry analysis dict from stl_analyzer.analyze_stl().
        process_card: Process card dict with material, tool, etc.
        tool_diameter: Tool diameter in mm.

    Returns:
        {'operations': [...], 'explanation': '...', 'source': 'deepseek'|'fallback'}
    """
    if not settings.deepseek_api_key:
        logger.info("DeepSeek API key 未配置，使用本地规则规划")
        return _fallback_plan(geom, tool_diameter)

    try:
        return await _call_deepseek(geom, process_card, tool_diameter)
    except Exception as e:
        logger.warning("DeepSeek 规划失败 (%s)，回退本地规则", type(e).__name__)
        logger.debug("DeepSeek error traceback:\n%s", traceback.format_exc())
        return _fallback_plan(geom, tool_diameter)


# ---------------------------------------------------------------------------
# DeepSeek call
# ---------------------------------------------------------------------------

async def _call_deepseek(geom: dict, card: dict,
                         tool_dia: float) -> dict:
    prompt = _build_prompt(geom, card, tool_dia)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.deepseek_api_key}',
    }
    body = {
        'model': 'deepseek-chat',
        'messages': [
            {
                'role': 'system',
                'content': (
                    '你是一个资深的CNC机加工工艺师，精通铣削加工工艺规划。'
                    '请根据零件几何数据，制定合理的加工工序顺序。'
                    '回复必须是合法的JSON，不要包含任何额外说明文字。'
                    '【安全规则-不可违反】'
                    '1.禁止直插下刀:所有Z向下刀必须同时移动X/Y(斜坡进刀)'
                    '2.最大每刀切深3mm,超出必须分层'
                    '3.深腔体(深度>30mm或>宽度的50%)必须用型腔铣削策略:'
                    '  每层=斜坡进刀→清层→修壁,重复至底面'
                    '4.精加工壁面时必须考虑刀具半径补偿'
                ),
            },
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.1,
    }

    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=40)
    ) as session:
        async with session.post(
            settings.deepseek_api_url, headers=headers, json=body
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()

    try:
        content = result['choices'][0]['message']['content']
    except (KeyError, IndexError) as e:
        raise ValueError(f"DeepSeek 响应格式异常: {e}") from e

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1].rsplit('\n```', 1)[0]

    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("DeepSeek 返回非JSON，内容: %.200s", content)
        raise

    operations = plan.get('operations', [])
    if not operations:
        raise ValueError("DeepSeek 未返回有效工序")

    # re-number sequences
    for i, op in enumerate(operations, 1):
        op['sequence'] = i
        op.setdefault('equipment', '立铣刀')
        op.setdefault('remark', '')
        op.setdefault('parameters', '')

    logger.info(
        "DeepSeek 规划完成: %d条工序 | %s",
        len(operations), plan.get('process_summary', '')
    )
    return {
        'operations': operations,
        'explanation': plan.get('process_summary', ''),
        'source': 'deepseek',
    }


# ---------------------------------------------------------------------------
# direction-aware DeepSeek call
# ---------------------------------------------------------------------------

async def _call_deepseek_directions(
    all_dirs: dict, card: dict, tool_dia: float
) -> dict:
    prompt = _build_direction_prompt(all_dirs, card, tool_dia)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.deepseek_api_key}',
    }
    body = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': '你是CNC工艺师。只输出JSON。'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.1,
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=40)) as s:
        async with s.post(settings.deepseek_api_url, headers=headers, json=body) as r:
            r.raise_for_status()
            result = await r.json()

    content = result['choices'][0]['message']['content'].strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1].rsplit('\n```', 1)[0]
    plan = json.loads(content)
    logger.info("DeepSeek方向推荐: %s", plan.get('recommended_order', []))
    return {
        'recommended_order': plan.get('recommended_order', list(all_dirs.keys())),
        'skip_reasons': plan.get('skip_reasons', {}),
        'explanation': plan.get('explanation', ''),
        'source': 'deepseek',
    }


def _build_direction_prompt(all_dirs: dict, card: dict, tool_dia: float) -> str:
    dir_lines = []
    for name in ['+Z', '-Z', '+X', '-X', '+Y', '-Y']:
        if name not in all_dirs:
            continue
        d = all_dirs[name]
        shape = d.get('shape_profile', {})
        dir_lines.append(
            f"  {d.get('label', name)}: {d['width']:.1f}×{d['height']:.1f}×{d['depth']:.1f}mm,"
            f" {'深腔体' if shape.get('is_deep_pocket') else '浅平面' if shape.get('is_flat') else '块状'},"
            f" 截面面积范围: {d.get('cross_sections', [{}])[0].get('cross_section_area', '?') if d.get('cross_sections') else '?'}"
            f"~{d.get('cross_sections', [{}])[-1].get('cross_section_area', '?') if d.get('cross_sections') else '?'}"
        )

    return f"""零件从6个方向看的几何数据如下。每个方向代表把该面朝上(Z+)装夹后加工。
请分析哪些方向需要加工、推荐加工顺序。

材料: {card.get('material', '铝合金')}, 刀具直径: {tool_dia:.1f}mm
安全约束: 最大切深3mm/刀, 禁止直插, 型腔需分层

【六方向几何数据】
{chr(10).join(dir_lines)}

输出JSON:
{{
  "recommended_order": ["+Z", "-Y", ...],
  "skip_reasons": {{"-Z": "底面为平面无需加工"}},
  "explanation": "简要说明加工策略"
}}

注意:
- 截面面积≈0的方向无需加工(那是实心底面)
- 优先加工面积大、深度大的面
- 简单零件可能只需1-2个方向
- recommended_order只用需要的方向"""


def _fallback_direction_plan(all_dirs: dict) -> dict:
    needed = list(all_dirs.keys())
    return {
        'recommended_order': needed,
        'skip_reasons': {},
        'explanation': '本地规则: 按默认顺序加工所有方向',
        'source': 'fallback',
    }


# ---------------------------------------------------------------------------
# prompt building
# ---------------------------------------------------------------------------

def _build_prompt(geom: dict, card: dict, tool_dia: float) -> str:
    w, h, d = geom['width'], geom['height'], geom['depth']
    material = card.get('material', '未知')
    tool_name = card.get('tool_name', '立铣刀')

    # cross-section summary
    sec_lines = []
    for s in geom.get('cross_sections', []):
        sec_lines.append(f"  Z={s['z']:.1f}mm → 截面面积 ≈ {s['cross_section_area']:.1f}mm²")

    # boundary loops summary
    loop_lines = []
    for lp in geom.get('boundary_loops', []):
        loop_lines.append(
            f"  中心({lp['center_x']:.1f},{lp['center_y']:.1f}) "
            f"≈Φ{lp['approx_diameter']:.1f}mm ({lp['vertex_count']}顶点)"
        )

    face_dist = geom.get('face_distribution', {})
    shape = geom.get('shape_profile', {})

    return f"""请根据以下零件几何分析数据，制定合理的CNC铣削加工工序。

【零件基本信息】
- 外形尺寸：{w:.1f} × {h:.1f} × {d:.1f} mm
- 材料：{material}
- 刀具：{tool_name}（直径{tool_dia:.1f}mm）
- 形状特征：{"薄板件" if shape.get('is_flat') else "块状件"}，
  长宽比 {shape.get('aspect_ratio', 1):.1f}

【网格统计】
- 面片数：{geom['vertex_count']:,} 顶点，{geom['face_count']:,} 三角面
- 表面积：{geom['surface_area']:.1f} mm²
- 水密性：{'是' if geom.get('is_watertight') else '否'}
- 体积：{geom['volume']:.1f} mm³

【面法向分布】
- 顶/底面占比：{face_dist.get('top_pct', 0):.0f}%（接近水平的三角面）
- 侧面占比：{face_dist.get('side_pct', 0):.0f}%（接近垂直的面）
- 斜面占比：{face_dist.get('angled_pct', 0):.0f}%（倾斜面）

【截面分析（从底部到顶部）】
{chr(10).join(sec_lines) if sec_lines else '  （无截面数据）'}

【边界环检测（可能是孔/槽/腔体）】
{chr(10).join(loop_lines) if loop_lines else '  （未检测到明显孔洞特征）'}

【加工要求】
- 每刀最大切深 3mm，精加工余量 0
- 粗加工进给 F=300，精加工进给 F=120
- 禁止直插：必须先走斜坡进刀
- 深腔体(深度>30mm)：必须用型腔策略分层加工

【工序content关键词（必须从下列选择，否则G代码生成器无法识别）】
- "斜坡进刀-Z{深度}" — 每层开始的斜坡进刀
- "型腔粗加工-第{N}层" — 腔体分层清层
- "侧壁精修-Z{深度}" — 壁面精修
- "底面精加工" — 最后底面光刀
- "粗加工-平面铣削" — 平板面铣
- "精加工-轮廓铣削" — 轮廓精加工
- "返回安全高度" — 回退

【输出格式】
请严格按照以下JSON格式输出（只输出JSON，不要加markdown代码块标记）：

{{
  "feature_analysis": "对零件几何特征的分析",
  "process_summary": "加工工艺简述",
  "operations": [
    {{
      "content": "斜坡进刀-Z3.0 或 型腔粗加工-第1层 或 侧壁精修-Z3.0 或 底面精加工 或 粗加工-平面铣削 或 精加工-轮廓铣削 或 返回安全高度",
      "parameters": "参数键值对",
      "equipment": "刀具或设备"
    }}
  ]
}}

注意：
1. content必须使用上述关键词之一，使G代码生成器能正确识别
2. 面铣参数: X=0, Y=0, X_END={宽}, Y_END={高}, Z={深度}, F={进给}, STEP={步距}
3. 型腔参数: X=0, Y=0, X_END={宽}, Y_END={高}, Z={深度}, F=300, STEP={步距}
4. 侧壁参数: X=0, Y=0, WIDTH={宽}, HEIGHT={高}, Z={深度}, F=120
5. 斜坡进刀: RAMP_X=5, RAMP_Y=5, Z={深度}, F=200
6. 先粗后精，先面后孔，所有尺寸mm"""
    return prompt


# ---------------------------------------------------------------------------
# fallback (same as stl_analyzer.plan_operations)
# ---------------------------------------------------------------------------

def _fallback_plan(geom: dict, tool_dia: float) -> dict:
    from app.core.stl_analyzer import plan_operations
    return {
        'operations': plan_operations(geom, tool_dia),
        'explanation': '使用本地规则生成（未配置DeepSeek API key或API调用失败）',
        'source': 'fallback',
    }
