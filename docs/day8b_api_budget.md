# Day 8B：API流程与待批准预算

日期：2026-10-10。**此预算尚未获付费执行授权。当前0次付费请求、0新增计费Token。**

## 1. 实际流程核对

| 内容 | 当前代码实际状态 |
| --- | --- |
| QuestionIntent | 是 ApplicationDraft 的字段，在候选请求中提取，没有独立 intent Provider |
| 候选 | `CandidateProvider.generate(QualityRequest)`，目前只有离线接口/替身 |
| 独立审核 | `IndependentReviewer.review(request,draft)`，单次独立接口/替身 |
| 本地拒绝 | 在审核前先 validate_draft，失败即回退，不消费审核请求 |
| 正式渲染 | 程序从原Frame/限制取传统文字，应用独立标识；不让模型生成冻结事实 |
| 真实DeepSeek | `DeepSeekConnectivityProvider.check_connection()`仅固定诊断，max_tokens=32；不能执行问事测试 |
| 自动重试 | 现有诊断和离线管线均无；拟议质量测试同样0 |
| 新全局费用/Token执行器 | **尚未实现**；本轮仅提供预留算法与验收要求，不宣称已有保护 |

Day8A下一步文件曾提“意图＋草稿＋审核”每例3请求/每次2,000tokens，那是未执行提案，**与实际协议槽位及完整证据尺寸不一致**。本次修正为每例最多2次，不修改Day8A文档或契约、不删证据、不加第四步生成。

## 2. 固定配置及申请范围

- Provider `deepseek`；model `deepseek-flash`；endpoint `https://api.deepseek.com/chat/completions`。
- 只在服务器受控配置读取凭据；未主动核验或保存真实Key，未向运行中的服务调用状态/诊断接口。既有单元测试涉及配置读取，本轮复核脚本显式供应合成凭据，避免Windows用户环境回退；不输出或记录真实Key。当前账户额度、当前凭据有效性及新schema厂商兼容性 **未验证**。
- 六例串行，最多 **12次实际请求**：candidate6、reviewer最多6。严格小于用户提出的18次最高边界；不把剩余额度用于重试、修JSON、重生成、预热或换模型。
- 每次非流式、固定model、关闭thinking，JSON object响应；严格Pydantic schema由本地执行，不能把厂商JSON模式当作schema已验证。
- Candidate max_output_tokens=4,096；Reviewer=3,072。保持Day8A字段/门槛不变，只在计划中给足固定结构输出空间。

## 3. 离线计量方法

用六例实际固定worker结果和受封印QualityRequest，规划白名单wire投影：完整四Frame原子/conditions/cautions、来源正文、Day7A判断/条件/分支和冻结事实全部保留；只排除内部receipt/封印及重复来源副本。没有截断原典、改写来源或只发送有利段落。

计量模板在 `scripts/day8b_prepare.py`：候选含完整context及现有ApplicationDraft schema；审核含相同原依据、完整草稿尺寸占位及IndependentVerdict schema。审核看到草稿是职责所需，但不看到生成器对话、推理、自评分。真实执行前必须将占位换成原封不动的实际草稿，重新测量。

使用DeepSeek官方公开离线 tokenizer，直接本地 `Tokenizer.from_file`，未执行下载示例的 `trust_remote_code`。公开文件下载不是模型请求。官方也注明离线估算与API实际usage可能不同。[官方Token说明及下载入口](https://api-docs.deepseek.com/quick_start/token_usage/)。

| 项目 | 数值/说明 |
| --- | --- |
| 官方下载URL | https://cdn.deepseek.com/api-docs/deepseek_v4_tokenizer.zip |
| ZIP SHA256 | e7310d1dafe0a86d8a5629fe78a7c763760f651db9b8682718a1781dcd6fe495 |
| 工具 | tokenizers==0.22.1，安装在被Git忽略的runtime/day8b-budget/lib；未改变项目venv/requirements |
| 测量对象 | 两条messages的content，不把它宣称为厂商完整chat template计费精确值 |
| 审核占位稿 | 只模拟结构/文本长度，非候选、非批准解释，不送模型、不进资料库 |
| 输入预留 | 内容计量×1.15＋256包装裕量，按256向上取整；审核再加4,096以覆盖实际草稿尺寸变化 |
| 典型输出估计 | 每例candidate2,300、reviewer1,800，合计4,100；是预算假设，不是实测usage |

## 4. 逐例精确预留表

| 案例 | Candidate内容Token | Reviewer内容Token（占位草稿） | 两次输入预留 | 输出上限 | 合计预留 |
| --- | ---: | ---: | ---: | ---: | ---: |
| B01 随六二 | 11,822 | 12,854 | 33,280 | 7,168 | 40,448 |
| B02 观六四 | 12,135 | 13,187 | 34,048 | 7,168 | 41,216 |
| B03 贲初九 | 10,699 | 11,636 | 30,720 | 7,168 | 37,888 |
| B04 屯九五 | 12,534 | 13,557 | 34,816 | 7,168 | 41,984 |
| B05 乾上九 | 11,073 | 12,180 | 31,488 | 7,168 | 38,656 |
| B06 未济初六 | 10,610 | 11,622 | 30,464 | 7,168 | 37,632 |
| **合计** | **68,873** | **75,036** | **194,816** | **43,008** | **237,824** |

实测内容输入合计143,909；加典型输出24,600，中心估计 **168,509 Token**。预计约16万～19.5万（完整六例、未提前拒绝），其余预留覆盖包装与输出差异。不能把“237,824预留”称作实际使用，也不承诺一定完成所有12次。

## 5. 价格及费用

官方当前列 `deepseek-flash` 对应 DeepSeek-V4.1-Flash。预算统一采用较高的峰值、输入缓存未命中费率：输入每百万Token **US$0.30**、输出 **US$1.20**；不计缓存/时段优惠。价格核对日2026-10-10，实际调用前需重新核对，不自动替换模型。[DeepSeek官方模型与价格](https://api-docs.deepseek.com/quick_start/pricing/)。

| 费用项 | 计算 | 美元 |
| --- | --- | ---: |
| 中心预计 | (143,909×0.30＋24,600×1.20)/1,000,000 | 0.072693 |
| 本表预留 | (194,816×0.30＋43,008×1.20)/1,000,000 | 0.110054 |
| **申请全局费用保护上限** | 独立费用账本，输入/输出分别核算；不依赖优惠 | **0.15** |
| **申请全局Token保护上限** | 预留与实际usage合并控制 | **250,000** |

价格单位是美元，不含换汇/账户活动优惠，未查账户余额。实际费用以厂商计费为准。上述金额是拟议预算，**不是已支付费用或已生效的账户级消费限制**。

## 6. 获批后执行器必须具备的保护（目前未实现）

1. 每次发出前原子预留：`已结算usage + 未结算预留 + 本次输入预算 + max_output` 不超过250,000；费用用Decimal按最坏峰值cache-miss输入/输出分别预留，不超过US$0.15；请求计数不超过12。前置条件不满足不发送。
2. 实际草稿到达后，审核prompt重新离线计量；若超该phase预留，**跳过审核、回退**，不截断条件或自动扩大上限。未知模板/新价格不满足预算假设则先停止。
3. HTTP返回usage按白名单读取prompt/completion/total及可用cache字段；只在一致、合理且不超过预留时结算释放差额。计费不明、缺失usage、超预留、超时后可能仍已计费或价格变化：保留最坏预留并停止后续付费请求，不能按0计算。
4. 禁SDK/网络/应用层自动重试；遇到schema、finish_reason非stop、空content、HTTP错误、timeout不修补，不重复发送。取消不能视作厂商没有计费。
5. 固定HTTPS、禁所有3xx跟随、不使用环境代理、不向其他origin转发凭据；复用Day3安全运输原语但不调用其固定诊断正文或扩大其功能。
6. 本地隔离测试执行器每次网络socket timeout20秒、请求总期限22秒、清理预留2秒、每例50秒、API批次总期限300秒；一次只运行一个模型任务。设计必须通过运输替身的超时/断连/cleanup测试才启用；不能把传统worker已有取消测试当成AI HTTP已取消的证据。
7. 人工式来源审阅时间不计模型耗时，不需额外DeepSeek请求。严重问题触发全批停止；未执行例单列，不为完成六例自动重启。
8. 仅保存用途、固定provider/model、安全HTTP状态、白名单usage/耗时/错误码及合成样例审核资料。禁止Key、认证头、完整请求头、异常原文、完整厂商envelope、内部封印/私有路径；不把真实用户问题写运行日志。

局限：离线Tokenizer和预留不能单独保证厂商账单硬上限；需要上述执行器、计费异常停止和调用前价格检查。若不能实现可靠预留/取消，不开始付费质量测试。已发请求是否被厂商处理，超时场景下不能从本地socket推断；必须计入预留而非免费重试。

## 7. 本轮实际执行与复现

实际仅下载公开官方Tokenizer、做离线计量及只读回归；没有调用DeepSeek模型API，没有输出或记录Key、连接生产SQLite写接口、签发应用批准或写入旧历史。计量记录见 `day8b_preparation_results.json`，模型usage和真实模型耗时为unavailable。

工具文件均位于本项目runtime，不进Git；已准备好时复现命令：

```powershell
.venv\Scripts\python.exe -B -X utf8 scripts/day8b_prepare.py
.venv\Scripts\python.exe -B -X utf8 scripts/day8b_recheck.py
```

这两个命令没有真实模型传输能力。不得把执行这些命令视为用户已经批准付费测试。
