"""Render the reviewed rulebook and actual offline results, not planned outcomes."""

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_bytes())


def save(name, text):
    (ROOT / "docs" / name).write_text(text.strip() + "\n", encoding="utf-8")


def cell(value):
    return str(value).replace("|", "／").replace("\n", " ")


def main():
    catalog = load("data/day6a_condition_reviews.json")
    audit = load("docs/day6a_frame_audit.json")
    cases = load("docs/day6a_cases_results.json")
    unit = load("docs/day6a_unit_results.json")
    legacy = load("docs/day6a_legacy_results.json")
    matrix = load("docs/day6a_matrix_results.json")
    probes = load("docs/day6a_probes_results.json")
    integrity = load("docs/day6a_integrity_results.json")
    examples = load("docs/day6a_examples.json")
    records = catalog["records"]
    source_url = "https://commons.wikimedia.org/wiki/File:NLC416-12jh005426-44577_%E6%A2%85%E8%8A%B1%E6%98%93%E6%95%B8.pdf"
    rule_rows = "\n".join(f"| {r['rule_id']} | {r['basis']} | {r['summary']} | {', '.join(r['dependencies'])} |" for r in catalog["rules"])
    save("day6a_condition_rulebook.md", f"""
# Day 6A：动爻条件与综合断卦规则

审查日期：2026-10-09。状态：**独立离线原型，待用户验收**。没有网页路由、生产写入、模型生成或付费 API 请求。

## 版本与范围

- 综合规则：`traditional_condition_synthesis_v1`。
- 独立动爻数据：`moving_line_condition_review_v1`。
- 审核记录：`offline_condition_review_receipt_v1`，只用于本轮离线审核追溯，**不是生产签名，也不是人工 verified**。
- 复用 Day 5 `traditional_judgement_v1`、冻结计算和原 `verified_semantic_frame_v1` 的读取/签名校验。
- 384 条原 Frame 均已只读审查；仅 {len(records)} 条另做逐条条件编码，其中 {sum(r['eligible'] for r in records)} 条可参与本轮离线裁决。其余 361 条不得自动取得资格。

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

本原型选择**保守并列约束、不评分、不强行选胜者**的项目执行政策。不同章节、起卦体系的优先级仍未统一；不声称这是唯一传统定法。[原扫描版本信息]({source_url})，新增页影像见 [p.57](day6a_source_pages/page-57.png)。

## 执行规则表

| Rule ID | 分类 | 执行内容 | 保留的 Day 5 来源规则 |
| --- | --- | --- | --- |
{rule_rows}

## 四类结果与范围

- `favorable`：有条件的规则层偏有利，不是现实成功。
- `adverse`：有范围限制的规则层偏不利，克方衰时保留作用受限。
- `mixed`：主要依据存在未决张力，记录条件和优先级，不相加、投票或评分。
- `insufficient_evidence`：未审核、证据/签名失效、规则来源不足，或无法选定条件分支。

未审核者 `scope=structure_only`；体用基础仍保留在 `body_use_baseline`，但不提供全卦综合裁决。获得资格且能合成者 `scope=bounded_reviewed_synthesis`。任何结果的现实条件都未被程序确认，`is_final_outcome=false`。

## 数据约束

固定目录以 SHA-256 锁定，记录绑定 target、原 Frame 完整指纹、原签名记录 ID、source fingerprint 和原典 reference hash。条件/分支有逐项 `source_evidence_ids`、原文摘录、版本和范围。原 Frame 或原典内容变动，旧条件资格撤回。规则影像缺失/损坏则不执行依赖规则。

新审核层不修改任何生产 verification_status，不重新签发 Frame，不覆盖现代《周易译注》或旧历史。追加复核必须另开新数据/规则版本，不能把目前 23 条直接推广到全部 384 爻。
""")

    blocks = []
    for record in records:
        source_rows = []
        for requirement in record["source_requirements"]:
            ref = requirement["reference"]
            source_rows.append(f"| `{ref['evidence_id']}` | {cell(ref['text'])} | [{cell(ref['source_title'])}]({ref['url']})；{cell(ref['edition'])}；{cell(ref['volume'])}；{cell(ref['location'])} | {ref['verification_status']} |")
        atoms = "\n".join(f"| {a['id']} | {a['kind']} | {cell(a['text'])} | {cell(a['quote'])} | {', '.join(a['source_evidence_ids'])} |" for a in record["conditions"]+record["branches"])
        blocks.append(f"""
## {record['hexagram_name']}{record['line_name']}（{record['record_id']}）

资格：{'可供本轮离线条件裁决' if record['eligible'] else '尚不具备新裁决资格'}。effect=`{record['effect']}`。

核对结论：{record['summary']}

- 原 Frame ID：`{record['frame_id']}`。
- 原 source fingerprint：`{record['source_fingerprint']}`。
- 原签名记录：`{record['original_verification_record_id']}`。
- 新编码版本：`{record['rule_version']}`；审核方式：`{record['review_method']}`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
{chr(10).join(source_rows)}

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
{atoms if atoms else '| 无 | 待研究 | 未自动编入新极性层 | — | 原典与 Frame 保留 |'}
""")
    kind_counts = dict(Counter(a["kind"] for r in records for a in r["conditions"] + r["branches"]))
    save("day6a_source_review.md", f"""
# Day 6A：原典与动爻条件审查

本轮只有本地只读审核。没有重新生成、润色或修改已批准 Frame；没有改变古籍验证状态。

## 384 条 Frame 审查结果

- 签名通过：384/384。
- core_claims 原子：686；含独立 conditions 的爻位：41；含独立 cautions 的爻位：8。
- 原始逐项读取记录：[day6a_frame_audit.json](day6a_frame_audit.json)。全量可阅读清单：[day6a_frame_inventory.md](day6a_frame_inventory.md)。
- 这次逐条读取不等于自动取得吉凶裁决资格。新条件编码仅审查 24 条，23 条可用于本轮离线原型，1 条保留待研究；其余 360 条只有原 Frame 语义，不自动添加方向。

审查发现：条件可能在 core_claims 而非 conditions 中；免咎不等于成功；原文具体身份/行动语境不能套成用户事实。清单中也保留了既有 Frame 的表达疑点，例如解初六包含候选流程叙述，本轮只记问题、不改 Frame、不赋予新裁决资格。

## 本轮方法及可信状态

1. 使用 Day 4 固定 guarded worker 再执行原 proof / issue_frame 校验，读取 384 条 core/conditions/cautions。
2. 对列出的 24 条逐段核对现有可靠古籍原典字段、Frame 的语义及限制。原典本身继续使用其原 machine_verified/verified 状态。
3. 显式定义每条条件、范围和分支；自动构建器只绑定/核对引用、文本和指纹，**不自动生成方向**。
4. 运行独立规则/条件/来源约束测试；新 receipt 为本次离线编码审计记录，**不是人工 verified、不是原签名替代品**。

本轮并没有重新对 24 条原典做双轮扫描转录，未虚称新增古籍 machine_verified。其来源状态沿用先前已签名资料。这些新条件编码的语义审核属于**证据约束的项目编码，仍待本阶段验收**。

## 传统规则来源

《梅花易数》文明书局1925年本，国图藏，五卷，本地影像 232 PDF 页。[版本元数据]({source_url})。复查 p.55、58、90，并新查 p.57《先天后天论》；p.60、65 等 Day 5 来源与指纹原样复用。原扫描本路径：`D:\\算卦工具\\资料源\\公开古籍\\梅花易数_国图1925.pdf`。

新增 p.57 影像 SHA-256：`{catalog['priority_source']['sha256']}`。方法为 `direct_scan_visual_review`，不是生产逐字文本双轮转录；短摘录只作定位。不同优先级保留为 DISPUTED，乾坤无互继续 CONFLICT/REFERENCE_ONLY。没有把同一底本的电子文本当成独立扫描版本复核。

## 编码类别统计

统计对象是本轮显式定义的语义项，不是用关键词统计全部爻位吉凶：`{json.dumps(kind_counts,ensure_ascii=False)}`。

### 唯一保留的本轮未决编码

节上六：Frame 将“悔亡”写成“若能因此悔悟”的条件解释。现有爻辞/小象没有把该前提充分展开，本轮不据此构造转机规则。保留原 Frame，新的 record eligible=false，回退结构层。后续可研究古注和版本，不自动纠正文义。

## 逐项证据与条件

下表所有版本字形保持原样；例如宾/賔、久/乆、彚等不作静默统一，现代展示文本没有改动。
{chr(10).join(blocks)}
""")

    inventory_rows = []
    reviewed_keys = {(r["hexagram_id"],r["position"]):r for r in records}
    for row in audit["rows"]:
        frame = row["frame"]
        review = reviewed_keys.get((row["hexagram_id"],row["position"]))
        status = "已逐条审核" if review and review["eligible"] else "待研究编码" if review else "未审核极性，仅保留原 Frame"
        texts = [" ／ ".join(a["text"] for a in frame[f]) or "—" for f in ("core_claims","conditions","cautions")]
        inventory_rows.append(f"| {row['hexagram_id']}:{row['position']} {row['hexagram_name']}{row['line_name']} | {cell(texts[0])} | {cell(texts[1])} | {cell(texts[2])} | {status} |")
    save("day6a_frame_inventory.md", f"""
# 384 条已批准动爻 Frame 的只读审查清单

原文摘要来自原签名 Frame，未进行修正。空列只表示原数组为空，不表示没有前提。未审核项不得据该表关键词取得新裁决资格。原证据指纹和引用逐项见 [完整审查 JSON](day6a_frame_audit.json)。

| 爻位 | core_claims | conditions | cautions | 新条件编码资格 |
| --- | --- | --- | --- | --- |
{chr(10).join(inventory_rows)}
""")

    representative = cases["reviewed_representative_cases"]
    rep_rows = "\n".join(f"| {r['target']} {r['hexagram']}{r['line']} | {r['relation']} | {r['body_state']}/{r['yong_state']} | {'有' if r['eligible'] else '无'} | {r['direction']} | {r['scope']} |" for r in representative)
    directional = [r["hexagram"]+r["line"] for r in representative if r["eligible"] and r["direction"] != "insufficient_evidence"]
    alternatives = [r["hexagram"]+r["line"] for r in representative if r["eligible"] and r["direction"] == "insufficient_evidence"]
    save("day6a_engine_report.md", f"""
# Day 6A：离线引擎报告

## 已实现

独立包：[backend/traditional_conditions_v1](../backend/traditional_conditions_v1/)，不改 Day 5 包。入口 `ConditionalJudgementEngine.evaluate(ValidatedJudgementInput)`，复用旧 guarded adapter 与原签名校验，不接受外部任意 JSON 作为可信输入。

数据：[day6a_condition_review_definitions.json](../data/day6a_condition_review_definitions.json) 为明确逐条审核定义；[day6a_condition_reviews.json](../data/day6a_condition_reviews.json) 为绑定证据和 Frame 后的固定目录。没有生产接口、数据库迁移、缓存写入或 AI 调用。

输出包含：有条件传统倾向、体用基础与时令修饰、动爻审核记录、原典完整引用、互变阶段辅助、条件性主要张力、未决分支、规则来源和版本。原始 calculation、原 Frame core/conditions/cautions、来源状态均原样保留。

## 实际覆盖与不能判断的原因

- 384 条原 Frame 读取通过，24 条新条件核对，23 条获得本轮离线条件裁决资格。
- 下列 20 条可形成**有范围限制的综合倾向**：{'、'.join(directional)}。
- 以下 3 条证据可用但无法选定分支：{'、'.join(alternatives)}。仍保留来源条件及体用基础，不能给单一综合方向。
- 节上六因前提编码尚无足够支持仅保留结构层和原有语义。
- 其余 360 个未审核爻位没有新综合裁决资格；不是缺古籍或缺 Frame，而是缺逐爻条件/范围审核。
- 任何案例都没有程序认可的现实条件满足证据；这里的方向只是规则层分析，不是实际事件的终判。

## 必须验收的案例

### 观六四

{examples['guan_manual']['traditional_tendency']['summary']}

本卦观、六四、互剥、变否完全不变；用克体、体土平、用木衰、酉月金当令保持。新方向：`{examples['guan_manual']['traditional_tendency']['direction']}`，范围 `bounded_reviewed_synthesis`。宾参与的局部机会单独列为 favorable factor，但不是整件事反转依据。互剥土比和与变否乾金耗体作为辅助分歧，不再自动制造 mixed。

### 随六二

{examples['sui_manual']['traditional_tendency']['summary']}

本卦随、六二、互渐、变兑不变；体兑金、用震木、体克用、体旺用衰保持。新方向 `{examples['sui_manual']['traditional_tendency']['direction']}`，必须带“弗兼与”的取舍限制；没有利用关键词给整爻添加吉凶。

### 比和但动爻不利限制：乾上九

{examples['1:6']['traditional_tendency']['summary']}

比和基础有利与亢极不可久的警示形成条件性主要张力，输出 mixed，保留优先级争议，不推定用户已亢极。

### 用生体但有前提：讼九四

{examples['6:4']['traditional_tendency']['summary']}

不能用用生体替代复即命、渝安贞；现实前提未评估。

### 体用不利但条件性转机：比六二

{examples['8:2']['traditional_tendency']['summary']}

用克体不消失，贞吉、不自失的原爻条件亦保留；mixed 是未决规则张力，不作现实好坏裁定。

### 乾坤互卦与来源不足

乾、坤的冻结互卦仍按 v1 计算，原典“乾坤无互、互其变卦”继续 reference_only，不改变计算。缺规则影像、原签名无效、来源被排除等情况均已通过测试撤去条件资格；有结构则仅保留结构，不用别的资料补证。

## 24 条代表性案例（统一验收时刻 2026-09-24 19:45:35 +08:00）

| 对象 | 体用关系 | 体/用状态 | 条件资格 | 综合方向 | 范围 |
| --- | --- | --- | --- | --- | --- |
{rep_rows}

完整结构结果及逐项依据：[day6a_examples.json](day6a_examples.json)。当前标签定义与 Day 5 不同：旧版只综合结构/辅助，新版对未审核爻位不授予整体综合标签。不能把标签变化夸称为修正了算法。

## 完整性

Day 5 回退提交：`{integrity['day5_commit']}`；独立分支 `day6a/condition-adjudication-offline`。

Day 5 的 {integrity['day5_tracked_files']} 个 tracked 文件、生产 {integrity['production_files']} 个冻结文件、{integrity['signed_cache_files']} 个签名缓存文件均未改变；{integrity['history_rows']} 条历史的 schema、逐行 hash、数据库字节 hash 一致。完整记录：[day6a_integrity_results.json](day6a_integrity_results.json)。

## 明确尚未实现

其余爻位条件裁决、现实前提自动认定、唯一传统优先级、外应/克应、应期、专业问事断法、正式网页接入。未做前端构建/浏览器验收，因为前端及原路由完全未改；不能把本离线原型宣传为正式上线。
""")

    regression_rows = "\n".join(f"| {r['case']} | {r['hexagram']}{r['line']} | {r['cast_at']} | {r['day5_tag']} | {r['day6a_tag']} | {r['scope']} | {r['change_or_retention_reason']} | {'PASS' if all(r[k] for k in ('day5_result_matches_original_baseline','calculation_unchanged','input_unchanged','repeat_identical','four_original_frames_preserved')) else 'FAIL'} |" for r in cases["cases"])
    save("day6a_acceptance_results.md", f"""
# Day 6A：实际验收结果

测试日期：2026-10-09。全部离线；真实 AI 调用 0。此报告反映实际运行，不将规划当成完成。

## 结果汇总

| 检查 | collected / 范围 | passed | failed | skipped |
| --- | --- | --- | --- | --- |
| 新项目全部单元/适配层回归 | {unit['collected']} | {unit['passed']} | {unit['failed']} | {unit['skipped']} |
| 其中原 Day 5 测试 | 210 | 210 | 0 | 0 |
| 其中新增 Day 6A 测试 | {unit['collected']-210} | {unit['passed']-210} | 0 | 0 |
| 旧生产系统允许的只读回归 | {legacy['collected']} | {legacy['passed']} | {legacy['failed']} | {legacy['skipped']} |
| 冻结确定性 + 四角色 Frame 全量组合 | 384 | {matrix['passed']} | {matrix['failed']} | — |
| 原 71 真实规则输入回归 | 71 | {cases['passed']} | {71-cases['passed']} | — |
| 本轮 24 条逐项来源案例 | 24 | {cases['reviewed_cases_passed']} | {24-cases['reviewed_cases_passed']} | — |

来源约束、原 Frame 篡改拒绝、生产/新项目写入阻断、网络阻断、生产 SQLite 阻断探针：{'PASS' if probes['passed'] else 'FAIL'}。只允许测试 harness 的本地 asyncio plumbing，不允许 live 5173/8765 或外网。

以上 24/71/384 不是额外 unittest 数，不与 274 加总成虚构测试数量。现代资料、生产算法及历史均未修改；未执行付费或网页验收请求。

## 71 旧案例的实际分布

- Day 5：偏有利 {cases['day5_distribution'].get('favorable',0)}，混合 {cases['day5_distribution'].get('mixed',0)}，偏不利 {cases['day5_distribution'].get('adverse',0)}。
- Day 6A：混合 {cases['day6a_distribution'].get('mixed',0)}，偏有利 {cases['day6a_distribution'].get('favorable',0)}，偏不利 {cases['day6a_distribution'].get('adverse',0)}，综合证据不足 {cases['day6a_distribution'].get('insufficient_evidence',0)}。
- 新版 scope：有条件审核综合 {cases['day6a_scope_distribution'].get('bounded_reviewed_synthesis',0)}，仅结构层 {cases['day6a_scope_distribution'].get('structure_only',0)}。
- 52 个综合证据不足中，50 个未逐条审核，1 个节上六条件编码待研究，1 个已审核但条件分支未选。体用基础数据继续保留。
- 标签文字/范围发生变化 {cases['labels_changed']}/71；**71/71 旧 Day 5 输出 hash 与原报告完全一致**。因此改变来自独立新层，旧逻辑和结果没有改写。

不同版本范围不相同，不把该分布当作传统正确率、预测准确率或产品全覆盖率，也没有人为设定比例。

## 24 条代表性案例分布

混合 {cases['reviewed_direction_distribution'].get('mixed',0)}，偏有利 {cases['reviewed_direction_distribution'].get('favorable',0)}，偏不利 {cases['reviewed_direction_distribution'].get('adverse',0)}，证据/分支不足 {cases['reviewed_direction_distribution'].get('insufficient_evidence',0)}。

这 24 条中有 23 条得到新条件资格，但仅 20 条能形成有范围的方向，3 条分支未决，1 条资格待研究。不要以 384 条原 Frame 全覆盖推断新综合判断亦全覆盖。

## 复现命令

```powershell
Set-Location -LiteralPath 'D:\\算卦工具\\divination-web'
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6a_frame_audit.py
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6a_offline_acceptance.py all
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6a_integrity_check.py
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6a_write_reports.py
```

无需设置 AI Key。没有 Provider 调用。构建条件目录用 `day6a_build_review_catalog.py`，只是绑定已审定义，不自动推断语义；目录内容改变必须经过新审核版本和 pin，不能擅改当前批准范围。

## 逐例回归表

| Case | 爻位 | 时间 | Day 5 | Day 6A | 新范围 | 变化/保留原因 | 完整性与确定性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
{regression_rows}

机器结果：[unit](day6a_unit_results.json)、[legacy](day6a_legacy_results.json)、[matrix](day6a_matrix_results.json)、[probes](day6a_probes_results.json)、[cases](day6a_cases_results.json)、[integrity](day6a_integrity_results.json)。
""")
    save("day6a_next_steps.md", """
# Day 6A：未决事项与下一步

当前停在独立离线原型，等待本阶段验收。没有接入正式网页，也没有付费 API 调用。

## 本阶段可验收能力

23 条固定爻位的条件资格、明确来源和版本、范围限制、主要条件性张力/辅助分歧分离、未审核回退；24 条来源案例、71 条旧输入、384 冻结组合与完整性保护均已实际运行。

## 仍未解决

1. 节上六“悔亡”的前提解释：需要可靠古注核验；当前不重新批准、改写或撤销原 Frame，只不授予新裁决资格。
2. 屯九五、随九四、大过九四的分支：原典有不同适用范围，不能靠卦象/问句/金额自动确认是哪一支。
3. 先天/后天与体用/爻辞优先级：来源章节有不同说明，项目的保守并列约束仍是约定，不能宣传为唯一传统真理。
4. 乾坤互卦：保留原冻结计算和来源冲突；另版本研究，不在当前版本强改。
5. 其余 360 个未审爻位没有新极性/条件编码；加上节上六，共 361 个没有新裁决资格。不得借 384 Frame 完整率来自动扩张权限。
6. 现实条件始终 unknown：当前不判断用户的身份、行为、经历或事情阶段，不能把爻中条件当成用户事实。
7. 问事专业规则、外应/克应、应期和现实成败仍未实现；不得由临时 AI 断语替代。

## 建议顺序（未执行）

先验收当前 24 条记录与 6 类重点案例 → 对来源优先级争议另做版本化研究 → 如继续，逐条补下一小组条件审核、保留反例 → 再决定是否需要条件分支接口 → 另开页面接入验收。

将来上线只展示已取得对应版本资格的有条件判断，其他对象继续结构 fallback。旧 Frame、旧 receipt、旧历史和 Day 5 回退点全部保留；新增状态不能伪装为人工 verified 或原生产签名。
""")
    print(json.dumps({"reports":5, "inventory_rows":len(inventory_rows), "source_review_records":len(blocks)},ensure_ascii=False))


if __name__ == "__main__":
    main()
