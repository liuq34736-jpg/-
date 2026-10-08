"""Day 3: server configuration/status only; no readings or production DB."""

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from backend.app.deepseek import MODEL, load_config, public_status


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

app = FastAPI(title="问象纪 · 本地服务", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
ALLOWED_ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173"}
app.add_middleware(CORSMiddleware, allow_origins=sorted(ALLOWED_ORIGINS),
                   allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"],
                   allow_headers=["Content-Type"])


@app.middleware("http")
async def preview_boundary(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        response = JSONResponse(status_code=403, content={"detail": "本地服务不接受其他来源。"})
    elif any(name in request.headers for name in ("authorization", "x-api-key", "x-api-url", "x-api-model")):
        response = JSONResponse(status_code=400, content={"detail": "本地服务不接受客户端认证配置。"})
    else:
        try:
            response = await call_next(request)
        except Exception:
            # Do not log/return exception text, request body, headers or traceback.
            response = JSONResponse(status_code=500, content={"detail": "本地服务暂不可用，请稍后再试。"})
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(_request, _error):
    return JSONResponse(status_code=422, content={"detail": "请求格式不正确。"})


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "stage": "day3", "mode": "preview", "real_ai_enabled": False}


@app.get("/api/v1/modules", response_model=list[ModuleInfo])
def modules():
    return list(MODULES)


@app.get("/api/v1/config")
def public_config():
    # Explicit public whitelist; never serialize the server configuration.
    load_config()  # Credential lookup is server-side; no upstream call.
    return {
        "mode": "preview", "provider_name": "deepseek", "model_name": MODEL,
        "real_ai_enabled": False, "production_connected": False,
        "credentials_checked": True, "history_mode": "isolated_preview",
    }


@app.get("/api/v1/ai/status")
def ai_status():
    # Checking status/refreshing the page cannot initiate a paid API request.
    return public_status()


@app.get("/api/v1/history")
def history():
    # No production imports, DB connections, file reads or fabricated readings.
    return {"items": [], "total": 0, "mode": "isolated_preview", "production_connected": False}


@app.post("/api/v1/readings")
def readings_not_connected():
    return JSONResponse(status_code=501, content={"detail": "梅花服务将在后续阶段接入，本轮不执行解卦。"})
