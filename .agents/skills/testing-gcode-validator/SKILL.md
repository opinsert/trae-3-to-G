---
name: testing-gcode-validator
description: Test the GCode validator logic and safety checks end-to-end. Use when verifying changes to backend/app/core/gcode_validator.py or the /api/v1/gcode/validate endpoint.
---

# Testing GCode Validator

## Overview
The GCode validator (`backend/app/core/gcode_validator.py`) performs syntax, logic, and safety checks on CNC G-code programs. It is exposed via `POST /api/v1/gcode/validate`.

## Prerequisites
- Python dependencies installed: `pip install fastapi uvicorn pydantic pydantic-settings pytest`
- Working directory: `backend/`

## Running Unit Tests
```bash
cd backend
python -m pytest tests/test_gcode_validator.py -v
```
All 21+ tests should pass. Tests cover:
- Valid programs (no false positives)
- E005: cutting before spindle start
- Safe Z height warnings
- G91 incremental overtravel accumulation
- G00 rapid plunge to negative Z
- Code after M30/M02
- Feed rate validation
- Backward compatibility (E001, E003)

## Running API E2E Tests
Start the backend:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Note: The OCR module (`baidu-aip`) may show a warning but doesn't block the server.

Test the validate endpoint:
```bash
curl -s -X POST http://localhost:8000/api/v1/gcode/validate \
  -H "Content-Type: application/json" \
  -d '{"gcode": "G90 G54\nM03 S3000\nG00 X10.0 Y10.0 Z50.0\nG01 Z5.0 F500\nM05\nM30"}'
```

## Key Validation Scenarios to Test

| Scenario | Input Pattern | Expected |
|----------|--------------|----------|
| Valid program | Full init+cut+end sequence | `valid: true`, no errors |
| Missing spindle | G01 without prior M03/M04 | E005 error |
| G91 overtravel | Start near limit + incremental move | E003 with accumulated position |
| G00 rapid plunge | G00 Z to negative value | Warning about rapid plunge |
| Code after end | Instructions after M30/M02 | Warning about unreachable code |
| Invalid code | Unknown G/M code | E001/E002 error |

## Important Notes
- The Z coordinate range is 0-100, so negative Z values always trigger E003 (range error)
- Safe Z height threshold defaults to 5.0 — horizontal moves below this Z trigger a warning
- The validator is stateful: it tracks position across lines, so test order matters in multi-line programs
- `validate_gcode()` module-level function signature must remain backward compatible
- The `baidu-aip` package is not strictly required for validator testing (only for OCR features)

## Devin Secrets Needed
None — the validator tests require no external credentials.
