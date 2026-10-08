# 网页无法打开：检查与修复

日期：2026-10-08。只修复新项目启动，不进入 Day 3。

## 检查结果

- 初始 5173、8765 都没有监听，两个网址都连接失败。
- 旧日志只有成功启动消息，没有应用异常或完整退出原因。因此不能断言此前进程具体因何退出。
- Python虚拟环境存在；pip check通过。Node 24.19.0、pnpm 11.25.0 与已安装Vite 6.4.4正常；前端构建通过。
- Node与pnpm只在Codex提供的临时PATH可见，不在Windows用户/系统持久PATH中。原start-local.ps1直接Get-Command node，普通Windows环境启动会失败。
- Vite仍固定127.0.0.1:5173，代理/api到127.0.0.1:8765，未更换端口或绑定外网。

## 修复内容

- `scripts/start-local.ps1`：兼容现有Node定位，验证依赖，独立后台启动，确认端口所有权及HTTP健康；已运行时幂等复用，部分停止时补启动。
- `scripts/local-runtime.ps1`：工具定位、实例与端口所有权检查、仅停止本项目进程树。
- `scripts/local-service.py`：隐藏服务启动、项目日志与状态记录；不导入生产项目，不读取密钥，不调用AI。
- `scripts/stop-local.ps1`：不依赖临时Node PATH，验证实例后仅停止本项目进程。
- `启动网页.bat`：调用修复后的脚本并打开本地网址。批处理双击界面未单独验收，底层启动命令已验收。
- `tests/test_local_launcher.py`：新增4项启动命令边界回归。
- 更新LOCAL_START.md；业务、Vite端口/代理、依赖版本未修改。

## 实际测试

| 检查 | 结果 |
|---|---|
| unittest（原12项+新增4项） | 16/16 PASS |
| 真实Chrome桌面/390px浏览器检查 | 23/23 PASS |
| Python依赖兼容 | pip check PASS |
| TypeScript/Vite构建 | PASS |
| 普通Windows持久PATH环境启动 | PASS，无需Node/pnpm在PATH |
| 同一服务重复启动 | PASS，没有重复启动 |
| 停止本项目后端/前端再启动 | PASS，停止后0监听，再启动两端恢复 |
| 未知端口所有权 | PASS，拒绝启动；原前后端仍HTTP200；模拟状态恢复 |
| 5173/8765监听范围 | 仅127.0.0.1 |
| 后端/api/v1/health | HTTP200，status=ok，mode=preview |
| 首页/ | HTTP200，Chrome正常加载 |
| 前端/api/v1/health代理 | HTTP200 |
| 启动命令结束后独立复查 | 两服务仍正常；服务监督进程与子进程不属于测试命令调用者的Job |
| 浏览器外部请求/认证头 | 0 / 0 |

Job检查补充：Windows WMI进程可能属于Windows自己的Job，不能用「是否属于任意Job」判断它是否依赖Codex。`local_caller_job_check.json`直接比对调用者Job成员，服务均不在其中。没有结束调用者Job或其他程序来做破坏性测试。

生产只读基线复查：157个文件、509个签名/语义缓存文件与42条历史记录、schema、数据库字节hash均一致。旧生产测试未重跑，也未修改生产系统。

## 使用

- 网页：**http://127.0.0.1:5173/**
- 后端：**http://127.0.0.1:8765/api/v1/health**
- 本地服务已启动；以后可双击新项目根目录的启动网页.bat，或按LOCAL_START.md执行PowerShell命令。

未设置开机自启；重启Windows后需重新启动。真实AI仍未启用，Day3未执行。之前已记录的lint/依赖安全告警不属于本轮启动修复范围，未声称已解决。
