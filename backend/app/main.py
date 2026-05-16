from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import natural_language, drawing, stl, gcode, examples, advance

app = FastAPI(title="G代码转换系统", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
