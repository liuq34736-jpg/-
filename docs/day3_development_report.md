# 问象纪网页版 Day 3 开发与验收报告

日期：2026-10-08。项目：`D:\算卦工具\divination-web`。

## 结论与阶段边界

Day 3 的服务器端 DeepSeek 配置、一次最小连通性测试、安全修复、ESLint 和界面回归已完成。依赖审计仍有 **1 high** 未能消除，须继续跟踪。等待用户审核；没有执行 Day 4。

当前只是本地配置与连通性接入。正式梅花易数 API、问事应用正文、生产历史均未连接；页面继续标注开发中。未实现的 `traditional_judgement_v1` 没有用临时 AI 判断替代。

## Git 与品牌 UI 回退点

- 已验收品牌 UI 的本地基线：`e75fe153822348d79055668df9d0d63567ceae68`。
- Day 3 实现提交：`b1144b2a3717383a5553f7e36ad1bb18daf2b641`。
- 当前分支：`day3/deepseek-security`；只做本地提交，没有推送远端。
- 提交前分别扫描候选文件与 Git 暂存区，未发现凭据、数据库、缓存数据、运行日志或私有文件。上游已有 `.env` 文件已在基线提交中移出当前跟踪，本地文件保留，未改写上游历史。
- 原 MIT 许可证和 Copyright (c) 2023 dreamhunter2333 保留，页面署名保留。

详细记录见 [Git 提交记录](day3_git_commit_records.md)。

## DeepSeek 调用链

```text
浏览器 → 本机 Python API → 安全公共配置状态
本机开发诊断脚本 → 服务器端 DeepSeekConnectivityProvider → 官方 HTTPS
```

采用此前已验证的配置值，未导入或执行生产系统：

| 项目 | 实际值 |
| --- | --- |
| provider_name | deepseek |
| endpoint | https://api.deepseek.com/chat/completions |
| model_name | deepseek-flash |
| 凭据读取 | DEEPSEEK_API_KEY，进程环境优先，Windows 用户环境补充 |
| timeout | 20 秒 |
| HTTP 重定向 | 全部禁止，包括同源 |
| 真实请求上限 | 本阶段 1 次，0 重试 |
| 客户端上游请求 | 不允许；浏览器 CSP 不包含 DeepSeek |

新增 `backend/app/deepseek.py` 提供固定内容的连通性诊断，没有任意 prompt、自由正文或流式输出接口。`GET /api/v1/ai/status` 只读取配置，刷新页面不会调用模型。真实诊断仅可通过本地脚本触发，网页没有付费调用入口。

诊断脚本以排他文件标记防止本阶段重复请求；标记位于 Git 忽略的 runtime 中。不要删除标记来反复测试。

配置来源说明见 [DeepSeek 配置来源](day3_deepseek_config_provenance.md)。

## API 连通性实际结果

先完成 Mock 测试，之后只进行了 **一次**真实请求：

| 指标 | 结果 |
| --- | --- |
| HTTP | 200，成功 |
| 总耗时 | 0.642 秒 |
| 请求 / 重试 | 1 / 0 |
| 固定 JSON 协议 | 通过，未人工修补返回 |
| prompt / completion tokens | 42 / 5 |
| total tokens | 47 |
| 费用 | unavailable，API 未返回费用 |
| 原始响应 / 请求头保存 | 否 |
| 正式断卦生成 | 否 |

记录见 [连通性结果](day3_api_connectivity_result.json)。这个结果仅证明当次诊断可调用，不是正式问事审核通过的证明。

## 安全与依赖

- 密钥只留在后端内存和服务器环境；配置 repr 隐藏密钥，公共输出严格白名单。
- 302/307/308 跨 HTTPS 来源、HTTPS → HTTP、同源重定向均用真实 urllib opener 的 Mock 传输测试拒绝，不转发认证头。
- HTTP 401/403/429/500/502、网络错误、空响应、非 JSON、多余字段、重复键、超限响应、凭据回显均安全失败；不读取上游 HTTP 错误体、不输出异常对象。
- 前端 React 文本节点显示状态；移除遗留 HTML 注入，禁用遗留浏览器密钥/自由流式传输，lint 限制重新导入旧调用路径。
- CORS 明确限制本机两个来源；拒绝陌生 Origin 和客户端认证配置。CSP 脚本仅 self 与开发工具精确哈希许可，样式仍允许 inline，此限制已公开记录。
- 前后端都有 nosniff、no-referrer、防嵌入头；仅监听 127.0.0.1。
- 修复原 3 moderate：React Router 固定到 7.18.4，PostCSS selector parser 固定到 7.1.6。
- 原 braces 3.0.3 的 1 high 暂无发布补丁，仍显示在 audit 中；当前为固定仓库模式的构建工具依赖，不接受用户 glob。没有隐藏告警或声称已经修好。
- 316 个前端依赖和 18 个独立 Python 包的许可证清单更新。`pip check` 通过，未做完整 Python CVE 审计。

详细说明见 [安全与依赖修复报告](day3_security_dependency_report.md)、[依赖审计结果](day3_dependency_audit.json)、[密钥边界检查](day3_secret_boundary_result.json)。密钥检测覆盖新项目 Git 候选、runtime 日志/收据及前端构建产物，匹配数为 0；不代表审计了 Windows 全部系统日志。

## 测试与启动

| 检查 | 实际结果 |
| --- | --- |
| 单元 / API / 安全测试 | 57 passed / 0 failed / 0 skipped；保留原 26 项，新增 31 项 |
| 真实 Chrome 检查 | 64 passed / 0 failed；原品牌 56 项 + Day 3 新增 8 项 |
| ESLint 9 | 通过，0 error / 0 warning |
| TypeScript + Vite build | 通过 |
| pip check | 通过 |
| Git diff --check | 通过 |
| pnpm audit | 未全绿：1 high / 0 moderate / 0 critical |
| 后端健康、状态接口 | 正常；已配置，正式解卦未启用 |
| 原生产测试全集 | 本轮未重新运行；采用只读基线完整性校验 |

单元测试存在 FastAPI/Starlette TestClient 的 httpx 迁移弃用提示，不是测试失败；ESLint 9 的支持状态及依赖维护事项见安全报告。

Chrome 结果：0 外部浏览器请求、0 客户端认证头、0 页面错误。2 条 console error 来自故意模拟网络断开，非意外错误。移动端是 Chrome 390px 模拟及 320px 窄窗口检查，尚未进行手机真机联网验收。

[机器可读测试结果](day3_test_results.json)、[Chrome 逐项结果](day3_browser_results.json)。

本地地址：

- 首页：<http://127.0.0.1:5173/>
- 设置：<http://127.0.0.1:5173/settings>
- 健康：<http://127.0.0.1:8765/api/v1/health>
- 安全状态：<http://127.0.0.1:8765/api/v1/ai/status>

可以双击项目中的 `启动网页.bat`，或执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\算卦工具\divination-web\scripts\start-local.ps1"
```

脚本、端口保持原样，复用本项目现有服务，不停止其他程序。详细启动方式见 [本地启动说明](LOCAL_START.md)。

## 问事质量分析与生产完整性

只读分析旧问事最终验收的失败问题，产出 [问事失败原因与修复方案](day3_question_quality_analysis.md)。旧报告仍为 **FAIL**：隐含保证、未提供事实、来源条件扩展、时间误识别及核验相关性等问题需要独立质量修复。此报告中的方案没有实现，也没有修改旧 Frame、资料、算法、审核门槛或历史。

原系统只读基线校验：

- 157 个基线生产文件：0 改变。
- 509 个签名语义缓存：0 改变。
- 42 条历史记录：表结构、行哈希、数据库文件字节均一致。
- 新项目 9 项保护基线：只有 3 个预期改动，0 非预期改动；MIT、Python requirements 和启动脚本未改变。

见 [生产完整性结果](production_integrity_result.json)、[新项目保护文件结果](day3_new_project_integrity.json)。检查范围为已记录基线，不宣称扫描了生产系统所有未纳入基线的文件。

## 截图

- [桌面首页](screenshots/day3-desktop.png)
- [DeepSeek 安全设置](screenshots/day3-settings.png)
- [手机尺寸首页](screenshots/day3-mobile.png)
- [手机尺寸导航](screenshots/day3-mobile-navigation.png)
- [梅花入口开发中](screenshots/day3-meihua.png)
- [隔离历史页面](screenshots/day3-history.png)

## 下一阶段

[Day 4 API 整合计划](day4_api_integration_plan.md) 是待审核计划。将先用 Mock 接入冻结计算和受控来源/历史契约，正式问事审核与回退按后续阶段单独验收。

当前 POST `/api/v1/readings` 仍返回 501，生产历史仍未接入，付费网页调用未开放。本轮到此停止。
