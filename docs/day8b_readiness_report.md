# Day 8B：准备就绪报告

日期：2026-10-10。Day8A回退点 `16d2809`，本轮开始工作区干净。独立准备分支 `day8b/real-quality-preparation`。

**结论：测试准备完成；真实AI质量未验证；付费执行尚未获授权。**

```text
PREPARATION_COMPLETE = true
PAID_RUN_AUTHORIZED = false
READY_TO_SEND_PAID_REQUESTS_NOW = false
REAL_AI_QUALITY_ACCEPTED = false
PRODUCTION_APPLICATION_ENABLED = false
```

## 1. 五份Day8A交付的核对

已读全部五份文件，并对照实际代码与新一轮离线结果；没有直接沿用文档“通过”结论。

| 文件 | 核对内容 | 当前结论 |
| --- | --- | --- |
| day8a_quality_design.md | 传统运输取消、展示投影、离线应用边界 | 与代码一致；传统取消有新实际回环证据；新AI HTTP取消未实现 |
| day8a_failure_regressions.md | 旧失败正文、时间窗口、事实/保证/源范围反例 | 7条旧真实摘录纳入fixture；已知失败及新增检查再次30/30，不证明任意语言无绕过 |
| day8a_interpretation_contract.md | 输入封印、四角色、来源/条件、独立receipt与渲染 | 约束存在于代码，六项true及score≥3未降低；语义正确性仍需要真模型＋独立原文审查 |
| day8a_offline_test_results.md | 原458、取消、生产完整性；Mock是否夸大 | 再次458/458；文档明确非实时AI质量，未冒充真实批准率 |
| day8a_next_steps.md | 未实现项目、真实预算 | 曾拟3次/例，与实际2个协议槽位不一致；完整证据远超2,000/请求，本次仅在新预算修正 |

## 2. 代码边界实际证据

| 核对项 | 位置与实际执行 |
| --- | --- |
| 受控输入 | `trusted_input.py`只接受固定ManualInput/TimeInput，调用原只读worker；原签名验证后签发输入；问题从计算参数排除 |
| 冻结Frame/来源/资格 | `contract.build_request`要求真实受控类型，Frame digest/role/批准状态/可用来源匹配；资格由固定Day7A引擎取得 |
| 问题锚定 | `validate_span`严格验证原问题字符下标与正文；不允许目标/疑问/转述成为既定事实；明确未来窗口不许标missing |
| 来源与条件 | `validate_draft`检查合法原子索引、准确source集合、全部Frame及Day7A limit ID；Q14固定范围hold及其绑定缺失/变化即回退 |
| 安全边界 | 标准化后检测已知事实/方向/资格修改、隐含保证、时间预测、条件认定、秘密/HTML等；schema extra=forbid |
| 独立核验 | `validate_verdict`绑定完整草稿digest、原请求、Frame/evidence/limit，六项全true、score≥3；候选与审核不能是同一个对象 |
| 输出 | `run_offline`用原Frame/条件渲染，应用独立标识；失败BASE_FALLBACK；始终production_approved=false/history_written=false |

**重要限制：** 上述ID/字段 gate 和已知词表不是任意中文语义证明。只凭reviewer的true/分数仍会误判；因此计划对最多24组应用独立读原文/完整条件。短Frame的原典隐含条件、未知事实同义表达和同厂商相关错误仍待真实验收。没有降低门槛或自动新增资格。

另外，QualityRequest虽为frozen dataclass，其payload仍是可变dict，封印可以发现改动但不是深层不可变；现有真实模型无法直接修改Python内存，不过未来运输适配器必须仅使用校验后的白名单序列化副本，调用后再校验封印，不能把该dict交给可修改的外部代码。此为接口实现前置要求，本轮未修改契约。

## 3. 超时、取消与并发

已读 `execution.py`、service、ASGI middleware及共享Vite取消处理器。网页不再使用180秒批量运输；20秒worker、22秒request、25秒前端与2秒清理政策没有改变冻结算法。仅清理请求自己启动的进程，进程退出后再释放两格并发槽，异常不重试。

本轮重新执行原真实回环HTTP探针，报告重定向到新文件，未覆盖Day8A证据：

| 检查 | 结果 |
| --- | --- |
| 直连ASGI断开 | 自有worker已回收，两槽释放；约0.061秒 |
| 共享Vite代理断开 | 自有worker已回收，两槽释放；约0.061秒 |
| 压缩0.2秒期限 | HTTP504，约0.264秒，一次启动、无重试、两槽释放 |
| 临时服务停止 | 通过；未改5173/8765或删除其他进程 |

合计 **4/4通过**，`day8b_cancellation_recheck_results.json`。探针使用明确的测试sleeper和临时127.0.0.1端口，不是生产卦象计算性能或未来真实AI取消证明。OS不可中断I/O等仍不能保证硬实时清理；新AI运输必须独立测试，不能盲目放大超时后宣称已解决。

## 4. 本轮新核验结果

| 项目 | 结果 |
| --- | --- |
| 全部现有单元测试 | **458 collected / 458 passed / 0 failed / 0 skipped** |
| 旧真实失败及对抗/Mock控制 | **30/30检查通过**；其中7条旧真实样例已拒绝 |
| 六例输入 | 6/6取得四角色批准Frame、可靠来源、原资格；3 bounded/1 branch_unresolved/2 unreviewed；已知hold 0 |
| 新增单元测试 | 0；新增的是准备计量/复核脚本，不增加业务能力 |
| Day8A已有416个文件 | 本轮复核前后SHA一致；最终Git差异另外确认不修改任何已有文件 |
| 生产157关键文件 | 与原保护基线一致 |
| 原签名缓存509文件 | 与原基线一致 |
| 旧历史42条 | schema、每行SHA、SQLite文件SHA均不变，只读连接 |
| 原384Frame/Day6A6B目录 | 未编辑；生产关键文件/签名缓存基线及已有文件差异检查通过 |
| API真实质量/Token/latency | **未验证 / unavailable**；本轮付费请求0 |
| 新浏览器/build/lint验收 | 本轮未重复执行；业务前后端没有改动，Day8A结果只作为先前证据 |

机器记录：`day8b_recheck_results.json`、`day8b_failure_recheck_results.json`、`day8b_cancellation_recheck_results.json`、`day8b_preparation_results.json`。矩阵/Chrome检查不累加到458单元测试，本轮未冒称完整重跑旧Streamlit872项。

## 5. 付费测试前置清单

| 状态 | 项目 |
| --- | --- |
| 已完成 | 六个固定合成问题、事实参考片段、原资格/计算/Frame/源指纹、逐例报告字段、来源抽查及停止准则 |
| 已完成 | 现有离线gate/独立回执/fallback再验证；标准解读及冻结结果不变 |
| 已测量 | 官方离线Tokenizer完整证据输入143,909；中心估计168,509；预留237,824 |
| 待用户批准 | 6例、最多12请求、0重试、250,000 Token、US$0.15；18次外部最高边界不自动用满 |
| 待实现及Mock验收 | 隔离的真实候选/审核运输、白名单wire投影、严格schema解析、安全异常、usage计量、总预算原子预留、串行截止/取消和资源清理 |
| 未验证 | 当前账户余额/凭据有效性、新schema厂商响应、真实意图/应用/审核语义、费用与耗时 |
| 不在本轮范围 | 正式网页AI正文、生产批准/专属签名缓存/历史写入或发布 |

**当前不能直接发送六例请求。** 用户预算批准与安全运输实现验收缺一不可；本轮不拿Day3固定诊断、旧生产问事服务或任意自由prompt绕过。

## 6. 仍保留的风险

1. 真实模型可能曲解原条件、补造事实或使用同义预测；receipt全true不足以证明来源一致，必须独立源审查。
2. 保守gate会误拒绝，包括带触发词的否定提醒；本轮照实记录，不降低门槛追求批准率。
3. 旧Q14局部hold保持有效，不是全库隐含条件修复；未审核328爻不自动扩大综合资格。
4. 真实运输、AI并发清理和全局费用执行器缺失；离线预算不是厂商账户硬上限。
5. 旧braces 1 high告警仍保留，本轮未重新执行依赖审计或更改依赖；只运行本机，不公开部署。
6. 新应用专属生产签名/cache/history尚未实现；42条旧历史只能保持原样，不能用它声称新AI正文可历史回放。

## 7. 交付及停止

- `docs/day8b_test_plan.md`
- `docs/day8b_quality_rubric.md`
- `docs/day8b_api_budget.md`
- 本报告

辅助脚本及机器结果只用于复核；Tokenizer及临时依赖在runtime内、未进入Git。没有更改生产算法、原Frame/古籍、审核目录、历史或Day8A业务代码。

**到此停止，等待用户明确批准真实测试预算。** 未获批准不执行任何付费调用、不把测试稿显示给普通用户。
