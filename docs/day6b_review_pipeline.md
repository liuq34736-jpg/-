# Day 6B：384 爻条件审核辅助流程

日期：2026-10-09。版本：`condition_review_tools_v1`；新批记录：`moving_line_condition_review_batch_v2`。
离线规则语义继续引用 `traditional_condition_synthesis_v1`。本轮不新增网页路由、生产签名、AI 请求或历史写入。

## 保护与输入

Day 6A 回退提交：`00f613af50fbd46fadc2f097b1ff4b098a71de7c`，原分支仍保留。新分支 `day6b/condition-review-tools`。
275 个原跟踪文件（含原 24 条记录）逐字节保护；生产 157 个冻结文件、509 个签名缓存及 42 条历史均无变化。
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

在项目根目录使用 `.venv\Scripts\python.exe -B -X utf8`：

```powershell
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6b_collect_candidates.py
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6b_review_cli.py table
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6b_review_cli.py worksheet --targets 1:2 2:1
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6b_offline_acceptance.py all
.\.venv\Scripts\python.exe -B -X utf8 scripts\day6b_integrity_check.py
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
