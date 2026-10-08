"""Day 1–2 preview only: no credentials, providers, casting or production DB."""

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class ModuleInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    name: str
    description: str
    status: str = "not_connected"


MODULES = (
    ModuleInfo(id="meihua", name="梅花易数", description="输入自己起好的卦，查看有依据的中文解读。"),
    ModuleInfo(id="tarot", name="塔罗", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="bazi", name="八字", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="name", name="姓名分析", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="dream", name="解梦", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="new_name", name="起名", description="参考项目入口保留，尚未接入。"),
    ModuleInfo(id="relationship", name="姻缘", description="参考项目入口保留，尚未接入。"),
)

app = FastAPI(title="占筮平台 · 本地预览", docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
ALLOWED_ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173"}


@app.middleware("http")
async def preview_boundary(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "本地预览不接受其他来源。"})
    if any(name in request.headers for name in ("authorization", "x-api-key", "x-api-url", "x-api-model")):
        return JSONResponse(status_code=400, content={"detail": "本地预览不接受客户端认证配置。"})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "stage": "day1_day2", "mode": "preview", "real_ai_enabled": False}


@app.get("/api/v1/modules", response_model=list[ModuleInfo])
def modules():
    return list(MODULES)


@app.get("/api/v1/config")
def public_config():
    # Deliberately static; no environment variables or production settings read.
    return {
        "mode": "preview", "provider_name": "mock", "model_name": "not_connected",
        "real_ai_enabled": False, "production_connected": False,
        "credentials_checked": False, "history_mode": "isolated_preview",
    }


@app.get("/api/v1/history")
def history():
    # No production imports, DB connections, file reads or fabricated readings.
    return {"items": [], "total": 0, "mode": "isolated_preview", "production_connected": False}


@app.post("/api/v1/readings")
def readings_not_connected():
    return JSONResponse(status_code=501, content={"detail": "梅花服务将在后续阶段接入，本轮不执行解卦。"})
