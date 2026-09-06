# -*- coding: utf-8 -*-
"""真实 AI 模型冒烟测试 —— 验证 VISION_OCR_MODEL 在本项目三条链路中的真实工作表现。

⚠️  本脚本会调用 .env 中配置的真实外部 API（当前为 poke2api / kimi-k3），消耗配额。
    不会输出 API Key。

用法（在 backend 目录下运行）:
    python -m scripts.ai_smoke               # 跑全部场景
    python -m scripts.ai_smoke ping ocr nl   # 按需筛选子集（可选: ping ocr nl stl）

覆盖场景:
    ping     网关连通性(最小 chat，验证 key/base_url/model 与 JSON 返回)
    ocr      工序图视觉识别 (工序图.png / 工序图2.png / backend/test.jpg)
    stl      STL 单方向(+Z) AI 工艺规划
    stl-dirs STL 六方向加工顺序 AI 推荐

注：自然语言提取已改为纯脚本（不调 AI），不在本脚本覆盖范围。

退出码: 0=全部通过, 1=存在失败。单个场景失败不中断，逐场景汇总。
"""

import asyncio
import base64
import os
import sys
import time
import traceback
from pathlib import Path

# backend 目录（本文件所在目录的上级的上级 = backend）: scripts/../.. == backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
# 项目根目录（放 text_column.STL / 工序图.png）
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))

# 必须先于 app.* 导入加载 .env，否则 Settings() 拿不到密钥
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
except ImportError:  # pragma: no cover - 环境缺 python-dotenv 时兜底
    pass

from app.utils.ai_gateway import request_chat_completion_json  # noqa: E402
from app.core.ocr_processor import ocr_recognize  # noqa: E402
from app.core.stl_analyzer import analyze_all_directions, analyze_stl  # noqa: E402
from app.core.process_planner import plan_directions_with_ai, plan_with_ai  # noqa: E402
from app.utils.config import settings  # noqa: E402

CARD = {"material": "铝合金", "tool_name": "立铣刀"}
TOOL_DIA = 10.0

# 工序卡识别应包含的最少可验证字段（证明真在做结构化识别而非空回退）
OCR_MIN_FIELDS = ("process_name", "process_card_number", "material_grade")

STL_SAMPLES = {
    "工序图.png": PROJECT_ROOT / "工序图.png",
    "工序图2.png": PROJECT_ROOT / "工序图2.png",
    "test.jpg": BACKEND_DIR / "test.jpg",
}


def _data_uri(path: Path) -> str:
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        path.suffix.lstrip(".").lower(), "image/png"
    )
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _short(text, limit=200):
    text = str(text).replace("\n", " ")
    return text[:limit] + ("…" if len(text) > limit else "")


async def case_ping():
    start = time.time()
    result = await request_chat_completion_json(
        [{"role": "user", "content": "只回复一个合法 JSON 对象，不要解释，内容为 {\"ok\": true}"}],
        timeout=30,
    )
    return {
        "passed": result.get("ok") is True,
        "summary": f"chat 返回 {result}",
        "elapsed": time.time() - start,
    }


async def case_ocr(path: Path):
    start = time.time()
    result = await ocr_recognize(_data_uri(path))
    found = [f for f in OCR_MIN_FIELDS if result.get(f)]
    steps = result.get("drawing_steps") or []
    passed = bool(found) and len(steps) > 0
    summary = (
        f"识别字段={len(result)} | 关键字段{found} | 工步表{len(steps)}行 | "
        f"工序={result.get('process_name')!r} 材料={result.get('material_grade')!r}"
    )
    if steps:
        summary += f" 首工步={_short(steps[0].get('step_content', ''), 40)}"
    return {"passed": passed, "summary": summary, "elapsed": time.time() - start}


async def case_stl():
    """单方向工艺规划（+Z）"""
    start = time.time()
    stl_b64 = base64.b64encode((PROJECT_ROOT / "text_column.STL").read_bytes()).decode("ascii")
    geom = analyze_stl(stl_b64, "+Z")
    plan = await plan_with_ai(geom, CARD, TOOL_DIA)
    ops = plan.get("operations") or []
    passed = plan.get("source") == "ai" and len(ops) > 0
    summary = (
        f"来源={plan.get('source')} 工序{len(ops)}条 | "
        f"首工序={_short(ops[0].get('content', ''), 40) if ops else '无'}"
    )
    return {"passed": passed, "summary": summary, "elapsed": time.time() - start}


async def case_stl_directions():
    """六方向加工顺序推荐"""
    start = time.time()
    stl_b64 = base64.b64encode((PROJECT_ROOT / "text_column.STL").read_bytes()).decode("ascii")
    dirs = analyze_all_directions(stl_b64)["directions"]
    plan = await plan_directions_with_ai(dirs, CARD, TOOL_DIA)
    order = plan.get("recommended_order") or []
    passed = plan.get("source") == "ai" and len(order) > 0
    summary = (
        f"来源={plan.get('source')} 推荐顺序={order} 跳过理由={len(plan.get('skip_reasons') or {})}条 | "
        f"说明={_short(plan.get('explanation', ''), 60)}"
    )
    return {"passed": passed, "summary": summary, "elapsed": time.time() - start}


CASES = {
    "ping": case_ping,
    "ocr": [lambda p=p: case_ocr(p) for p in STL_SAMPLES.values()],
    "stl": case_stl,
    "stl-dirs": case_stl_directions,
}


async def run_selected(selected):
    results = []
    for name in selected:
        runners = CASES[name]
        if not isinstance(runners, list):
            runners = [runners]
        for index, runner in enumerate(runners):
            label = f"{name}" if len(runners) == 1 else f"{name}[{list(STL_SAMPLES)[index]}]"
            try:
                outcome = await runner()
                passed, summary = outcome["passed"], outcome["summary"]
            except Exception as exc:  # noqa: BLE001 - 冒烟脚本要求单场景失败不中断
                passed, summary = False, f"{type(exc).__name__}: {exc}"
                if settings.debug:
                    summary += " | " + traceback.format_exc(limit=1).strip().splitlines()[-1]
            results.append({"name": label, "passed": passed, "summary": summary})
            mark = "PASS" if passed else "FAIL"
            print(f"  [{mark}] {label}: {summary}")
    return results


def main():
    selected = sys.argv[1:] or list(CASES)
    unknown = [s for s in selected if s not in CASES]
    if unknown:
        print(f"未知场景: {unknown}（可选: {'/'.join(CASES)}）")
        sys.exit(2)
    print(f"模型: {settings.vision_ocr_model} | base_url: {settings.vision_ocr_base_url}")
    print(f"场景: {selected}\n")
    results = asyncio.run(run_selected(selected))
    failed = [r for r in results if not r["passed"]]
    print(f"\n汇总: {len(results) - len(failed)}/{len(results)} 通过")
    if failed:
        print("失败场景:")
        for r in failed:
            print(f"  - {r['name']}: {r['summary']}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
