# question_application_contract_v1

阶段：Day 8A，离线设计与可运行原型。生产状态：未接入。代码：`backend/question_quality_v1/`。

## 1. 受控输入

只有 `build_request(ValidatedJudgementInput)` 可签发内部 `QualityRequest`。普通 dict、浏览器 JSON、指定规则/文件路径不被接受。

输入来自原固定 worker：

- 用户原问题，仅作解释上下文；禁止参与任何冻结计算。
- 原计算结果：本卦、动爻、互变、体用、生克、旺衰及其版本。
- 已通过原签名校验的四角色批准 Frame；Frame digest 与角色必须一致。
- 状态为 verified/machine_verified 的来源证据及正文。
- 由服务自己重新读取固定 Day7A 引擎得出的原资格、方向、条件、冲突和范围限制。

输入带 HMAC 封印及规范内容指纹；每次校验确认没有改变。不向网页公开密钥、内部 payload、私人路径或原始模型响应。这不是新的生产 Frame 签名或历史签名方案。

## 2. QuestionIntent

```text
category: general/career/business/relationship/decision/travel/other
focus: 原问题精确 QuestionSpan
provided: 最多12个精确 QuestionSpan
missing: background/options/constraints/time_window/other_party_view
QuestionSpan: start,end,text,kind
kind: reported/reported_speech/goal/question/time_window/unknown
```

目标、疑问、指令、转述不等于已认定的现实事实。原文提及的时间窗口不能被记为缺失；不能生成现实截止期。结构及已知词检查只是基础 gate，真实意图提取与独立意图核验尚未接入。

## 3. 四角色 ApplicationDraft

严格字段白名单、严格 bool/int、未知字段拒绝，不接受 direction、qualification、hexagram、raw prompt或额外 reality facts。完整草稿必须恰有本卦、动爻、互卦、变卦四个角色。

每条 `ApplicationClaim`：

| 字段 | 约束 |
| --- | --- |
| claim_id / role | 唯一 ID与四角色绑定 |
| frame_id | 对应批准 Frame 的规范 SHA256 |
| meaning_refs | 原 Frame core_claims 的合法唯一索引 |
| source_evidence_ids | 必须完全等于选中原子 supported_by，来源必须可用 |
| question_spans | 必须逐字符对应原问题，不把目标等改成事实 |
| preserved_limit_ids | 全部原 conditions/cautions；动爻还包含 Day7A conditions/scope_limits，不得增删 |
| analogy_text | 20–180字；明确条件性的现实应用类比 |
| guidance | 6–80字；证据范围内的核对/观察动作 |
| source_layer | 固定 application_analogy，不可伪装古籍或现代译注 |

模型只生成问题应用，不能声明计算、生克、时令、综合方向、裁决资格或现实吉凶。未审核爻位依旧未审核：可以应用基础卦义，不可以得到模型创造的最终综合裁决。

已知 Q14 原典限制不足使用独立的只拒绝范围记录，绑定原子、来源指纹、原文引用。该文件规范内容 SHA固定，缺失或变动即安全回退；没有卦名关键词推断或新资格批准。

## 4. 独立核验 receipt

`IndependentVerdict` 绑定 contract_version、request_fingerprint、完整草稿 digest，以及恰好四条 claim。

每条必须回传准确的 reviewed_frame_id、reviewed_evidence_ids、reviewed_limit_ids，并全部满足：

1. supported
2. preserves_conditions
3. no_invented_facts
4. no_prediction
5. preserves_scope
6. question_relevant

score≥3（0–4量尺），reason 8–400字。这里 score 是审核支持程度，不是现实成功概率，不向用户显示成功分数。任何绑定缺失、false、低分、额外字段均失败。

候选生成器和核验器不能是同一对象。核验器重新收到原问题、冻结事实、批准原子、可靠源全文、全部条件和草稿；不给它生成器的推理过程或对话上下文。实际不同会话/模型的独立性与真实核验质量：未验证，Mock 不构成证明。

## 5. 确定性渲染

- “传统卦义”逐字取自已批准原子。
- “现实应用类比（未认定现实条件）”显式区分模型应用文本与古籍。
- 程序逐字附带全部条件/限制及现实尚未核实提示。
- 互卦只作辅助；变卦是变化方向，不是必然发生的结果。
- 体用/旺衰/传统倾向另取冻结结果及 Day7A 判断，绝不能取模型草稿。

不直接流式展示任何待核验正文。离线成功仅 `OFFLINE_ACCEPTED`；`production_approved=false`、`history_written=false`。失败返回原标准基础卦义 `BASE_FALLBACK`，不人工修补模型输出、不自动重试，不改变资格或资料。

## 6. 安全边界与下一阶段

原 Provider/密钥/CORS/CSP/来源签名/生产数据库规则保持原样。本原型没有 HTTP 出站功能、生产缓存或数据库写入，没有注册 API。测试 fixture 的解释不可导入正式语义资料。

真实 Provider、重放 receipt、生产签名、专属缓存及历史 replay 仍须另行设计与验收。失败负缓存建议独立命名空间：原问题规范哈希 + 全部 Frame/source/规则指纹 + 模型/契约版本；短 TTL，明确手动重试入口，不缓存敏感问题正文到日志。该建议尚未实施，不读取/改变旧缓存或历史。

不能仅因六项 true 就宣称开放语义可靠。真实源抽查、条件逐项对照、反例攻击和跨问题应用差异是正式接入前的必要验收项。
