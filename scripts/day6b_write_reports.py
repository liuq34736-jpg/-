"""Render six delivery documents from actual machine-readable acceptance artifacts."""

from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_bytes())


def save(name, text):
    (ROOT / "docs" / name).write_text(text.strip() + "\n", encoding="utf-8")


def write():
    catalog = load("data/day6b_condition_reviews.json")
    candidates = load("data/day6b_condition_candidates.json")
    inventory = load("docs/day6b_signed_frame_inventory.json")
    batch = load("docs/day6b_batch_results.json")
    unit = load("docs/day6b_unit_results.json")
    legacy = load("docs/day6b_legacy_results.json")
    matrix = load("docs/day6b_matrix_results.json")
    probes = load("docs/day6b_probes_results.json")
    integrity = load("docs/day6b_integrity_results.json")
    coverage = batch["coverage"]
    table = {tuple(r["target"]): r for r in batch["batch"]}
    flags = Counter(f for row in candidates["rows"] for f in row["inspection"]["findings"])
    atoms = sum(len(r["candidates"]) for r in candidates["rows"])
    counts = {f: sum(len(r["frame"][f]) for r in inventory["rows"]) for f in ("core_claims", "conditions", "cautions")}
    assert unit["failed"] == 0 and legacy["failed"] == 0 and matrix["failed"] == 0 and batch["passed"] and integrity["passed"]
    save("day6b_review_pipeline.md", f"""
# Day 6B：384 爻条件审核辅助流程

日期：2026-10-09。版本：`condition_review_tools_v1`；新批记录：`moving_line_condition_review_batch_v2`。
离线规则语义继续引用 `traditional_condition_synthesis_v1`。本轮不新增网页路由、生产签名、AI 请求或历史写入。

## 保护与输入

Day 6A 回退提交：`00f613af50fbd46fadc2f097b1ff4b098a71de7c`，原分支仍保留。新分支 `day6b/condition-review-tools`。
{integrity['day6a_tracked_files']} 个原跟踪文件（含原 24 条记录）逐字节保护；生产 {integrity['production_files']} 个冻结文件、{integrity['signed_cache_files']} 个签名缓存及 {integrity['history_rows']} 条历史均无变化。
输入只由固定的隔离子进程读取：原 corpus → 原 proof → 原 issue_frame 签名/证据验证 → 原 Frame。
子进程只传 SYSTEMROOT/WINDIR/PATH/TEMP/TMP，不读模型密钥；文件写入、SQLite、DNS、HTTP、外部子进程被原 guard 拒绝。

## 分层

```text
384 原签名 Frame + 原核验来源
    → 完整字面提取 core_claims / conditions / cautions
    → candidate（永不自动授予资格）
    → 机械完整性 / 精确来源范围检查
    → 单条源文与语义范围复核
    → 新版本离线 reviewed / disputed / insufficient_evidence 记录
    → 固定目录指纹 + 原 Frame/来源 + 原规则仍有效时，离线资格读取
```

`generate_candidates` 不按卦号、吉凶关键词或分数产生方向。core 原子保持 `unclassified_scope`；另外两类仅依照原数组分类为潜在限制。
工具另以若/或、勿/敬/惕、君子/小人/王事及无咎/未大失等定位词整理潜在前提、行为、范围与结果限制的原文字面位置；所有定位线索仍为 candidate，绝不由定位词判整爻吉凶或确认逻辑前提。
来源范围是原字段全文上下文，offset 为 Python Unicode code-point 索引；不伪称找到古文与白话一一对应译句。
每条保留 source_id、Frame ID、原审核 receipt ID、source_fingerprint、全体原限制与异文元数据。

## 四种审核状态

| 状态 | 含义 | 可否参与新条件裁决 |
| --- | --- | --- |
| candidate | 自动提取或未逐条复核 | 否 |
| reviewed | 逐条复核已完成，绑定固定离线目录 | 仅该条、该版本、该原证据范围 |
| disputed | 原 Frame 中存在待解释的语义范围问题 | 否 |
| insufficient_evidence | 新充分条件编码缺少可靠依据 | 否 |

reviewed 不等于人工 `verified` 或生产 `SEMANTIC_APPROVED`。新 receipt 仅为内容 SHA-256 完整性记录，`is_production_signature=false`。
生成候选、填写 worksheet、重算一份 receipt 或手工把 status 写成 reviewed，都不能绕过固定目录的整体 hash。
既有 24 条不迁移/覆盖；新目录仅覆盖本次 32 条。新旧表合并只是审查索引，不启用新生产判断。

## 条件门槛

原签名、原全文、全部原子、全部源字段 hash、原规则扫描页、逐条精确 quote 和条件 ID 必须全部有效。
所有现实条件保持 unknown。相互替代的分支分别绑定自己的条件，不能当作同时为真的矛盾或投票。
旺衰仍修饰原体用关系；互变仍为不同阶段辅助；不输出评分、概率、实际应期或必然成败。

## 本地命令

在项目根目录使用 `.venv\\Scripts\\python.exe -B -X utf8`：

```powershell
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6b_collect_candidates.py
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6b_review_cli.py table
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6b_review_cli.py worksheet --targets 1:2 2:1
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6b_offline_acceptance.py all
.\\.venv\\Scripts\\python.exe -B -X utf8 scripts\\day6b_integrity_check.py
```

worksheet 仅固定路径导出未审核对象（最多 48 条），无自动批准命令。上面两条 worksheet target 只是未来维护示例，本轮未审核它们。
`day6b_build_review_catalog.py` 只绑定已经逐条写明的试点定义；它不是“处理所有候选并自动 approved”的批任务。
未来追加需新批记录/新版本、逐条复核及独立验收；不能覆盖现有批记录，也不能更新旧 Frame 或历史。

## 机器可读交付

- [384 签名复核清单](day6b_signed_frame_inventory.json)
- [737 个候选原子](../data/day6b_condition_candidates.json)
- [新 32 条离线记录](../data/day6b_condition_reviews.json)
- [384 条审核状态表](day6b_review_table.json)
- [实际试点及原 71 例回归](day6b_batch_results.json)
""")
    save("day6b_candidate_audit.md", f"""
# Day 6B：候选完整性与误批审计

重新读取 384 条原签名 Frame：384/384 通过原签名和原来源约束，与 Day 6A 清单完全一致。
共 {atoms} 个候选原子：core_claims {counts['core_claims']}、conditions {counts['conditions']}、cautions {counts['cautions']}。
自动取得裁决资格：**0**。原 conditions 非空 {inventory['nonempty_conditions']} 条、cautions 非空 {inventory['nonempty_cautions']} 条。

## 自动检查实际结果

384 个提取包全部机械完整。来源异文待范围复核 {flags.get('source_variant_requires_scope_review', 0)} 条；审核流程元话语提示 {flags.get('process_meta_text_requires_scope_review', 0)} 条。
potential_signals 将若/或、勿/敬/惕等原字位置及完整上下文分类为潜在前提、行为提醒、结果限制和不同范围。语义条件是否成立一律 false/未确认；不会按吉/凶/利/悔生成方向。
这两种提示是审核线索，不是原 Frame 无效判定，不改任何已批准数据。
范围为“包含全部原子和已核验原文上下文”，不是“任意白话都已经被机器证明语义正确”。

## 可自动检出的失败

| 检查 | 处理 |
| --- | --- |
| 丢原 conditions / cautions / core 原子或限制数组 | omitted_original_atom_or_condition / omitted_or_changed_original_limits |
| 改候选文本、添未经绑定内容 | candidate_changed_or_expanded / unsupported_candidate_or_expanded_meaning |
| Frame / fingerprint / source hash 变化 | source_or_frame_binding_changed；离线目录资格拒绝 |
| 不可靠来源 / 未绑定 source ID / quote 不在精确范围 | 来源及 quote 校验失败 |
| 任意候选添加相反方向分支 | unreviewed_branch_claims，提示须复核分支范围，不直接判混合 |
| candidate 私自写 reviewed / eligible | unauthorized_candidate_promotion；不能作为可信 request |
| 伪造 receipt 或任意 catalog | 固定整体目录 hash 不符，拒绝资格 |

语义近义改写、古文省略条件、同一词在不同适用范围的矛盾不能靠上述字面检查可靠自动解决。
它们必须逐条复核，本轮将具体结论和 quote 写入独立离线记录；工具不声称具备通用自动语义裁决能力。

## 代表性候选

1. **蒙初六**：原 core 与 conditions 均完整提取，`以往吝` 未被省掉；新复核把限定正法用途与继续推行分成不同分支。
2. **乾九三**：conditions 原数组为空，但原典 `夕惕若厲无咎` 仍随候选全文保留。新条件编码不把勤勉提升为保证成功。
3. **恒九三**：保持 `恒/𢘆`、`徳/德` 两套见证，保存原 ID 和各自原文，不能归一后声称无异文。
4. **解初六**：原 Frame 包含“两个候选…”流程文字，工具提示该异常；新资格 held/disputed，原 Frame 与原签名不变。

具体 candidate_id、原文 offsets、source_id、版本、URL、卷次、位置及原限制均在 [候选 JSON](../data/day6b_condition_candidates.json)。
""")
    parts = ["# Day 6B：32 条新爻位逐条源文与语义复核", "",
             "方法：重新读取已签名 Frame 与其 machine_verified/verified 古籍字段，逐条对照核心语义、条件和范围。未重新 OCR 扫描，也未宣称新做原典双重转录。",
             "已存在的原来源核验/签名仍由原 issuer 重新验证；本报告是新增条件编码的离线复核，不是原文人工 verified。", "",
             "结果：reviewed 29；disputed 2；insufficient_evidence 1。29 条中 11 条保留分支未决；18 条可形成限定范围的裁决条件。", "",
             "覆盖五种体用关系：" + json.dumps(batch["relations"], ensure_ascii=False),
             "覆盖六个动爻位置：" + json.dumps(batch["positions"], ensure_ascii=False),
             "源文/Frame 方向与体用相反的条件性张力样本 8 条；不是已观测到的现实冲突，不自动升级整事件成败。", "",
             "## 逐例摘要", "", "| 爻位 | 体用 | 状态 | 离线资格 | 分支/范围 | 复核说明 |",
             "| --- | --- | --- | --- | --- | --- |"]
    for record in catalog["records"]:
        r = table[tuple(record["target"])]
        parts.append(f"| {record['hexagram_name']}{record['line_name']}（{record['target'][0]}:{record['target'][1]}） | {r['relation']} | {record['state']} | {'有' if record['eligible'] else '无'} | {record['readiness']} | {record['summary']} |")
    parts += ["", "## 三条未取得新资格及全部原因", "",
              "- 乾九四：`sufficient_condition_requires_unbound_commentary`；现有来源未直接支持把‘只要顺势’编码为充分条件。",
              "- 明夷上六：`generalized_causal_scope_not_supported_for_new_encoding`；特定爻象的失则不能直接推广为所有由盛转衰皆自因。",
              "- 解初六：`process_meta_atom_not_classical_semantics`；审核过程说明不是古籍语义。", "",
              "原 Day 6A 节上六仍为新条件依据不足，既有记录不改。其余未审核 328 条一律 candidate，不因源字段已签名而取得新裁决资格。", "",
              "## 每条完整对照"]
    for record in catalog["records"]:
        parts += ["", f"### {record['hexagram_name']}{record['line_name']}（{record['record_id']}）", "",
                  f"状态：{record['state']}；规则版本：{record['rule_version']}；现实条件：unknown。",
                  f"Frame ID：`{record['frame_id']}`；来源指纹：`{record['source_fingerprint']}`。", "",
                  "**原 Frame 原子（未修改）**", ""]
        for f in ("core_claims", "conditions", "cautions"):
            parts.append(f"- {f}：" + " ／ ".join(a["text"] for a in record["original_frame_snapshot"][f]) if record["original_frame_snapshot"][f] else f"- {f}：原数组为空，不推定无条件。")
        parts += ["", "**来源原字段与定位**", ""]
        for source in record["source_requirements"]:
            ref = source["reference"]
            meta = record["source_metadata"][source["evidence_id"]]
            parts += [f"- `{source['evidence_id']}`；source_id `{meta['source_id']}`；{ref['source_title']}，{ref['edition']}。",
                      f"  卷次 {meta['volume']}；位置 {meta['content_location']}；核验 {ref['verification_status']}；原页码未提供则保持 null。",
                      f"  URL：{meta['canonical_url']}", f"  原文字段：{ref['text']}"]
        parts += ["", "**逐条范围结论**", "", record["semantic_review_note"], ""]
        for atom in record["conditions"] + record["branches"]:
            parts.append(f"- `{atom['id']}`（{atom['kind']}）：{atom['text']}" +
                         (f"；方向 {atom['direction']}；仅绑定条件 {', '.join(atom['condition_ids'])}。" if "direction" in atom else "；未确认现实已满足。"))
            for quote in atom["source_quotes"]:
                parts.append(f"  原文范围 `{quote['evidence_id']}` [{quote['start']}, {quote['end']})：{quote['quote']}")
        parts.append("新条件与全部原子均已在本批复核；不把 source quote 的字面存在当作自动语义批准，整体目录已固定。")
    save("day6b_batch_review_report.md", "\n".join(parts))
    save("day6b_coverage_report.md", f"""
# Day 6B：覆盖率与未决项

## 实际覆盖

| 指标 | Day 6A | 本批新增 | 累计 |
| --- | ---: | ---: | ---: |
| 已逐条审核 | 24 | 32 | 56 |
| 离线资格 | 23 | 29 | 52 / 384（13.54%） |
| 有限定综合裁决条件编码 | 20 | 18 | 38 / 384（9.90%） |
| 有资格但适用分支未决 | 3 | 11 | 14 |
| 已审而不具新资格 | 1 | 3 | 4 |
| 尚未审核 | 360 | -32 | 328 |

恒等校验：38 + 14 + 4 + 328 = 384；52 = 38 + 14。
审核表状态为 reviewed 52、disputed 2、insufficient_evidence 2、candidate 328。
已审而未决/来源不足不算未审核，避免重复计数。

## 指标边界

“有限定综合裁决条件编码”是新旧离线目录具备该类输入资格的数量，**不是**宣称已运行升级后的综合断卦引擎或正式网页。
新目录只提供审核/绑定工具；原 Day 6A 引擎仍只认原 23 条资格，新 29 条未接入。
本批真实冻结请求 32/32 与原输入、原 Frame 一致；固定 71 个旧结果 SHA-256 为 71/71 完全相同。
潜在体用/动爻张力 8 条只保留限制，不把互变的反向关系误计为主要冲突。

## 无资格原因

新增三条具体原因见 [批次复核报告](day6b_batch_review_report.md)。
11 条新分支未决：坤六三、蒙初六、讼六三、师六五、否六二、大有九三、临六三、观初六、剥上九、夬九四、未济上九。
未知用户现实条件，不能因为目标覆盖率而擅自选分支、删除限制或放宽批准门槛。

原 Day 6A 条件与来源事实没有重生成，乾坤互卦争议继续保持原 reference_only / CONFLICT 处理。
""")
    save("day6b_test_results.md", f"""
# Day 6B：实际测试结果

## 最终运行

| 检查 | 通过 | 失败 | 跳过 |
| --- | ---: | ---: | ---: |
| 新项目全部单元测试 collected={unit['collected']} | {unit['passed']} | {unit['failed']} | {unit['skipped']} |
| 受保护生产只读回归 | {legacy['passed']} | {legacy['failed']} | {legacy['skipped']} |
| 全量冻结组合计算、四角色 Frame | {matrix['passed']} / 384 | {matrix['failed']} | 0 |
| 原 384 动爻签名重新校验 | 384 / 384 | 0 | 0 |
| 新批逐条绑定/重复输出/输入不变 | 32 / 32 | 0 | 0 |
| 旧 71 个 Day 6A 结果哈希逐字回归 | {batch['old_71_exact_results_preserved']} / 71 | 0 | 0 |

保留原 274 项，新增 **{unit['collected'] - 274} 项**。测试包含候选状态隔离、完整提取、条件遗漏、原义扩大、源文 hash/quote/offset、Frame 变化、伪造 receipt、伪造 catalog、任意 rulebook、分支条件 ID、无资料/无规则、安全 guard、重复输入与旧目录保留。

第一次验收中新增测试初始化漏传严格模型的 input_mode，已补齐测试与试点请求字段；来源排除测试另检出资格读取未排除体用基础不可用的情况，已在新工具拒绝该情况。上述修复均只涉及 Day 6B 新文件。最终全部重跑，不改原 274 项和旧来源门槛。

## 安全与完整性

- 原 signature 篡改拒绝：{probes['tampered_original_frame_rejected']}；生产写入/数据库/网络 guard 探针全部拒绝。
- Day 6A {integrity['day6a_tracked_files']} 个跟踪文件、原 24 条审核记录：不变。
- 冻结生产 {integrity['production_files']} 个文件、签名缓存 {integrity['signed_cache_files']} 个：不变。
- 原 SQLite {integrity['history_rows']} 条：schema、全部行 hash、文件 SHA-256 不变。
- 真实 AI 请求 0；生产写入 0；新正式网页功能 0。

## 机器可读结果

- [unit](day6b_unit_results.json)
- [legacy](day6b_legacy_results.json)
- [matrix](day6b_matrix_results.json)
- [安全探针](day6b_probes_results.json)
- [32 新例与 71 旧例](day6b_batch_results.json)
- [文件与历史完整性](day6b_integrity_results.json)

测试计数分别列示，不把384组合、签名和试点重复相加称作 unit tests。
""")
    save("day6b_next_steps.md", """
# Day 6B：未来网页回退设计（仅设计，未接入）

## 显示边界

| 可用状态 | 未来展示 | 不能做什么 |
| --- | --- | --- |
| 已有综合裁决资格且条件可表示 | 有范围限制的传统综合分析，列出来源和未知现实前提 | 不能显示必然成败、概率或擅自确认前提 |
| reviewed 但分支不明 | 分别列出分支条件及不能选定原因 | 不能按投票/打分选择分支 |
| 尚未审核 candidate | 已验证体用、生克、旺衰与基础卦义 | 不能按吉凶关键词把原 Frame 自动授予综合裁决资格 |
| 缺失合法来源或原签名无效 | 仅显示确定性结构与来源限制 | 不能让 AI/常识补原典条件或生成确定性结论 |
| disputed / insufficient_evidence | 不采用新的条件裁决；保留其余可靠结构与基础资料 | 不能把来源争议静默消掉 |

原 approved Frame 与新增条件审核资格是两层；新增层 disputed 不自动取消原批准，原来源/签名坏了才排除对应证据。
乾坤互卦争议继续按原 policy 保留，不重算互卦。源字段 `verified` / `machine_verified` 门槛不变。

## 后续验收建议

1. 人工式独立抽查本批 32 条的精确 quote、适用范围及异文保留。先确认审核工具和新目录，不追求剩余328条一次通过。
2. 另开阶段设计能并行读取旧/新固定目录的离线引擎，保持 Day 6A 的历史定义和回退点；本轮没有实施该集成。
3. 后续每批24–48条使用候选 worksheet，补明确来源或古注，再逐条审核；新版本写新目录，不覆盖本批或原24条。
4. 三个持留项分别研究乾九四充分条件的古注依据、明夷上六因果范围、解初六元话语处理。不得在本轮重写原Frame。
5. 网页接入须单独验收展示范围、无资格回退、旧历史不重解释、证据损坏不降门槛。

当前交付停留在离线辅助工具与一个32条试点。没有付费AI、生产数据库迁移、新页面或其他流派扩展。
""")
    summary = {"version": "day6b_acceptance_summary_v1", "collected": unit["collected"], "passed": unit["passed"],
               "failed": unit["failed"], "skipped": unit["skipped"], "new_tests": unit["collected"] - 274,
               "old_tests_preserved": 274, "coverage": coverage, "candidate_atoms": atoms,
               "signature_checks": 384, "matrix_combinations": 384, "integrity_passed": integrity["passed"],
               "real_ai_calls": 0, "web_integration": False}
    (ROOT / "docs/day6b_acceptance_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    write()
