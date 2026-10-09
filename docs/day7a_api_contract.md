# Day 7A：受控传统综合判断预览 API

日期：2026-10-09。仅 Windows 本地预览，未公开发布。

## 路由与输入

`POST /api/v1/meihua/traditional-preview`

沿用 Day 4 的 `CastingInput` 严格白名单。浏览器只提交起卦输入，不提交计算结果、审核状态、规则文件或条件真假。

```json
{
  "input_mode": "manual_hexagram",
  "hexagram_id": 20,
  "moving_line": 4,
  "cast_at": "2026-09-24T19:45:35+08:00",
  "question_text": "这件事情有哪些条件需要留意？"
}
```

时间起卦：`input_mode=time_cast`，只允许 `cast_at`、`question_text`，不得同时携带手动卦号、爻位。

| 字段 | 约束 |
| --- | --- |
| input_mode | manual_hexagram / time_cast，必须明确 |
| hexagram_id | 仅手动模式；严格整数 1–64，不接受 bool、字符串或浮点数 |
| moving_line | 仅手动模式；严格整数 1–6，不接受六/九名称覆盖 |
| cast_at | 带偏移量的 ISO 时间；转为 Asia/Shanghai；2000–2099；省略则中国当前时间 |
| question_text | 选填，最多 500 字；拒绝异常控制字符；不参与计算或条件满足判断 |

未知字段拒绝。特别包括 calculation、rule_file、source_path、review_status、eligible、conditions、SQL、prompt、api_url、model。JSON 必须唯一键、有限数值；请求体最多 8192 字节；只接受 application/json。

## 固定调用链

```text
CastingInput
  → TraditionalPreviewService（最多 2 个并行受控调用）
  → 原 OfflineJudgementAdapter / 固定隔离子进程
  → 原 Day 4 FrozenRuntime / 冻结算法及签名校验
  → ValidatedJudgementInput
  → Day 5 TraditionalJudgementEngine
  → day6ab_readonly_registry_v1
  → 原 Day 6A lookup / 原 Day 6B lookup_review
  → traditional_condition_synthesis_v1 政策的网页投影
  → PreviewResponse 严格公开字段白名单
```

没有模型、来源抓取、数据库连接或历史保存。子进程沿用固定环境白名单与 180 秒超时，不继承模型凭据；页面 25 秒超时并锁定重复提交。原 `/api/v1/readings` 基础接口保持兼容，默认仍走基础卦象。

## 输出

根字段只有 `preview_api_version`、`reading`、`judgement`。

`reading` 完整沿用 Day 4 `ReadingResponse`：原卦、动爻、互变卦、体用、生克、节气月建、旺衰、四角色基础卦义、古籍引用及冻结版本；不重新计算或修改任何字段。

`judgement` 公开字段：

- 版本：preview_version、policy_version、registry_version。
- 资格：review_status、eligible_for_condition_review、finite_synthesis_available、scope。
- 有限传统倾向：direction、label、summary、body_use_baseline。非 bounded 时 direction 必须 null。
- 条件：conditions、branches、branch_relationship、scope_limits；每项保留来源 ID、原文短引及绑定的条件 ID，satisfaction 固定 unknown。
- 依据：favorable_factors、adverse_factors、strength_modifiers、auxiliary_analysis。
- 未决项：conflicts、auxiliary_divergences、uncertainties。
- 引用：rules（规则 ID、依据类别、摘要、公开来源 ID）、rule_sources（书名、版本、卷章、扫描页及 HTTPS 来源）、classical_sources。
- 审核说明：review_provenance 只含规则版本、离线逐条审核范围、human_verified=false、is_production_signature=false。
- 固定限制：real_world_conditions=unknown，question_used_to_satisfy_conditions=false，is_final_event_outcome=false，ai_used=false，history_written=false。

不返回原 Frame、内部审核目录、receipt、原签名、source_fingerprint、绑定散列、私有路径、缓存内容或任何密钥。原文范围及来源指纹仍在后台按原目录检查，但不传给浏览器。

前后端独立严格校验状态、资格、结论范围、引用及条件绑定。前端遇到额外字段或非法预览，只保留单独通过 Day 4 schema 的 `reading`，显示安全回退；不会展示原始响应或异常文本。

## 状态

| review_status | 资格 | 有限综合可用 | direction | 行为 |
| --- | --- | --- | --- | --- |
| bounded | true | true | favorable / adverse / mixed | 仅原审核范围，现实条件仍未知 |
| branch_unresolved | true | false | null | 列出不同条件分支，不选择 |
| not_eligible | false | false | null | 保留结构和基础卦义 |
| unreviewed | false | false | null | 保留结构和基础卦义 |
| evidence_unavailable | false | false | null | 排除扩展判断，保留可靠计算 |

有限综合资格不代表已证明现实条件成立，mixed 不由辅助因素数量决定。乾坤互卦保留原争议，仅供参校。

## 错误与安全

400：客户端认证配置；403：不允许 Origin；413：超长请求；415：非 JSON；422：字段或 JSON 无效；503：冻结计算不可用或服务并发已满。

若扩展审核/规则证据损坏但冻结计算仍有效，返回 200 + evidence_unavailable；若冻结生产基线不能通过，则返回 503，绝不编造卦象。

错误只给固定中文提示。服务仅监听 127.0.0.1，保留原 CORS/CSP、安全响应头，不新增 HTTP 批量、调试、规则配置或故障注入接口。
