"""Day 4: frozen calculation adapter; no AI readings or production DB."""

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from backend.app.deepseek import MODEL, load_config, public_status, strict_json
from backend.app.meihua_adapter import MeihuaServiceAdapter, MeihuaUnavailable
from backend.app.meihua_models import CastingInput, CatalogResult, ReadingResponse


class ModuleInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    name: str
    description: str
    status: str = "not_connected"


MODULES = (
    ModuleInfo(id="meihua", name="梅花易数", description="手动或时间起卦，查看冻结计算及已批准基础解释。", status="deterministic_ready"),
    ModuleInfo(id="tarot", name="塔罗", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="bazi", name="八字", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="name", name="姓名分析", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="dream", name="解梦", description="独立模块接口预留，尚未实现。"),
    ModuleInfo(id="new_name", name="起名", description="参考项目入口保留，尚未接入。"),
    ModuleInfo(id="relationship", name="姻缘", description="参考项目入口保留，尚未接入。"),
)

app = FastAPI(title="问象纪 · 本地服务", docs_url=None, redoc_url=None, openapi_url=None)
meihua_service = MeihuaServiceAdapter()
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
    elif request.method == "POST" and request.url.path == "/api/v1/readings" and request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
        response = JSONResponse(status_code=415, content={"detail": "请使用 JSON 格式提交起卦信息。"})
    else:
        try:
            if request.method == "POST" and request.url.path == "/api/v1/readings":
                chunks, length = [], 0
                async for chunk in request.stream():
                    length += len(chunk)
                    if length > 8192:
                        break
                    chunks.append(chunk)
                if length > 8192:
                    response = JSONResponse(status_code=413, content={"detail": "提交内容过长，请缩短问题。"})
                else:
                    request._body = b"".join(chunks)
                    try:
                        strict_json(request._body.decode("utf-8"))
                    except (ValueError, UnicodeError):
                        response = JSONResponse(status_code=422, content={"detail": "请求格式不正确。"})
                    else:
                        response = await call_next(request)
            else:
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
    return {"status": "ok", "stage": "day4", "mode": "preview", "real_ai_enabled": False}


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


@app.exception_handler(MeihuaUnavailable)
async def meihua_unavailable(_request, _error):
    return JSONResponse(status_code=503, content={"detail": "冻结计算服务暂不可用，请检查本地服务和版本基线。"})


@app.get("/api/v1/meihua/catalog", response_model=CatalogResult)
def meihua_catalog():
    return meihua_service.catalog()


@app.post("/api/v1/readings", response_model=ReadingResponse)
def calculate_reading(request: CastingInput):
    return meihua_service.calculate(request)
