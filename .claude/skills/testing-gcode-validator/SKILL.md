---
name: testing-gcode-validator
description: Test the GCode validator logic and safety checks end-to-end. Use when verifying changes to backend/app/core/gcode_validator.py or the /api/v1/gcode/validate endpoint.
---

# Testing GCode Validator

## Unit tests

在 Windows PowerShell 中运行：

```powershell
Set-Location backend
python -m pytest tests\test_gcode_validator.py -v
```

测试应覆盖：

- 合法程序无误报。
- E005：主轴启动前切削。
- 安全 Z 高度警告。
- G91 增量位移累计越界。
- G00 快速向负 Z 下刀。
- M30/M02 后不可达代码。
- 进给速度验证。
- E001、E003 向后兼容。

## API 端到端验证

启动后端：

```powershell
Set-Location backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

使用 PowerShell 请求：

```powershell
$body = @{ gcode = "G90 G54`nM03 S3000`nG00 X10.0 Y10.0 Z50.0`nG01 Z5.0 F500`nM05`nM30" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/gcode/validate" -ContentType "application/json" -Body $body
```

## 关键约束

- Z 坐标允许范围为 0–100，负 Z 会触发 E003。
- 默认安全 Z 高度为 5.0。
- validator 会跨行跟踪位置状态。
- 模块级 `validate_gcode()` 函数签名须保持兼容。
- validator 测试不依赖 OCR 或外部凭据。
