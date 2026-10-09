# Day 6A：实际验收结果

测试日期：2026-10-09。全部离线；真实 AI 调用 0。此报告反映实际运行，不将规划当成完成。

## 结果汇总

| 检查 | collected / 范围 | passed | failed | skipped |
| --- | --- | --- | --- | --- |
| 新项目全部单元/适配层回归 | 274 | 274 | 0 | 0 |
| 其中原 Day 5 测试 | 210 | 210 | 0 | 0 |
| 其中新增 Day 6A 测试 | 64 | 64 | 0 | 0 |
| 旧生产系统允许的只读回归 | 99 | 99 | 0 | 0 |
| 冻结确定性 + 四角色 Frame 全量组合 | 384 | 384 | 0 | — |
| 原 71 真实规则输入回归 | 71 | 71 | 0 | — |
| 本轮 24 条逐项来源案例 | 24 | 24 | 0 | — |

来源约束、原 Frame 篡改拒绝、生产/新项目写入阻断、网络阻断、生产 SQLite 阻断探针：PASS。只允许测试 harness 的本地 asyncio plumbing，不允许 live 5173/8765 或外网。

以上 24/71/384 不是额外 unittest 数，不与 274 加总成虚构测试数量。现代资料、生产算法及历史均未修改；未执行付费或网页验收请求。

## 71 旧案例的实际分布

- Day 5：偏有利 10，混合 60，偏不利 1。
- Day 6A：混合 5，偏有利 6，偏不利 8，综合证据不足 52。
- 新版 scope：有条件审核综合 20，仅结构层 51。
- 52 个综合证据不足中，50 个未逐条审核，1 个节上六条件编码待研究，1 个已审核但条件分支未选。体用基础数据继续保留。
- 标签文字/范围发生变化 63/71；**71/71 旧 Day 5 输出 hash 与原报告完全一致**。因此改变来自独立新层，旧逻辑和结果没有改写。

不同版本范围不相同，不把该分布当作传统正确率、预测准确率或产品全覆盖率，也没有人为设定比例。

## 24 条代表性案例分布

混合 6，偏有利 11，偏不利 3，证据/分支不足 4。

这 24 条中有 23 条得到新条件资格，但仅 20 条能形成有范围的方向，3 条分支未决，1 条资格待研究。不要以 384 条原 Frame 全覆盖推断新综合判断亦全覆盖。

## 复现命令

```powershell
Set-Location -LiteralPath 'D:\算卦工具\divination-web'
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6a_frame_audit.py
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6a_offline_acceptance.py all
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6a_integrity_check.py
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6a_write_reports.py
```

无需设置 AI Key。没有 Provider 调用。构建条件目录用 `day6a_build_review_catalog.py`，只是绑定已审定义，不自动推断语义；目录内容改变必须经过新审核版本和 pin，不能擅改当前批准范围。

## 逐例回归表

| Case | 爻位 | 时间 | Day 5 | Day 6A | 新范围 | 变化/保留原因 | 完整性与确定性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 乾初九 | 2026-09-24T19:45:35+08:00 | favorable | favorable | bounded_reviewed_synthesis | baseline_retained_with_reviewed_line_constraints | PASS |
| 2 | 坤六二 | 2026-02-20T12:00:00+08:00 | mixed | favorable | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 3 | 屯六三 | 2026-05-20T12:00:00+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 4 | 蒙六四 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 5 | 需九五 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 6 | 讼上九 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 7 | 师初六 | 2026-02-20T12:00:00+08:00 | mixed | mixed | bounded_reviewed_synthesis | reviewed_line_and_body_use_conditional_tension | PASS |
| 8 | 比六二 | 2026-05-20T12:00:00+08:00 | mixed | mixed | bounded_reviewed_synthesis | reviewed_line_and_body_use_conditional_tension | PASS |
| 9 | 小畜九三 | 2026-11-20T12:00:00+08:00 | adverse | adverse | bounded_reviewed_synthesis | baseline_retained_with_reviewed_line_constraints | PASS |
| 10 | 履九四 | 2026-04-20T12:00:00+08:00 | mixed | favorable | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 11 | 泰六五 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 12 | 否上九 | 2026-02-20T12:00:00+08:00 | mixed | mixed | bounded_reviewed_synthesis | reviewed_line_and_body_use_conditional_tension | PASS |
| 13 | 同人初九 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 14 | 大有九二 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 15 | 谦九三 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 16 | 豫九四 | 2026-09-24T19:45:35+08:00 | mixed | mixed | bounded_reviewed_synthesis | reviewed_line_and_body_use_conditional_tension | PASS |
| 17 | 随九五 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 18 | 蛊上九 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 19 | 临初九 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 20 | 观六二 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 21 | 噬嗑六三 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 22 | 贲六四 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 23 | 剥六五 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 24 | 复上六 | 2026-11-20T12:00:00+08:00 | favorable | mixed | bounded_reviewed_synthesis | reviewed_line_and_body_use_conditional_tension | PASS |
| 25 | 无妄初九 | 2026-04-20T12:00:00+08:00 | favorable | favorable | bounded_reviewed_synthesis | baseline_retained_with_reviewed_line_constraints | PASS |
| 26 | 大畜九二 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 27 | 颐六三 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 28 | 大过九四 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | bounded_reviewed_synthesis | alternative_scope_prerequisites_not_known | PASS |
| 29 | 坎九五 | 2026-11-20T12:00:00+08:00 | mixed | favorable | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 30 | 离上九 | 2026-04-20T12:00:00+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 31 | 咸初六 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 32 | 恒九二 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 33 | 遯九三 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 34 | 大壮九四 | 2026-11-20T12:00:00+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 35 | 晋六五 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 36 | 明夷上六 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 37 | 家人初九 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 38 | 睽九二 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 39 | 蹇九三 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 40 | 解九四 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 41 | 损六五 | 2026-09-24T19:45:35+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 42 | 益上九 | 2026-02-20T12:00:00+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 43 | 夬初九 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 44 | 姤九二 | 2026-11-20T12:00:00+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 45 | 萃六三 | 2026-04-20T12:00:00+08:00 | favorable | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 46 | 升六四 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 47 | 困九五 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 48 | 井上六 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 49 | 革初九 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 50 | 鼎九二 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 51 | 震六三 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 52 | 艮六四 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 53 | 渐九五 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 54 | 归妹上六 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 55 | 丰初九 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 56 | 旅六二 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 57 | 巽九三 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 58 | 兑九四 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 59 | 涣九五 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 60 | 节上六 | 2026-04-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | approved_frame_condition_not_explicitly_supported_for_new_directional_encoding | PASS |
| 61 | 中孚初九 | 2026-09-24T19:45:35+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 62 | 小过六二 | 2026-02-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 63 | 既济九三 | 2026-05-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 64 | 未济九四 | 2026-11-20T12:00:00+08:00 | mixed | insufficient_evidence | structure_only | line_not_individually_reviewed | PASS |
| 65 | 观六四 | 2026-09-24T19:45:35+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 66 | 观六四 | 2026-02-20T12:00:00+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 67 | 观六四 | 2026-05-20T12:00:00+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 68 | 观六四 | 2026-11-20T12:00:00+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 69 | 观六四 | 2026-04-20T12:00:00+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |
| 70 | 随六二 | 2026-09-24T19:45:35+08:00 | favorable | favorable | bounded_reviewed_synthesis | baseline_retained_with_reviewed_line_constraints | PASS |
| 71 | 观六四 | 2026-09-24T19:45:35+08:00 | mixed | adverse | bounded_reviewed_synthesis | strength_modifier_and_auxiliary_divergence_are_not_opposite_votes | PASS |

机器结果：[unit](day6a_unit_results.json)、[legacy](day6a_legacy_results.json)、[matrix](day6a_matrix_results.json)、[probes](day6a_probes_results.json)、[cases](day6a_cases_results.json)、[integrity](day6a_integrity_results.json)。
