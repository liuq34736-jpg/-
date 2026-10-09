# Day 6A：动爻条件与综合断卦规则

审查日期：2026-10-09。状态：**独立离线原型，待用户验收**。没有网页路由、生产写入、模型生成或付费 API 请求。

## 版本与范围

- 综合规则：`traditional_condition_synthesis_v1`。
- 独立动爻数据：`moving_line_condition_review_v1`。
- 审核记录：`offline_condition_review_receipt_v1`，只用于本轮离线审核追溯，**不是生产签名，也不是人工 verified**。
- 复用 Day 5 `traditional_judgement_v1`、冻结计算和原 `verified_semantic_frame_v1` 的读取/签名校验。
- 384 条原 Frame 均已只读审查；仅 24 条另做逐条条件编码，其中 23 条可参与本轮离线裁决。其余 361 条不得自动取得资格。

## 五类语义，不能压成整爻吉凶

| 类别 | 数据形式 | 如何使用 |
| --- | --- | --- |
| 明确传统判断 | `traditional_judgement` + 源中明确方向 + 原文摘录 | 只保留原来的动作、时位或行为范围 |
| 前提条件 | `prerequisite` / `risk_condition` / `scope_selector` | 现实满足情况始终 unknown，不从问题、日期或卦象补推 |
| 行为提醒 | `behavioral_reminder` | 勿用、取舍等限制参与断语，但不自动贴整爻有利/不利 |
| 结果限制 | `outcome_limit` | 无咎、不能兼顾、不可久等不能升级为整件事成功 |
| 无法定向 | 分支 direction=`undetermined` 或 record 不可用 | 保留提醒、不同分支或结构 fallback，不猜极性 |

`conditions=[]` 只代表原 Frame 没有独立数组项目，**不代表原文没有条件**。每项编码由本条原典和已签名 Frame 明确绑定；引擎没有“吉/凶/利/悔”关键词分类器。

## 体用与旺衰

Day 5 五类关系基本倾向保持：用生体、体克用、比和为结构层有利；体生用、用克体为结构层不利。来源仍为《梅花易数》卷二《体用总诀》《人事占第二》，PDF p.60、65。

**旺衰只修饰同一关系**。体旺、体衰、生体方旺衰、克体方衰等 Day 5 qualifier 全部保留。区别在于不把克方衰额外算作一票“吉”，不让强弱修饰自动抵消基础关系。原书《衰旺论》p.90 支持这些限制，但没有给出定量抵消表。

## 主要依据、辅助依据与分歧

1. 主要依据：原体用关系及其时令限制，和**逐条获得离线审核资格**的动爻条件。
2. 本卦已批准语义提供当前背景，不另做未经审核的整体吉凶分类。
3. 动爻提供具体行为范围、前提、风险与转机；不能去掉“贞”“艰”“愬愬”“有孚在道以明”等限制。
4. 互卦提供内部过程；变卦提供后续结构方向。上下卦对原体的生克仍沿用 Day 5 比较，始终标为辅助。
5. 互与变不同方向：`auxiliary_phase_divergence` / `between_auxiliary_phases`，**不自动触发 mixed**。
6. 具体动作有利与整件事结构不利不一定是同范围冲突。例如观六四“利用宾于王”只支持宾参与这一角色，不自动反转用克体。
7. 同范围的主要依据出现相反方向：记录 `primary_conditional_tension`，保留两种优先解释；mixed 是**规则的条件性张力**，不是已经观察到现实冲突。
8. 不同适用条件的分支未能选择：`insufficient_evidence`。不把“小贞/大贞”等不同分支假装同时成立，也不按金额推定其范围。

## 优先级的来源差异

- p.55《占卜总诀》提出成卦后先看周易爻辞，再看体用等。
- p.57《先天后天论》区分先天、后天，先天不甚用爻辞，后天用爻辞兼用卦辞。
- p.58《卦断遗论》既说以体用为主，又列不拘体用的情形。

本原型选择**保守并列约束、不评分、不强行选胜者**的项目执行政策。不同章节、起卦体系的优先级仍未统一；不声称这是唯一传统定法。[原扫描版本信息](https://commons.wikimedia.org/wiki/File:NLC416-12jh005426-44577_%E6%A2%85%E8%8A%B1%E6%98%93%E6%95%B8.pdf)，新增页影像见 [p.57](day6a_source_pages/page-57.png)。

## 执行规则表

| Rule ID | 分类 | 执行内容 | 保留的 Day 5 来源规则 |
| --- | --- | --- | --- |
| TJ6-ELIGIBILITY | PROJECT_CONVENTION | 只有固定审核目录、原 Frame 签名及对应证据仍有效的爻位可参与条件裁决。 | TJ-SEMANTIC-BOUNDARY |
| TJ6-CONDITION-UNKNOWN | PROJECT_CONVENTION | 不从问题或卦象推定现实前提已满足，全部条件保持未评估。 | TJ-SEMANTIC-BOUNDARY |
| TJ6-LINE-SCOPE | PROJECT_CONVENTION | 具体动作的利、免咎与行为提醒不能提升为整件事结果；保留原爻限制。 | TJ-TRADITIONAL-ROLES, TJ-SEMANTIC-BOUNDARY |
| TJ6-STRENGTH-QUALIFIER | PROJECT_CONVENTION | 旺衰修饰原生克关系，不作为相反一票；克方衰不等于关系已消除。 | TJ-STRENGTH, TJ-QUALIFIER |
| TJ6-AUXILIARY-DIVERGENCE | PROJECT_CONVENTION | 互中变终的不同阶段只作辅助分歧，不自动制造主要冲突。 | TJ-AUXILIARY, TJ-TRADITIONAL-ROLES |
| TJ6-PRIMARY-TENSION | PROJECT_CONVENTION | 体用基础与已审核同范围动爻方向相反时保留条件性张力；不用评分选胜者。 | TJ-PRIORITY, TJ-SEMANTIC-BOUNDARY |
| TJ6-ALTERNATIVE-SCOPES | PROJECT_CONVENTION | 不同条件分支未能选择时，不把它们当成同时成立的矛盾；总倾向保留不足。 | TJ-SEMANTIC-BOUNDARY |
| TJ6-PRIORITY-UNRESOLVED | DISPUTED | 先看爻辞、先天后天区分与以体用为主不拘体用并存；本原型采用保守的并列约束而非宣称唯一传统优先级。 | TJ-PRIORITY, TJ-TRADITIONAL-ROLES |

## 四类结果与范围

- `favorable`：有条件的规则层偏有利，不是现实成功。
- `adverse`：有范围限制的规则层偏不利，克方衰时保留作用受限。
- `mixed`：主要依据存在未决张力，记录条件和优先级，不相加、投票或评分。
- `insufficient_evidence`：未审核、证据/签名失效、规则来源不足，或无法选定条件分支。

未审核者 `scope=structure_only`；体用基础仍保留在 `body_use_baseline`，但不提供全卦综合裁决。获得资格且能合成者 `scope=bounded_reviewed_synthesis`。任何结果的现实条件都未被程序确认，`is_final_outcome=false`。

## 数据约束

固定目录以 SHA-256 锁定，记录绑定 target、原 Frame 完整指纹、原签名记录 ID、source fingerprint 和原典 reference hash。条件/分支有逐项 `source_evidence_ids`、原文摘录、版本和范围。原 Frame 或原典内容变动，旧条件资格撤回。规则影像缺失/损坏则不执行依赖规则。

新审核层不修改任何生产 verification_status，不重新签发 Frame，不覆盖现代《周易译注》或旧历史。追加复核必须另开新数据/规则版本，不能把目前 23 条直接推广到全部 384 爻。
