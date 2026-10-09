# Day 6B：候选完整性与误批审计

重新读取 384 条原签名 Frame：384/384 通过原签名和原来源约束，与 Day 6A 清单完全一致。
共 737 个候选原子：core_claims 686、conditions 43、cautions 8。
自动取得裁决资格：**0**。原 conditions 非空 41 条、cautions 非空 8 条。

## 自动检查实际结果

384 个提取包全部机械完整。来源异文待范围复核 145 条；审核流程元话语提示 1 条。
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
