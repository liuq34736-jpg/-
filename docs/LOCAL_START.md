# 问象纪 · Windows 本地启动

新项目目录：`D:\算卦工具\divination-web`。只监听本机。不要运行上游根 main.py、Docker、Vercel 或 Tauri 启动方式。

当前阶段：Day 3。后端支持服务器端 `DEEPSEEK_API_KEY`（进程环境优先，Windows 用户环境作为补充），前端设置只显示安全配置状态。`/api/v1/ai/status` 不发起付费请求；正式解卦与生产历史仍未接入。

## 已验证工具版本

- Windows / Python 3.13.15 / Node 24.19.0 / pnpm 11.25.0 / Git 2.53.0。
- 前端直接依赖固定于 package.json；传递依赖固定于 pnpm-lock.yaml。
- 后端全部已安装包固定于 backend/requirements.lock.txt；上游根 requirements.txt 仅保留参照，本轮不安装。
- esbuild 为唯一明确允许执行构建脚本的依赖，配置于 frontend/pnpm-workspace.yaml。

## 安装（本机已完成）

```powershell
Set-Location -LiteralPath 'D:\算卦工具\divination-web'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
Set-Location -LiteralPath 'D:\算卦工具\divination-web\frontend'
pnpm install --frozen-lockfile
```

本机 npm/corepack 未找到；已使用现有 pnpm.cmd，没有安装系统级工具或修改生产虚拟环境。

## 一键启动/停止

也可双击项目根目录的 `启动网页.bat`，它调用同一启动脚本并打开本地网址。

```powershell
Set-Location -LiteralPath 'D:\算卦工具\divination-web'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
```

启动脚本定位 PATH 中或本机现有缓存中的 Node 24；普通 Windows PATH 没有 Node/pnpm 时也可启动已安装的 Vite，不要求修改系统环境变量。通过 Windows WMI 启动隐藏的独立后台服务，等待 health 与首页成功；关闭启动窗口后服务继续运行。

本项目已正常运行时再次启动直接复用；只有一项停止时补启动该项。其他程序占用端口时中文提示并拒绝启动，不终止未知程序，不自动换端口。停止脚本验证实例标记与进程关系，只停止本项目服务及其子进程。服务日志在本项目 runtime（Git忽略），没有真实 Provider、请求体或认证头日志。重启 Windows 后需重新启动，未设置开机自启。

- 前端：http://127.0.0.1:5173/
- 设置：http://127.0.0.1:5173/settings
- 预览历史：http://127.0.0.1:5173/history
- 后端健康：http://127.0.0.1:8765/api/v1/health

## 分别启动

```powershell
# 终端一，项目根目录
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765 --no-access-log

# 终端二，frontend目录
pnpm dev --host 127.0.0.1 --port 5173 --strictPort
```

不能将 host 改成 0.0.0.0，本周不开放局域网/外网。手机浏览器能力本轮仅用 Chrome 390px 视口模拟验证，不声称已经通过手机真机联网验收。

## 本轮检查命令

```powershell
# 根目录
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 scripts\verify_production.py

# frontend目录
pnpm build
pnpm audit
pnpm lint
```

Day 3 已增加 ESLint 9 flat config，lint 与构建通过。依赖审计仍有 1 项无已发布补丁的 braces high 告警，详见 `day3_security_dependency_report.md`，未忽略或隐藏。

## Day 3 连通性测试

开发用 Mock 测试不会访问网络：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\check_deepseek_connectivity.py --mock
```

本阶段的一次真实测试已经完成。真实入口仅为本地开发脚本（`--real`），没有网页按钮或 HTTP 调用接口。它使用固定诊断内容，最多一次请求，不重试；`runtime/day3_real_api_attempt.json` 通过排他创建阻止本阶段重复执行。不要删除标记来重复测试。原始响应与认证头不保存。

浏览器 smoke 使用真实本机 Chrome。Playwright 未加入业务运行依赖；本轮只读借用原系统已有测试工具，未向生产目录安装包：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts\browser_smoke.py --playwright-path 'D:\算卦工具\streamlit_mvp\.test_tools\v1_final_browser'
```

没有上述测试工具的机器，浏览器自动测试为「未验证」，需在独立测试环境安装 Playwright；不应向生产虚拟环境安装。
