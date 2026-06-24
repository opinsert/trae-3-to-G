import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import natural_language, drawing, stl, gcode, examples, advance
from app.utils.config import settings

app = FastAPI(
    title="G代码转换系统",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

_allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5175,http://127.0.0.1:5175",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(natural_language.router, prefix="/api/v1/natural-language", tags=["自然语言转换"])
app.include_router(drawing.router, prefix="/api/v1/drawing", tags=["工序图转换"])
app.include_router(stl.router, prefix="/api/v1/stl", tags=["STL文件转换"])
app.include_router(gcode.router, prefix="/api/v1/gcode", tags=["G代码验证"])
app.include_router(examples.router, prefix="/api/v1/examples", tags=["工序卡示例"])
app.include_router(advance.router, prefix="/api/v1/advance", tags=["进阶功能"])

@app.get("/")
async def root():
    return {"message": "G代码转换系统 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
