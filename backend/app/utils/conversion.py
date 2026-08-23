from hashlib import sha256
import json
from typing import Optional

from app.core.parameter_extractor import (
    ParameterExtractor,
    draft_to_params,
    merge_natural_language_draft,
    natural_language_missing_labels,
    natural_language_value_errors,
    normalize_draft,
    validate_and_convert,
)
from app.core.gcode_generator import generate_gcode, missing_operation_parameters
from app.core.gcode_validator import validate_gcode
from app.models.schemas import ConvertData, ConvertResponse, MachineProfile, ProcessCard, ValidationResult


DEFAULT_MACHINE_PROFILE = MachineProfile()


def natural_draft_digest(draft: dict) -> str:
    payload = json.dumps(draft, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def process_card_to_params(process_card: ProcessCard, operations: list = None) -> dict:
    return {
        "product_name": process_card.product_name or "",
        "process_name": process_card.process_name or "",
        "process_number": process_card.process_number or "",
        "version": process_card.version or "",
        "equipment": process_card.equipment or "",
        "control_system": process_card.control_system or "",
        "fixture": process_card.fixture or "",
        "material": process_card.material or "",
        "cutting_fluid": process_card.cutting_fluid or "",
        "tool_name": process_card.tool_info.name if process_card.tool_info else "",
        "tool_length": process_card.tool_info.length if process_card.tool_info else 0,
        "tool_diameter": process_card.tool_info.diameter if process_card.tool_info else 0,
        "operations": [
            operation.model_dump() if hasattr(operation, "model_dump") else operation
            for operation in (operations or [])
        ],
    }


def natural_language_precheck(params: dict) -> dict:
    draft = normalize_draft(params)
    missing = natural_language_missing_labels(params)
    errors = natural_language_value_errors(params)
    return {
        "status": "ready_for_confirmation" if not missing and not errors else "needs_input",
        "draft": draft,
        "digest": natural_draft_digest(draft),
        "missing_fields": [*missing, *errors],
        "filled_fields": [
            field for field in params
            if field not in {"operations", "field_sources"} and params.get(field) not in ("", None, 0)
        ],
        "unconfirmed_fields": [],
    }


def validate_params(params: dict, fail_message: str = "参数不完整") -> ConvertResponse:
    result, missing = validate_and_convert(params)
    if missing:
        return ConvertResponse(success=False, message=fail_message, missing_fields=missing)

    process_card, operations = result
    geometry_missing = missing_operation_parameters(operations)
    return ConvertResponse(
        success=not geometry_missing,
        message="工序参数完整" if not geometry_missing else "缺少生成刀路所需的几何参数",
        missing_fields=geometry_missing,
        data=ConvertData(
            process_card=process_card,
            operations=operations,
            gcode="",
            validation=ValidationResult(valid=False, errors=[], warnings=[]),
        ),
    )


def convert_params_to_gcode(params: dict, fail_message: str = "参数不完整") -> ConvertResponse:
    result, missing = validate_and_convert(params)
    if missing:
        return ConvertResponse(success=False, message=fail_message, missing_fields=missing)

    process_card, operations = result
    geometry_missing = missing_operation_parameters(operations)
    if geometry_missing:
        return ConvertResponse(
            success=False,
            message="缺少生成刀路所需的几何参数",
            missing_fields=geometry_missing,
        )

    gcode = generate_gcode(process_card, operations, DEFAULT_MACHINE_PROFILE)
    validation = validate_gcode(gcode, DEFAULT_MACHINE_PROFILE)
    return ConvertResponse(
        success=validation.valid,
        message="转换成功，等待人工审核" if validation.valid else "G代码安全验证未通过",
        data=ConvertData(
            process_card=process_card,
            operations=operations,
            gcode=gcode,
            validation=validation,
        ),
    )


def confirm_natural_language_draft(draft: dict) -> tuple[Optional[ConvertData], list]:
    params = draft_to_params(draft)
    missing = natural_language_missing_labels(params)
    errors = natural_language_value_errors(params)
    if missing or errors:
        return None, [*missing, *errors]

    result, conversion_missing = validate_and_convert(params, use_defaults=False)
    if conversion_missing:
        return None, [
            {
                "path": field,
                "label": field,
                "scope": "process_card",
                "code": "REQUIRED_FIELD",
                "reason": field,
            }
            for field in conversion_missing
        ]

    process_card, operations = result
    geometry_missing = missing_operation_parameters(operations)
    if geometry_missing:
        return None, [
            {
                "path": f"operations[{item.split(':', 1)[0].replace('工序', '')}]",
                "label": "工艺参数/要求",
                "scope": "operation",
                "code": "GEOMETRY_PARAMETER",
                "reason": item,
            }
            for item in geometry_missing
        ]

    gcode = generate_gcode(process_card, operations, DEFAULT_MACHINE_PROFILE)
    validation = validate_gcode(gcode, DEFAULT_MACHINE_PROFILE)
    data = ConvertData(
        process_card=process_card,
        operations=operations,
        drawing_steps=[],
        gcode=gcode,
        validation=validation,
    )
    return data, []


def merge_and_precheck(previous_draft: dict | None, message: str) -> dict:
    extracted = __import__("asyncio").run(ParameterExtractor().extract(message))
    previous = draft_to_params(previous_draft or {}) if previous_draft else {}
    params = merge_natural_language_draft(previous, extracted)
    params["field_sources"] = {
        **(previous.get("field_sources") or {}),
        **{field: "user" for field in extracted if field != "operations" and extracted.get(field) not in (None, "", 0)},
    }
    return params
