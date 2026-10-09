# Day 6B：实际测试结果

## 最终运行

| 检查 | 通过 | 失败 | 跳过 |
| --- | ---: | ---: | ---: |
| 新项目全部单元测试 collected=357 | 357 | 0 | 0 |
| 受保护生产只读回归 | 99 | 0 | 0 |
| 全量冻结组合计算、四角色 Frame | 384 / 384 | 0 | 0 |
| 原 384 动爻签名重新校验 | 384 / 384 | 0 | 0 |
| 新批逐条绑定/重复输出/输入不变 | 32 / 32 | 0 | 0 |
| 旧 71 个 Day 6A 结果哈希逐字回归 | 71 / 71 | 0 | 0 |

保留原 274 项，新增 **83 项**。测试包含候选状态隔离、完整提取、条件遗漏、原义扩大、源文 hash/quote/offset、Frame 变化、伪造 receipt、伪造 catalog、任意 rulebook、分支条件 ID、无资料/无规则、安全 guard、重复输入与旧目录保留。

第一次验收中新增测试初始化漏传严格模型的 input_mode，已补齐测试与试点请求字段；来源排除测试另检出资格读取未排除体用基础不可用的情况，已在新工具拒绝该情况。上述修复均只涉及 Day 6B 新文件。最终全部重跑，不改原 274 项和旧来源门槛。

## 安全与完整性

- 原 signature 篡改拒绝：True；生产写入/数据库/网络 guard 探针全部拒绝。
- Day 6A 275 个跟踪文件、原 24 条审核记录：不变。
- 冻结生产 157 个文件、签名缓存 509 个：不变。
- 原 SQLite 42 条：schema、全部行 hash、文件 SHA-256 不变。
- 真实 AI 请求 0；生产写入 0；新正式网页功能 0。

## 机器可读结果

- [unit](day6b_unit_results.json)
- [legacy](day6b_legacy_results.json)
- [matrix](day6b_matrix_results.json)
- [安全探针](day6b_probes_results.json)
- [32 新例与 71 旧例](day6b_batch_results.json)
- [文件与历史完整性](day6b_integrity_results.json)

测试计数分别列示，不把384组合、签名和试点重复相加称作 unit tests。
