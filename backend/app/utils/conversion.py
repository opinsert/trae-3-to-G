from app.core.parameter_extractor import validate_and_convert
from app.core.gcode_generator import generate_gcode
from app.core.gcode_validator import validate_gcode
from app.models.schemas import ConvertResponse, ConvertData, ProcessCard


def process_card_to_params(process_card: ProcessCard, operations: list = None) -> dict:
    return {
        'product_name': process_card.product_name or '',
        'process_name': process_card.process_name or '',
        'process_number': process_card.process_number or '',
        'version': process_card.version or '',
        'equipment': process_card.equipment or '',
        'control_system': process_card.control_system or '',
        'fixture': process_card.fixture or '',
        'material': process_card.material or '',
        'tool_name': process_card.tool_info.name if process_card.tool_info else '',
        'tool_length': process_card.tool_info.length if process_card.tool_info else 0,
        'tool_diameter': process_card.tool_info.diameter if process_card.tool_info else 0,
        'operations': operations or []
    }


def validate_params(params: dict, fail_message: str = "参数不完整") -> ConvertResponse:
    result, missing = validate_and_convert(params)
    if missing:
        return ConvertResponse(
            success=False,
            message=fail_message,
            missing_fields=missing
        )

    process_card, operations = result
    return ConvertResponse(
        success=True,
        message="工序生成成功",
        data=ConvertData(
            process_card=process_card,
            operations=operations,
            gcode='',
            validation=None
        )
    )


def convert_params_to_gcode(params: dict, fail_message: str = "参数不完整") -> ConvertResponse:
    result, missing = validate_and_convert(params)
    if missing:
        return ConvertResponse(
            success=False,
            message=fail_message,
            missing_fields=missing
        )

    process_card, operations = result
    gcode = generate_gcode(process_card, operations)
    validation = validate_gcode(gcode)

    return ConvertResponse(
        success=True,
        message="转换成功",
        data=ConvertData(
            process_card=process_card,
            operations=operations,
            gcode=gcode,
            validation=validation
        )
    )
