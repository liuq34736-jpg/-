# 问象纪 Day 7A：传统综合判断网页预览接入

日期：2026-10-09。仅完成本地预览集成，未公开发布。

## 实际实现

已在原梅花易数表单中加入独立的“结果内容”选择：

1. **基础卦象**：默认值，保留 Day 4 现有接口和解释。
2. **传统综合判断预览**：使用新受控接口，同一套起卦输入和冻结计算，追加有限传统规则分析。

访问：<http://127.0.0.1:5173/modules/meihua>。选择“传统综合判断预览”后点击“开始起卦”。

启动：在本项目 PowerShell 执行 `scripts/start-local.ps1`。后端健康：<http://127.0.0.1:8765/api/v1/health>。现有健康字段仍保持 Day 4 兼容，不代表新预览未加载。

网页实际显示：传统综合判断、主要依据、有利/不利因素、旺衰修饰、动爻条件与提醒、未决冲突、互变辅助分析及折叠古籍/审核来源。手机预览判断正文为 16px，桌面梅花结果区域上限为 1120px；首页与品牌没有重做。

## 集成前基线

- 回退提交：`4d4d19e70c8263e1d26dd71be5b8070e6591b7e0`。
- 新分支：`day7a/traditional-preview-integration`；集成前工作区干净。
- 已检查 Day 6B 全部六份文档、机器可读结果、固定审核目录、来源绑定及测试入口。
- 原 357 项测试先完整运行通过。
- 原 Day 6A 引擎仅识别 23 条资格；Day 6B 新 29 条尚未注册到网页。这是本轮补齐的接入缺口，并非重新批准候选。

## 固定只读注册

新增 `backend/traditional_preview_v1/registry.py`，只读取既有 Day 6A/6B 固定审核目录。逐请求重新检查目录 pin、Day 6A 来源扫描指纹、Day 6B 依赖清单、原签名 Frame 与对应引用/条件绑定。

资格判断继续调用原 Day 6A `lookup` 和 Day 6B `lookup_review`；机器候选文件完全不进入注册。旧算法、旧引擎、原 Frame、审核目录、receipt 及原文保持原文件原字节。

| 范围 | 数量 |
| --- | ---: |
| 已有审核记录 | 56（24 + 32） |
| 有离线资格 | 52（23 + 29） |
| 可显示有限综合倾向 | 38 |
| 有资格、分支未决 | 14 |
| 已审但未取得资格 | 4 |
| 未审核 | 328 |

本轮没有批准新的爻位，资格覆盖率仍为 52/384。离线资格并未被改称人工 verified 或生产签名。

## 引擎与展示分离

新增网页投影 `PreviewJudgementEngine`：复用 Day 5 体用与旺衰依据，采用固定 `traditional_condition_synthesis_v1` 的条件、主要张力和辅助分歧政策。只按经过审核的 effect/branch enum 工作，不按汉字情感关键词判断吉凶。

原 Day 6A 24 条逐条对照：资格、综合方向、主要冲突和辅助分歧类型相同。另对 71 个旧案例验证原引擎完整结果 SHA-256，71/71 未改变。

网页摘要只取已审核分支文字及其范围限制，不向用户展示目录内部的 Frame 审计备注。所有现实条件仍为 unknown，用户问题不使条件成立。互、变分歧不按数量投票，也不自动提升为整件事成败。

## 文件与接口

- 新后端：`backend/traditional_preview_v1/{registry,engine,models,service}.py` 与包入口。
- 仅修改后端入口 `backend/app/main.py`，新增路由和相同的请求体边界；原 Day 4 API 不变。
- 新前端：`TraditionalJudgementPreview.tsx`、`traditionalPreviewContract.ts`。
- 仅修改 `MeihuaPage.tsx`、`meihua.css`，增加预览选项、结果组件及局部样式。
- 新测试/验收脚本：`tests/test_traditional_preview_day7a.py`、`scripts/day7a_*.py`；所有旧测试和交付文件未改。

详情见 [API 合约](day7a_api_contract.md)、[回退矩阵](day7a_fallback_matrix.md)、[验收结果](day7a_acceptance_results.md)。

## 安全边界

- 浏览器只能提交手动/时间起卦白名单，不能上传计算 JSON、规则、路径、审核状态、模型或 prompt。
- 后端只输出严格 `PreviewResponse` 白名单。内部审核 receipt、原 Frame、签名、私有路径及缓存不返回。
- React 只使用文本节点；不使用 HTML 注入，不展示原始模型 JSON。来源链接必须 HTTPS。
- 没有 DeepSeek 调用链、自由正文、流式 AI 或公开批量接口。真实付费 AI 请求为 0。
- 固定子进程禁止来源/生产写入、SQLite、网络及模型调用。未创建生产仓储或启动迁移，历史页面仍隔离。
- 仅 127.0.0.1:5173 / 8765；保留现有 CORS/CSP、响应安全头、日志限制和 MIT 署名。

## 完整性与仍未完成事项

完整性校验：原 303 个跟踪文件中仅批准的 3 个 UI/API 入口文件改变；原规则、审核记录与旧引擎未变。157 个生产文件、509 个签名缓存及 42 条旧历史的 schema、逐行散列和数据库字节均相同。

当前不是正式发布：没有个性化 AI 问事正文、现实条件自动认定、问事专门规则、应期、生产历史保存或公开部署。14 条分支未决、4 条无资格及 328 条未审核保持真实状态。

依赖仍有原 `braces <=3.0.3` 的 1 high、0 moderate、0 critical，审计没有发布补丁；未新增或升级依赖。它位于构建工具链，用户请求不进入 glob 模式，但不能据此宣称漏洞已消除。Python `pip check` 通过，不等同完整 Python CVE 审计。

Chrome 手机模式为模拟器及 320px 窄窗口；手机真机浏览器验收未验证。Windows 全系统日志的秘密扫描未验证。

## 截图

- [桌面传统判断](screenshots/day7a-judgement-desktop-viewport.png)
- [手机传统判断](screenshots/day7a-judgement-mobile-viewport.png)
- [完整观六四桌面结果](screenshots/day7a-guan-desktop.png)
- [古籍依据展开](screenshots/day7a-guan-evidence-desktop.png)
- [随六二](screenshots/day7a-sui-desktop.png)
- [乾上九冲突](screenshots/day7a-qian-top-desktop.png)
- [条件分支未决](screenshots/day7a-branches-desktop.png)
- [未审核回退](screenshots/day7a-unreviewed-desktop.png)
- [证据故障的浏览器传输替身](screenshots/day7a-evidence-fallback-desktop.png)

Git 实际记录见 `day7a_git_commit_records.md`。Day 6B 原回退点保留，不推送、不公开部署；本轮完成后等待验收。
