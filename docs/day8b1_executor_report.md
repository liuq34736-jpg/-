# Day 8B-1：受控执行器交付

日期：2026-10-12。回退点 `0944d7d`，开始工作区干净；分支 `day8b1/budget-executor`。只新增独立工具、测试和本阶段报告，原业务代码及资料保持原样。

## 已完成

| 文件 | 职责 |
|---|---|
| backend/ai_acceptance_v1/policy.py | 固定DeepSeek/model、官方价格版本、请求/问题/Token/费用上限、usage白名单 |
| ledger.py | 原子预留、保守结算、跨进程串行、防重复dispatch、外部锚点、两批授权隔离 |
| prompts.py | 复用Day8B完整证据投影；深拷贝、封印检查、实际草稿重新计量 |
| transport.py | 隔离Mock/真实运输代码；自有进程取消/超时/回收；Key仅服务器且不打印 |
| executor.py | 固定六例、原计算及证据指纹绑定、本地约束、独立核验、原renderer、基础回退 |
| scripts/day8b1_acceptance.py | **Mock-only**启动、守护回归、完整性检查及机器结果 |
| tests/test_day8b1_budget.py | 上限、账本防删改、重启、并发、异常、取消、HTTP错误及脱敏 |
| tests/test_day8b1_executor.py | 固定真实冻结输入、完整问事契约链、严重失败停批及原义回退 |

没有修改FastAPI公开路由、普通网页、DeepSeek旧诊断、原契约/阈值、判断引擎、签名缓存或历史。

## 受控链路

固定人工卦象输入 → 原只读worker验证签名并计算 → 已批准Frame → Day7A固定资格及传统判断 → 受封印QualityRequest → 完整证据白名单投影 → 预算预留 → 单次候选 → 原validate_draft → 单次独立审核 → 原validate_verdict → 原deterministic renderer。

独立审核看同一原问题、全Frame、全原文/条件和候选，但不看生成器对话/推理。六项true及score≥3保持不变。Frame ID、来源集合、全部limit ID、草稿摘要必须绑定。新增固定测试的类别一致性检查没有放宽原门槛。

input在外部处理前拷贝；使用后再检查封印。即使受封印dict被篡改，回退也取最初可信基础文字，并停止后续调用，而不是从被篡改数据渲染。

`MOCK_CONTRACT_ACCEPTED`只是测试协议接受；将来真实结果也仅为`TEST_CONTRACT_ACCEPTED`。两者始终 `production_approved=false / history_written=false`。对普通用户的正式AI正文没有新接入。

## 当前范围与不足

1. 执行器和HTTP运输用替身/进程Mock验收，实际DeepSeek schema、usage字段、耗时、事实/语义质量**未验证**。
2. 未创建或授权本轮真实预算，付费请求0；没有读取或检查真实Key内容/有效性。
3. 第一批Mock有独立报告；第二批的预算与分支仅用临时账本单元模拟，不是实际第二批授权。
4. 独立模型全true也可能语义误批；后续仍须按Day8B rubric逐条读原文审查，不能以Mock流畅性或模型自评分代替。
5. 保守旧gate对B06“只有一个想法”的reported片段误拒绝，保留安全回退；未修改旧gate或原事实标签来凑通过率。
6. 不新增384爻资格、不修改原Frame。bounded、branch_unresolved、unreviewed三种范围保持原有状态。
7. 服务只维持既有本地隔离；本轮没有启动公开服务、新增历史写入或发布。

运行方式：

```powershell
cd D:\算卦工具\divination-web
.venv\Scripts\python.exe -B -X utf8 scripts/day8b1_acceptance.py
```

此命令只运行Mock和回归。再次运行会验证原Mock报告/账本并复用，不重复四次Mock运输，更不会转为付费请求。正式批准后仍需由受控服务器操作登记真实第一批授权，价格复核不得重置预算。

测试详见 `day8b1_test_results.md` 和 `day8b1_acceptance_results.json`；费用与状态边界详见 `day8b1_budget_policy.md`。完成本轮后停止，等待独立真实测试授权。
