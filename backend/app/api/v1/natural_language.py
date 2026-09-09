import hashlib
import logging

from fastapi import APIRouter, HTTPException, status

from app.core.parameter_extractor import (
    ai_extract_full_card_extra,
    draft_to_params,
    extract_parameters,
    infer_slot_geometry,
    merge_natural_language_draft,
)
from app.models.schemas import (
    NaturalLanguageConfirmRequest,
    NaturalLanguageConfirmResponse,
    NaturalLanguageDraft,
    NaturalLanguagePrecheckRequest,
    NaturalLanguagePrecheckResponse,
)
from app.utils.conversion import (
    confirm_natural_language_draft,
    natural_draft_digest,
    natural_language_precheck,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/precheck", response_model=NaturalLanguagePrecheckResponse)
async def precheck_natural_language(request: NaturalLanguagePrecheckRequest):
    if not request.message.strip() and not request.draft:
        raise HTTPException(status_code=422, detail="本轮补充内容不能为空")

    try:
        extracted = extract_parameters(request.message)
        previous = draft_to_params(request.draft or {})
        params = merge_natural_language_draft(previous, extracted)
        # 表格/文本给出了键槽与毛坯尺寸但没有坐标时，自动推算居中键槽的刀路坐标
        infer_slot_geometry(request.message, params)
        params["field_sources"] = {
            **(previous.get("field_sources") or {}),
            **{
                field: "user"
                for field, value in extracted.items()
                if field != "operations" and value not in (None, "", 0)
            },
        }
        # 三段式：脚本已抽 → AI 整卡解读补足缺失（仅文本含加工动作时允许补工步文字）→ 规则复核
        # AI 网关未配置/失败时返回 {}，保持纯脚本结果（毫秒级路径不受影响）。
        ai_extra = await ai_extract_full_card_extra(request.message, params)
        if ai_extra:
            params = merge_natural_language_draft(params, ai_extra)
            infer_slot_geometry(request.message, params)

        result = natural_language_precheck(params)
        revision = request.revision + 1
        draft = NaturalLanguageDraft.model_validate(result["draft"])
        return NaturalLanguagePrecheckResponse(
            status=result["status"],
            revision=revision,
            digest=result["digest"],
            draft=draft,
            filled_fields=result["filled_fields"],
            missing_fields=result["missing_fields"],
            unconfirmed_fields=result["unconfirmed_fields"],
            message=(
                "工序卡已完整，请核对后确认生成G代码"
                if result["status"] == "ready_for_confirmation"
                else "请补充页面列出的缺失信息"
            ),
        )
    except Exception:
        logger.exception("natural language precheck failed")
        raise HTTPException(status_code=500, detail="工序卡信息检查失败，请稍后重试")


@router.post("/confirm", response_model=NaturalLanguageConfirmResponse)
async def confirm_natural_language(request: NaturalLanguageConfirmRequest):
    if not request.confirmed:
        raise HTTPException(status_code=422, detail="必须明确确认工序卡后才能生成G代码")

    actual_digest = natural_draft_digest(request.draft.model_dump())
    if actual_digest != request.digest:
        logger.warning(
            "confirm digest 不匹配: 请求digest=%s... 实算=%s... revision=%s 工步数=%s",
            request.digest[:16], actual_digest[:16], request.revision, len(request.draft.operations or []),
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="工序卡已发生变化，请重新检查后确认")

    try:
        data, errors = confirm_natural_language_draft(request.draft.model_dump())
        if errors:
            return NaturalLanguageConfirmResponse(
                success=False,
                status="blocked",
                message="工序卡仍不能安全生成G代码",
                errors=errors,
            )
        if not data.validation.valid:
            return NaturalLanguageConfirmResponse(
                success=False,
                status="blocked",
                message="G代码安全验证未通过",
                errors=[
                    {
                        "path": "gcode",
                        "label": error.code,
                        "scope": "machine",
                        "code": error.code,
                        "reason": error.message,
                    }
                    for error in data.validation.errors
                ],
            )
        return NaturalLanguageConfirmResponse(
            success=True,
            status="generated",
            message="转换成功，等待人工审核",
            data=data,
        )
    except Exception:
        logger.exception("natural language confirmation failed")
        raise HTTPException(status_code=500, detail="G代码生成失败，请稍后重试")


@router.post("/convert", status_code=status.HTTP_409_CONFLICT)
async def convert_natural_language():
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "CONFIRMATION_REQUIRED",
            "message": "请先调用/precheck完成工序卡检查，再调用/confirm确认生成G代码",
        },
    )
