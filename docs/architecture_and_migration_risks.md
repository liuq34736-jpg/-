# 占筮网页平台：Day 1 架构与迁移风险

日期：2026-10-08。范围仅 Day 1–2；以下「后续架构」为设计，未实现，不代表已经接入服务。

## 1. 两个项目的实际状态

- 生产系统：`D:\算卦工具\streamlit_mvp`，VERSION `1.2.0`，不是 Git 仓库。本轮未初始化、覆盖、移动或修改。
- 新项目：`D:\算卦工具\divination-web`，独立克隆 [chatgpt-tarot-divination](https://github.com/dreamhunter2333/chatgpt-tarot-divination)，上游提交 `2b73870e5400811f6f5172259d15aa767e06d194`（2026-08-27）。本地分支 `week1/day1-day2`；远端改名 `upstream`，未推送。
- 重要既有问题：生产 `docs/question_interpretation_v2_final_acceptance.md` 发布结论为 **FAIL**，虽有 893/893 测试通过，原典抽查 12 例中 5 FAIL、1 WARNING，首次批准 19/30，保护修复后同批仅 11/30 仍可用。不能将测试全绿当成问事语义验收通过。本轮未修改该结论或重新调用 AI。
- `traditional_judgement_v1`：未发现正式实现，不在本轮或已完成能力清单内。

## 2. 当前实际运行结构

```text
浏览器
  → React 18 / TypeScript / Vite 6（127.0.0.1:5173）
  → /api 同源本地代理
  → 独立 FastAPI preview（127.0.0.1:8765）
       health / modules / public config / 空预览历史
       readings → 501（尚未接入）

生产 Streamlit / 数据 / 历史 / SemanticFrame：完全不接入运行链
真实 AI：完全不接入；环境密钥未检查、未读取
```

保留上游 React、BrowserRouter、Vite、Tailwind、Radix Button/Card 结构。新入口 `frontend/src/App.tsx` 只挂载 `platform/PlatformPreview.tsx`，不导入上游 store、密钥设置、原始流式结果组件或两数字梅花页。

`backend/app/main.py` 没有生产项目导入、环境变量读取、AI 客户端、数据库访问。所有模块均为 `not_connected`，首页入口可查看说明，不能执行解卦。设置显示 mock，历史为空的隔离预览，不能将其描述为生产历史迁移成功。

## 3. 拟复用模块与边界

| 已有文件/模块 | 已有职责 | 后续适配约束 |
|---|---|---|
| `iching/algorithm.py` | traditional_meihua_datetime_v1 | 原样调用，问事文本不得参与计算 |
| `iching/manual_hexagram.py` | 用户本卦、动爻结构及名称校验 | 保留手动输入；时间仅用于时令 |
| `iching/analysis/` | 互卦、变卦、体用、五行、生克、旺衰 | 锁定 v1，不采用上游 AI 两数字起卦 |
| `iching/interpretation/engine.py` | 结构化解释、证据链 | 结构字段只由确定性代码产生 |
| `iching/daily_reading/engine.py` | daily_reading_v1 | 原样使用，不重写历史定义 |
| `iching/manual_service.py` | 分析、资料、语义流程编排 | 必须显式隔离缓存/来源获取/生成策略，防止隐式付费调用 |
| `iching/question_service_v2.py` | 问事入口 | 复用 analyze_question_input；本轮未调用 |
| `iching/question_interpretation_v2.py` | 意图、应用解释、独立审核、签名、缓存、失败回退 | 必须保留当前必要保护修复及审核门槛；既有发布 FAIL 仍需处理 |
| `iching/question_provider_v2.py` | 受控 DeepSeek Provider | 服务器持有 Key；类型化请求、HTTPS、禁重定向、限重试，Day 3 验证 |
| `iching/question_snapshot_v2.py` 等 | v1.2/旧版快照校验与回放 | 回放当时文本，不用当前数据重新解释；旧快照保持原样 |
| `storage/repository.py` | 保存白名单、验证 snapshot、读取记录 | 仅通过受控服务接口；web 不自行连生产 SQLite |
| canonical corpus / 签名 SemanticFrame / receipts | 已批准原典与语义证据 | 只读，保留状态、指纹、签名与来源引用 |

现有历史仓储是 Python 接口，**不是已经存在的远程 HTTP 历史服务**。新网页需要服务边界设计，当前尚未接入。仓储构造/迁移可能写库，不能仅以「导入代码」认定只读。不得为省事从前端直接读 SQLite，或在 web 启动时初始化生产仓储。

## 4. 后续目标架构（未实现）

```text
React 用户输入（手动 / 独立时间起卦）
 → FastAPI 请求结构/大小校验
 → MeihuaServiceAdapter（独立、版本固定）
 → 既有确定性服务 → 固定四角色 Frame 与 source evidence
 → question_interpretation_v2 → 独立审核
 → approved application 或既有安全 fallback
 → deterministic renderer → 允许展示的结果 DTO
 → 受控历史接口保存签名快照
```

AI 未审核内容、prompt、原始模型响应和 Key 不进入浏览器；浏览器只接收完成审核后的结果，可用作业状态表示等待，不直接流式展示 AI 正文。历史列表/详情只暴露必要字段；回放由既有校验链处理，失败安全回退并保留原记录。

未来独立模块契约可包含 module_id / input_schema / capabilities / result_schema / evidence / snapshot_version。塔罗、八字、姓名、解梦必须分别实现，不能以「一个通用 AI 提示词」声称正式完成。

## 5. 上游审查与隔离

| 定位 | 观察 | 本轮处理 / 后续风险 |
|---|---|---|
| `src/divination/plum_flower.py:5` | 请求模型按两数字起卦和解释 | 原文件保留参照，但没有挂载运行；后续绝不替代确定性核心 |
| `frontend/src/pages/Settings.tsx`、`store/index.ts` | 浏览器 API Key 配置及持久化状态 | 新入口不使用这些代码，无 Key 输入、localStorage 写入 |
| `frontend/src/hooks/useDivination.ts`、`src/chatgpt_router.py` | 自定义 key/url/model header、直接 AI SSE | 新页面不导入，新后端无该路由；不能绕过审核接入 |
| `frontend/src/components/ResultDrawer.tsx:95` | dangerouslySetInnerHTML | 新页面只用 React 文本节点；完整旧链 XSS 审查留 Day 3 |
| `src/app.py` | 通配 CORS、原始异常文本、异常详细日志 | 新后端固定 loopback、Host/Origin 拦截，不运行上游 app |
| 上游 `frontend/index.html` | AdSense 外部脚本、原站公开部署元信息 | 本地入口移除广告/外部资源；浏览器实测外部请求 0 |
| 新 index CSP | 本地开发 CSP 仍允许 unsafe-inline 配合 Vite | 不是生产 CSP；nonce/严格部署策略未验证，必须后续完善 |
| 根 `main.py` / Docker / Vercel / Tauri | 存在上游原启动与部署入口 | 本轮不运行、不发布；只用新 scripts/start-local.ps1 |

上述是 Day 1 的源码检查与 Day 2 的预览隔离，不替代 Day 3 完整 API/日志/渲染/CSP 审查。原上游高风险路径仍存在于代码参照区，不能误启动旧 main.py。

## 6. 冻结基线

`docs/production_baseline.json` 保存 157 个生产文件 SHA-256；另保存 509 个语义/审核/签名缓存文件 SHA-256。含生产算法、分析、旺衰、解释、daily_reading、问事服务、资料 JSON 和测试代码，以及原启动器。

SQLite 以只读模式审计：42 条记录、schema、逐行 SHA-256、数据库字节 SHA-256。不复制正文、不写库。签名密钥仅记文件哈希，不复制密钥内容。后验结果见 `docs/production_integrity_result.json`。本轮不重新运行旧系统 893 项全回归，按计划留 Day 7。

## 7. Day 3–7 的依赖与风险（全部尚未实施）

| 阶段 | 依赖 / 风险 | 当前状态 |
|---|---|---|
| Day 3 | 仅存在性检查 DEEPSEEK_API_KEY；官方 HTTPS、typed request、限重试、最小真实调用；异常脱敏/Key不落库 | 未验证，0真实调用 |
| Day 4 | 版本固定适配层、显式路径及只读策略；黄金案例回归；避免导入时触发缓存/数据库迁移 | 未接入 |
| Day 5 | 保留审核/签名/fallback；现有问事发布 FAIL 和源 Frame 条件完整性问题影响上线 | 未验收，不得声称传统综合断卦完成 |
| Day 6 | 受控历史服务、隔离新记录、移动端真实设备/触屏/可访问性、六爻图形及依据展开 | 仅桌面Chrome与390px视口预览通过，真机未验证 |
| Day 7 | 旧893项回归、新API、构建、浏览器、密钥、历史完整性、依赖安全及许可证附件 | 未执行整体验收 |

前端兼容更新后仍有 1 high、3 moderate 依赖告警，详见 dependency 审查文件；React Router 修复涉及升级大版本，不应把本轮构建通过等同于依赖完全安全。公开部署严格禁止；Windows 防火墙无需开放入站端口。
