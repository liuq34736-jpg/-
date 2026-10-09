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

《梅花易数》文明书局1925年本，国图藏，五卷，本地影像 232 PDF 页。[版本元数据](https://commons.wikimedia.org/wiki/File:NLC416-12jh005426-44577_%E6%A2%85%E8%8A%B1%E6%98%93%E6%95%B8.pdf)。复查 p.55、58、90，并新查 p.57《先天后天论》；p.60、65 等 Day 5 来源与指纹原样复用。原扫描本路径：`D:\算卦工具\资料源\公开古籍\梅花易数_国图1925.pdf`。

新增 p.57 影像 SHA-256：`0d384359b978345cb43a1b591900ebb77a66f9bb7200d48fe7c57c574c97db0c`。方法为 `direct_scan_visual_review`，不是生产逐字文本双轮转录；短摘录只作定位。不同优先级保留为 DISPUTED，乾坤无互继续 CONFLICT/REFERENCE_ONLY。没有把同一底本的电子文本当成独立扫描版本复核。

## 编码类别统计

统计对象是本轮显式定义的语义项，不是用关键词统计全部爻位吉凶：`{"prerequisite": 15, "behavioral_reminder": 2, "outcome_limit": 6, "traditional_judgement": 18, "scope_selector": 9, "risk_condition": 2}`。

### 唯一保留的本轮未决编码

节上六：Frame 将“悔亡”写成“若能因此悔悟”的条件解释。现有爻辞/小象没有把该前提充分展开，本轮不据此构造转机规则。保留原 Frame，新的 record eligible=false，回退结构层。后续可研究古注和版本，不自动纠正文义。

## 逐项证据与条件

下表所有版本字形保持原样；例如宾/賔、久/乆、彚等不作静默统一，现代展示文本没有改动。

## 乾初九（L01-1）

资格：可供本轮离线条件裁决。effect=`action_restriction`。

核对结论：潜伏阶段须保留勿用限制；比和不能自动许可行动。

- 原 Frame ID：`19c9e64eccb78667749cd8b0359768c3b2914c627b96744ae36a9c7ece3c9791`。
- 原 source fingerprint：`410b8c2047a00de4b0e21d30f0dae6e54e35a5a234341913b36f4d5ac0e8fdb2`。
- 原签名记录：`d058c998b7b75ded5c1a176228a341b95cfff0b10ca23f3b02f0405af65d9644`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `ctext_wuyingdian:qian:1:yao_classical_text:1` | 初九：潛龍，勿用。 | [周易（CTP易經整理文本）](https://ctext.org/book-of-changes/qian/zh)；頁面關聯底本：武英殿十三經注疏《周易正義》；搜尋索引快照，非掃描轉錄；易經；易經/qian 中文表格第4項 yao_classical_text | machine_verified |
| `runtime_ws_benyi:卷1:1:xiang_classical_text:1` | 潛龍勿用陽在下也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第1卦块 xiang_classical_text 第1爻 | machine_verified |
| `runtime_ws_benyi:卷1:1:yao_classical_text:1` | 初九潛龍勿用 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第1卦块 yao_classical_text 第1爻 | machine_verified |
| `runtime_ws_sibu:卷一:1:xiang_classical_text:1` | 潛龍勿用陽在下也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第1卦块 xiang_classical_text 第1爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| latent_stage | prerequisite | 适用的是潜伏、尚不宜施用的阶段。 | 潛龍勿用 | runtime_ws_benyi:卷1:1:yao_classical_text:1 |
| withhold_action | behavioral_reminder | 勿用是行动限制，不等同于整件事必败。 | 潛龍勿用陽在下也 | runtime_ws_benyi:卷1:1:xiang_classical_text:1, runtime_ws_sibu:卷一:1:xiang_classical_text:1 |


## 乾上九（L01-6）

资格：可供本轮离线条件裁决。effect=`adverse_warning`。

核对结论：亢极而有悔、盈不可久，是比和基础之外的明确不利限制。

- 原 Frame ID：`3c3c6182dd3279ec25085c41e9f281f6f97766774fed1468f7edeb8c6726f5c0`。
- 原 source fingerprint：`a9eef8e89a8ba917f985a0501559edb7ec1eee58749a30567c7c530d325c02a8`。
- 原签名记录：`e1d79dd811dde527522f47d421ed336d7694d3fe8290a32af74660f7366dff42`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:1:xiang_classical_text:6` | 亢龍有悔盈不可久也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第1卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_benyi:卷1:1:yao_classical_text:6` | 上九亢龍有悔 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第1卦块 yao_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷一:1:xiang_classical_text:6` | 亢龍有悔盈不可乆也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第1卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷一:1:yao_classical_text:6` | 上九亢龍有悔 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第1卦块 yao_classical_text 第6爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| excessive_height | prerequisite | 爻辞所述亢极状态；不推定用户现实已处高位。 | 亢龍有悔 | runtime_ws_benyi:卷1:1:yao_classical_text:6, runtime_ws_sibu:卷一:1:yao_classical_text:6 |
| cannot_last | outcome_limit | 盈满不可长久，不能由比和推出长久顺遂。 | 盈不可久也 | runtime_ws_benyi:卷1:1:xiang_classical_text:6 |


## 坤六二（L02-2）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：直方大的正直端方语境与无不利相连；不得去掉语境保证万事。

- 原 Frame ID：`d25d85f705329e79e339325651fc59d34357c234edb2a42e1357b9fcc3ff28d0`。
- 原 source fingerprint：`81c954556f6e77525433ca659d5dcd50336a502e5b1cca674b97978c120898d0`。
- 原签名记录：`1243ecaa9ab0620ae3a97548fd8ca043cb83e2fcb8527f72b0490cd266a5f54c`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:2:xiang_classical_text:2` | 六二之動直以方也不習无不利地道光也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第2卦块 xiang_classical_text 第2爻 | machine_verified |
| `runtime_ws_benyi:卷1:2:yao_classical_text:2` | 六二直方大不習无不利 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第2卦块 yao_classical_text 第2爻 | machine_verified |
| `runtime_ws_sibu:卷一:2:xiang_classical_text:2` | 六二之動直以方也不習无不利地道光也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第2卦块 xiang_classical_text 第2爻 | machine_verified |
| `runtime_ws_sibu:卷一:2:yao_classical_text:2` | 六二直方大不習无不利 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第2卦块 yao_classical_text 第2爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| upright_behavior | prerequisite | 直方大的行为语境。 | 直方大 | runtime_ws_benyi:卷1:2:yao_classical_text:2, runtime_ws_sibu:卷一:2:yao_classical_text:2 |
| upright_scope | traditional_judgement | 在直方大的爻义语境内保留无不利；不是现实成败保证。 | 不習无不利 | runtime_ws_benyi:卷1:2:yao_classical_text:2, runtime_ws_sibu:卷一:2:yao_classical_text:2 |


## 屯六三（L03-3）

资格：可供本轮离线条件裁决。effect=`adverse_warning`。

核对结论：无虞而逐鹿、继续前往之吝与见机舍弃必须合读。

- 原 Frame ID：`0624fa813fbf21a57576e306c959e3e536ccb209d57aa308cc5f38745b25e1cb`。
- 原 source fingerprint：`b83cef5b1c7589032c45b133a8c215bbef8576014df61130f1c92730e61ef16a`。
- 原签名记录：`b79dadee7f8658181c1f15a2ade139ad32aa9c85f12eecb89d8e476c2c8643bd`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:3:xiang_classical_text:3` | 即鹿无虞以從禽也君子舍之往吝窮也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第3卦块 xiang_classical_text 第3爻 | machine_verified |
| `runtime_ws_benyi:卷1:3:yao_classical_text:3` | 六三即鹿无虞惟入于林中君子幾不如舍往吝 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第3卦块 yao_classical_text 第3爻 | machine_verified |
| `runtime_ws_yichuan:卷1:3:xiang_classical_text:3` | 即鹿无虞以從禽也君子舍之往吝窮也 | [伊川易傳（四庫全書本）](https://zh.wikisource.org/wiki/%E4%BC%8A%E5%B7%9D%E6%98%93%E5%82%B3_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫逐卷電子轉錄，程頤撰；卷01；卷01 h3.l3.xiang_classical_text；伊川本完整经文段落/明确注解起点定位 | machine_verified |
| `runtime_ws_yichuan:卷1:3:yao_classical_text:3` | 六三即鹿无虞惟入于林中君子幾不如舍往吝 | [伊川易傳（四庫全書本）](https://zh.wikisource.org/wiki/%E4%BC%8A%E5%B7%9D%E6%98%93%E5%82%B3_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫逐卷電子轉錄，程頤撰；卷01；卷01 h3.l3.yao_classical_text；伊川本完整经文段落/明确注解起点定位 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| without_guide | prerequisite | 没有虞人引导而追逐的语境。 | 即鹿无虞 | runtime_ws_benyi:卷1:3:yao_classical_text:3, runtime_ws_yichuan:卷1:3:yao_classical_text:3 |
| persisting_risk | traditional_judgement | 继续前往的限制是往吝、穷；原文另有舍弃提醒，不能省略。 | 君子舍之往吝窮也 | runtime_ws_benyi:卷1:3:xiang_classical_text:3, runtime_ws_yichuan:卷1:3:xiang_classical_text:3 |


## 屯九五（L03-5）

资格：可供本轮离线条件裁决。effect=`alternative_scopes`。

核对结论：小贞与大贞是不同适用范围，不能合成一条整体吉凶。

- 原 Frame ID：`8ba932d99dc1d9d13f9e75a4523d01057941badeca8479887580caa9c3242f6d`。
- 原 source fingerprint：`eb9261cb3b5dc83b1b412ff9d90093c7aecf627c99e67714c5572c90a5c29657`。
- 原签名记录：`31adedc7b8a6d2451af0cbd59669a581939bb24bf3783ff5a970639ad0ef2bd0`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:3:xiang_classical_text:5` | 屯其膏施未光也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第3卦块 xiang_classical_text 第5爻 | machine_verified |
| `runtime_ws_benyi:卷1:3:yao_classical_text:5` | 九五屯其膏小貞吉大貞凶 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第3卦块 yao_classical_text 第5爻 | machine_verified |
| `runtime_ws_sibu:卷一:3:xiang_classical_text:5` | 屯其膏施未光也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第3卦块 xiang_classical_text 第5爻 | machine_verified |
| `runtime_ws_sibu:卷一:3:yao_classical_text:5` | 九五屯其膏小貞吉大貞凶 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%80)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷一；卷一 第3卦块 yao_classical_text 第5爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| small_scope | scope_selector | 适用于小贞范围。 | 小貞吉 | runtime_ws_benyi:卷1:3:yao_classical_text:5, runtime_ws_sibu:卷一:3:yao_classical_text:5 |
| large_scope | scope_selector | 适用于大贞范围。 | 大貞凶 | runtime_ws_benyi:卷1:3:yao_classical_text:5, runtime_ws_sibu:卷一:3:yao_classical_text:5 |
| small | traditional_judgement | 小贞范围记为有利；不推定所问事情属于该范围。 | 小貞吉 | runtime_ws_benyi:卷1:3:yao_classical_text:5, runtime_ws_sibu:卷一:3:yao_classical_text:5 |
| large | traditional_judgement | 大贞范围记为不利；不按用户金额自动划定古义大小。 | 大貞凶 | runtime_ws_benyi:卷1:3:yao_classical_text:5, runtime_ws_sibu:卷一:3:yao_classical_text:5 |


## 讼九四（L06-4）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：不克讼后的复即命、渝安贞是吉的前提，不是用生体便可继续争讼。

- 原 Frame ID：`e797334db60003330ce861424598593b451e5a078231b5f3a33e73a61fdda1e6`。
- 原 source fingerprint：`e55e08452cce45cb6f59ee6b0712bac8105bdc7c92a8fb27bf156af5aa132314`。
- 原签名记录：`7dfd65d19f2dde864cd9503618c70708e74094cf3b7fe162ea8f44b43a4a9af4`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:6:xiang_classical_text:4` | 復即命渝安貞不失也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第6卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:6:yao_classical_text:4` | 九四不克訟復即命渝安貞吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第6卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| return_change_settle | prerequisite | 复即命、改变心意而安贞。 | 復即命渝安貞吉 | runtime_ws_benyi:卷1:6:yao_classical_text:4 |
| return_without_loss | traditional_judgement | 有利表述连同回返、改变与安贞一起保留，不推定这些前提已做到。 | 復即命渝安貞不失也 | runtime_ws_benyi:卷1:6:xiang_classical_text:4 |


## 师初六（L07-1）

资格：可供本轮离线条件裁决。effect=`adverse_warning`。

核对结论：出师以律、失律之凶是明确约束，体克用不替代纪律。

- 原 Frame ID：`b7b9a1eec8eca30c55d3e59eda32d1e9ef41e645ea1871cef8bf718898f6ed83`。
- 原 source fingerprint：`04d9f682eb11a5d94c58e114b6d2b63b7f6447868e8fb2bfcfae985b65fbf434`。
- 原签名记录：`dcb1b18bb0708d1de7c0e9836018eea326758c88185d1b3a967788a5563e0a49`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:7:xiang_classical_text:1` | 師出以律失律凶也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第7卦块 xiang_classical_text 第1爻 | machine_verified |
| `runtime_ws_benyi:卷1:7:yao_classical_text:1` | 初六師出以律否臧凶 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第7卦块 yao_classical_text 第1爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| loss_of_discipline | risk_condition | 失律的情形；未推定用户失律。 | 失律凶也 | runtime_ws_benyi:卷1:7:xiang_classical_text:1 |
| discipline_warning | traditional_judgement | 失律带来的不利警示须保留，不能凭结构有利忽略。 | 師出以律失律凶也 | runtime_ws_benyi:卷1:7:xiang_classical_text:1 |


## 比六二（L08-2）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：比之自内、贞吉与不自失相连，是用克体之外的条件性有利线索。

- 原 Frame ID：`127eed28768394028d21ff58cadcf94fc58853865f497040b04a7411b15f1b81`。
- 原 source fingerprint：`089258a73f8d454155678b4ae6a636f755c8d0cee67119b644f7bc82ade2a289`。
- 原签名记录：`59d68280a11ffa77a623087c1ae6440a026b7b0acfd93c6ac67ae983849da22d`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:8:xiang_classical_text:2` | 比之自内不自失也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第8卦块 xiang_classical_text 第2爻 | machine_verified |
| `runtime_ws_benyi:卷1:8:yao_classical_text:2` | 六二比之自内貞吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第8卦块 yao_classical_text 第2爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| inner_steadfastness | prerequisite | 比之自内且持守贞、不自失。 | 比之自内不自失也 | runtime_ws_benyi:卷1:8:xiang_classical_text:2 |
| steadfast_affiliation | traditional_judgement | 在自内而贞、不自失的语境下有贞吉；不能无条件翻转用克体。 | 比之自内貞吉 | runtime_ws_benyi:卷1:8:yao_classical_text:2 |


## 小畜九三（L09-3）

资格：可供本轮离线条件裁决。effect=`action_restriction`。

核对结论：舆说辐、夫妻反目与不能正室是失和、受阻提醒，不按该爻推定用户婚姻事实。

- 原 Frame ID：`162dafb12cff95f296ca2dabd05650972f16241388c2fbadfac496f0d2dca442`。
- 原 source fingerprint：`3ed6bbe9f20efe0e1665c795954a3478f5fb87691a5a1cfef2311d6e31ea731e`。
- 原签名记录：`14c7fa42cb866f4d66e6fd92d3e92f4179eabe8964a40e6bf50cf6b66a51fb1d`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:9:xiang_classical_text:3` | 夫妻反目不能正室也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第9卦块 xiang_classical_text 第3爻 | machine_verified |
| `runtime_ws_benyi:卷1:9:yao_classical_text:3` | 九三輿説輻夫妻反目 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第9卦块 yao_classical_text 第3爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| discoordination | scope_selector | 该爻描述受阻与不协调的语境，不代表现实已发生。 | 輿説輻夫妻反目 | runtime_ws_benyi:卷1:9:yao_classical_text:3 |
| coordination_limit | outcome_limit | 保留协调与受阻的限制，不扩为具体感情预测。 | 夫妻反目不能正室也 | runtime_ws_benyi:卷1:9:xiang_classical_text:3 |


## 履九四（L10-4）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：终吉不得脱离履虎尾、愬愬的危惧谨慎前提。

- 原 Frame ID：`c0e1a737afac64ae20bffd744318ff7ead3a00c3986dccfdff6258c0a045fdc3`。
- 原 source fingerprint：`875d02dee8c773ab4ea90a019efe88839d6d41fd1cdb3b90d3018e38d356e376`。
- 原签名记录：`6dd0b8e224287412cad13086238c3c7dbc59e148bb630fbae596ebfbcb95f320`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:10:xiang_classical_text:4` | 愬愬終吉志行也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第10卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:10:yao_classical_text:4` | 九四履虎尾愬愬終吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第10卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| fearful_caution | prerequisite | 履虎尾而愬愬，保持危惧谨慎。 | 履虎尾愬愬終吉 | runtime_ws_benyi:卷1:10:yao_classical_text:4 |
| caution_supported | traditional_judgement | 终吉只在该爻危惧谨慎的完整语境内保留，不能省去限制。 | 愬愬終吉志行也 | runtime_ws_benyi:卷1:10:xiang_classical_text:4 |


## 否初六（L12-1）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：拔茅同类关系与贞、志在君的条件相连，不以用生体代替守正。

- 原 Frame ID：`6e5a74b4360df89bd595a0a7adc2d1d5968b7749062a78ba61c39ac896c8c944`。
- 原 source fingerprint：`825175af35452707a7bcec7430718ca32129631e6510d0e48090d13df9fd2309`。
- 原签名记录：`bc2648f0a983cfbcebc830f69d1e5684811e28f3ec1797766a8b9644e573c4e8`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:12:xiang_classical_text:1` | 拔茅貞吉志在君也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第12卦块 xiang_classical_text 第1爻 | machine_verified |
| `runtime_ws_benyi:卷1:12:yao_classical_text:1` | 初六拔茅茹以其彚貞吉亨 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第12卦块 yao_classical_text 第1爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| steadfast_loyal_intent | prerequisite | 贞及志在君的语境。 | 拔茅貞吉志在君也 | runtime_ws_benyi:卷1:12:xiang_classical_text:1 |
| steadfast_flow | traditional_judgement | 原爻贞吉亨的有利表述保留其贞的限定；不改变已确认展示标点。 | 貞吉亨 | runtime_ws_benyi:卷1:12:yao_classical_text:1 |


## 否上九（L12-6）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：否终则倾是终极闭塞转变的来源语境，不推定所有闭塞均已到终点。

- 原 Frame ID：`825967de5cf045e7f036984ccb4b3d66c26e9d06de300acece2cd05c4e0aa108`。
- 原 source fingerprint：`889448ef7182613e96eedd839f4094a8d6788cc519fb5eeac227cd5984418365`。
- 原签名记录：`427113f3a3e91e97abb5ecfdf9dd62e86d8547189b1476ab0f920266e376c816`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:12:xiang_classical_text:6` | 否終則傾何可長也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第12卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_benyi:卷1:12:yao_classical_text:6` | 上九傾否先否後喜 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第12卦块 yao_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷二:12:xiang_classical_text:6` | 否終則傾何可長也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第2卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷二:12:yao_classical_text:6` | 上九傾否先否後喜 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第2卦块 yao_classical_text 第6爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| closure_at_end | prerequisite | 否已到终的语境，未确定现实处于此阶段。 | 否終則傾 | runtime_ws_benyi:卷1:12:xiang_classical_text:6, runtime_ws_sibu:卷二:12:xiang_classical_text:6 |
| reversal_at_end | traditional_judgement | 先否后喜作为终极转变的有利线索，不称为必然未来。 | 傾否先否後喜 | runtime_ws_benyi:卷1:12:yao_classical_text:6, runtime_ws_sibu:卷二:12:yao_classical_text:6 |


## 大有初九（L14-1）

资格：可供本轮离线条件裁决。effect=`action_restriction`。

核对结论：艰则无咎是谨慎限制；无咎不延伸为额外获利或整件事的成功结果。

- 原 Frame ID：`1e7a876bfb0b6a0db488c3dd965b56b597c5eada293d7eec1b57050af2a13655`。
- 原 source fingerprint：`65322cca5cb92650c3a942c8c90b7ed989bdda460ee6497c5332824aae01047d`。
- 原签名记录：`36fb002b0239afdc7d94dc601fd715cbb5be2649f8f0f37a0f1de42b6c4acc47`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:14:xiang_classical_text:1` | 大有初九无交害也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第14卦块 xiang_classical_text 第1爻 | machine_verified |
| `runtime_ws_benyi:卷1:14:yao_classical_text:1` | 初九无交害匪咎艱則无咎 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第14卦块 yao_classical_text 第1爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| difficult_caution | prerequisite | 艰的限定。 | 艱則无咎 | runtime_ws_benyi:卷1:14:yao_classical_text:1 |
| avoid_fault_only | outcome_limit | 只有免于咎的有限表述，不提升为整体有利结果。 | 无交害匪咎艱則无咎 | runtime_ws_benyi:卷1:14:yao_classical_text:1 |


## 豫九四（L16-4）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：由豫、大有得、勿疑与志大行构成有利线索，不能用来取消体用不利。

- 原 Frame ID：`c59a1a794ebd28f0a5f54905b89c68784d3bfc12257e3b45da071f394790fbc0`。
- 原 source fingerprint：`73ec3e03b1ef946f02ee647caf505309a34c151bf5ad0a3ed01e524c9b2356bd`。
- 原签名记录：`b45a48668507f8be5184e1a4f5ee549e223b30c510f3622b6fdb3ee7b0f779d6`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:16:xiang_classical_text:4` | 由豫大有得志大行也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第16卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:16:yao_classical_text:4` | 九四由豫大有得勿疑朋盍簪 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第16卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| by_yu_scope | prerequisite | 由豫而勿疑的爻义语境，不推定用户已有所得。 | 由豫大有得勿疑 | runtime_ws_benyi:卷1:16:yao_classical_text:4 |
| intent_proceeds | traditional_judgement | 大有得、志大行提供有利线索，只与体用关系并列保留。 | 由豫大有得志大行也 | runtime_ws_benyi:卷1:16:xiang_classical_text:4 |


## 随六二（L17-2）

资格：可供本轮离线条件裁决。effect=`tradeoff`。

核对结论：系小子、失丈夫与弗兼与明确提示不能兼顾；没有整爻吉凶许可。

- 原 Frame ID：`d649c7f98a2aa36212e36f5d2d7987509791063592d1030f2559256a8a834d51`。
- 原 source fingerprint：`ad2b4cc972ef48167a5b5e1b8286cf6e09f5579d21ac35cd66f67694ddba0cba`。
- 原签名记录：`020585aa60183d272caf0a77209345e41eb4916b61832a951374d802ea447cea`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:17:xiang_classical_text:2` | 係小子弗兼與也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第17卦块 xiang_classical_text 第2爻 | machine_verified |
| `runtime_ws_benyi:卷1:17:yao_classical_text:2` | 六二係小子失丈夫 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第17卦块 yao_classical_text 第2爻 | machine_verified |
| `runtime_ws_sibu:卷二:17:xiang_classical_text:2` | 係小子弗兼與也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第7卦块 xiang_classical_text 第2爻 | machine_verified |
| `runtime_ws_sibu:卷二:17:yao_classical_text:2` | 六二係小子失丈夫 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第7卦块 yao_classical_text 第2爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| attachment_choice | scope_selector | 选择系小子的语境，不把小子、丈夫指定为现实人物。 | 係小子失丈夫 | runtime_ws_benyi:卷1:17:yao_classical_text:2, runtime_ws_sibu:卷二:17:yao_classical_text:2 |
| cannot_keep_both | behavioral_reminder | 取舍是必须保留的限制；体旺、体克用不支持两边同时保全。 | 係小子弗兼與也 | runtime_ws_benyi:卷1:17:xiang_classical_text:2, runtime_ws_sibu:卷二:17:xiang_classical_text:2 |


## 随九四（L17-4）

资格：可供本轮离线条件裁决。effect=`alternative_scopes`。

核对结论：固守随之所得的风险与有孚在道以明的免咎条件分支必须分开。

- 原 Frame ID：`ee96de5cdf7916345219ed267c7a14bd9c91522199ecc92f75fee733eeeb7eac`。
- 原 source fingerprint：`f39a84073279674b26527b6a7771ce068b491cd79bc3381c2a2e924fe9675109`。
- 原签名记录：`bb6822b1dd1a1ca579a3a17d2c6843986eaa2ac8ef82d3a4db3fd0dbee4a5595`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:17:xiang_classical_text:4` | 隨有獲其義凶也有孚在道明功也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第17卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:17:yao_classical_text:4` | 九四隨有獲貞凶有孚在道以明何咎 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第17卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| cling_to_gains | scope_selector | 随有获而贞的风险分支。 | 隨有獲貞凶 | runtime_ws_benyi:卷1:17:yao_classical_text:4 |
| faith_path_clarity | scope_selector | 有孚在道以明的免咎分支。 | 有孚在道以明何咎 | runtime_ws_benyi:卷1:17:yao_classical_text:4 |
| cling_risk | traditional_judgement | 在随有获而固守的语境内保留风险，不能据有获直接断有利。 | 隨有獲其義凶也 | runtime_ws_benyi:卷1:17:xiang_classical_text:4 |
| qualified_no_fault | outcome_limit | 何咎只表免咎的有限结果，不自动等于整体成功。 | 有孚在道以明何咎 | runtime_ws_benyi:卷1:17:yao_classical_text:4 |


## 观六四（L20-4）

资格：可供本轮离线条件裁决。effect=`bounded_opportunity`。

核对结论：利用宾于王仅在观国之光、尚宾的参与角色中有利；不越界推断所问事情整体成功。

- 原 Frame ID：`cddf110a973e4f69b79d6ee1661724394fb29c298fa2d0b685d060320fb7d068`。
- 原 source fingerprint：`e95f8e284138d99e7cd38e1774c804ddb36833d80afbc30046e8def40d8c7a07`。
- 原签名记录：`763d22fffbcf92da66e7c29458d12ced93ce18d36298897e111a90a934e1a87c`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:20:xiang_classical_text:4` | 觀國之光尚賓也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第20卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:20:yao_classical_text:4` | 六四觀國之光利用賔于王 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第20卦块 yao_classical_text 第4爻 | machine_verified |
| `runtime_ws_sibu:卷二:20:xiang_classical_text:4` | 觀國之光尚賔也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第10卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_sibu:卷二:20:yao_classical_text:4` | 六四觀國之光利用賔于王 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%BA%8C)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷二；卷二 第10卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| guest_participation_scope | scope_selector | 观国之光、以宾参与的限定角色，不推定用户身份。 | 觀國之光尚賓也 | runtime_ws_benyi:卷1:20:xiang_classical_text:4 |
| guest_role_opportunity | traditional_judgement | 以宾参与这一特定动作有利，不能与用克体视为同一范围的直接矛盾。 | 利用賔于王 | runtime_ws_benyi:卷1:20:yao_classical_text:4, runtime_ws_sibu:卷二:20:yao_classical_text:4 |


## 贲九三（L22-3）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：永贞之吉须连同长期持守的前提保留。

- 原 Frame ID：`888d10399531c851ee4e7b834ca9b1743a7d5baa26e1bb49d01e2823e1f34a43`。
- 原 source fingerprint：`1ddf5b924bb42bbae066241aff3b663dbacb4d48b4336aeaeb0747391b292f4c`。
- 原签名记录：`e86709a8ed8eefb34251fdc51d9172b1a214431e7c2eeebcecdabe6c7ec690c6`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:22:xiang_classical_text:3` | 永貞之吉終莫之陵也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第22卦块 xiang_classical_text 第3爻 | machine_verified |
| `runtime_ws_benyi:卷1:22:yao_classical_text:3` | 九三賁如濡如永貞吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第22卦块 yao_classical_text 第3爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| lasting_steadfastness | prerequisite | 永贞，不能只凭外表润泽。 | 賁如濡如永貞吉 | runtime_ws_benyi:卷1:22:yao_classical_text:3 |
| lasting_support | traditional_judgement | 永贞范围内有利，不能确认现实已经满足长期持守。 | 永貞之吉終莫之陵也 | runtime_ws_benyi:卷1:22:xiang_classical_text:3 |


## 复上六（L24-6）

资格：可供本轮离线条件裁决。effect=`adverse_warning`。

核对结论：迷复、反君道的风险是明确动爻限制，不把行师、十年扩成现代时间预测。

- 原 Frame ID：`81886810416e25f04f9229653d40ea9c24a1fa783094052ea862a9bc92d3e719`。
- 原 source fingerprint：`f6b0056327f713d48c6119762985b18ec254362e782c779c58f074282b78cc11`。
- 原签名记录：`170aeef62fb652b237debbe35b9f2cbc8ec897437e4d5db3b2c4974a1e074f07`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:24:xiang_classical_text:6` | 迷復之凶反君道也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第24卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_benyi:卷1:24:yao_classical_text:6` | 上六迷復凶有災眚用行師終有大敗以其國君凶至于十年不克征 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第24卦块 yao_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷三:24:xiang_classical_text:6` | 迷復之凶反君道也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%89)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷三；卷三 第4卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_sibu:卷三:24:yao_classical_text:6` | 上六迷復凶有災眚用行師終有大敗以其國君凶至于十年不克征 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%89)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷三；卷三 第4卦块 yao_classical_text 第6爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| lost_return | risk_condition | 迷复而反君道的语境，未推定用户已迷失。 | 迷復之凶反君道也 | runtime_ws_benyi:卷1:24:xiang_classical_text:6, runtime_ws_sibu:卷三:24:xiang_classical_text:6 |
| lost_return_risk | traditional_judgement | 迷复的明确风险与体克用基础有利形成条件性张力；不代替现实成败。 | 迷復凶有災眚 | runtime_ws_benyi:卷1:24:yao_classical_text:6, runtime_ws_sibu:卷三:24:yao_classical_text:6 |


## 无妄初九（L25-1）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：无妄之往的有利表述以不虚妄为语境，不自动评价用户动机。

- 原 Frame ID：`b565325207b4a780a8f2d3d8ddbc828ba4c0f629d484b0a78d0ed41568614c56`。
- 原 source fingerprint：`b18f31141f9b892ed03791ebf76447b1003fdeecde1dd7d742913c9f2c45fd5d`。
- 原签名记录：`79798b06f24ca59cda52e6417138e19ea8a40c21dfd253f168c0bdb95e6de78f`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:25:xiang_classical_text:1` | 无妄之往得志也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第25卦块 xiang_classical_text 第1爻 | machine_verified |
| `runtime_ws_benyi:卷1:25:yao_classical_text:1` | 初九无妄往吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第25卦块 yao_classical_text 第1爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| without_falsehood | prerequisite | 无妄的行事语境。 | 无妄往吉 | runtime_ws_benyi:卷1:25:yao_classical_text:1 |
| uncontrived_progress | traditional_judgement | 无妄而往的有利线索保留，不能推定所有行动都属无妄。 | 无妄之往得志也 | runtime_ws_benyi:卷1:25:xiang_classical_text:1 |


## 大过九四（L28-4）

资格：可供本轮离线条件裁决。effect=`alternative_scopes`。

核对结论：栋隆之吉与有它之吝是有无牵累的不同分支，不作加权抵消。

- 原 Frame ID：`5bf2242364e0b22cb950942cff10cff45d925f0890662b220090e8477e6c2405`。
- 原 source fingerprint：`1064578e62fa6675a6f54c672b3ff31ab184c3cc6615a9c0514e3eb3480b7516`。
- 原签名记录：`cd758474abde6b169ed2044af202f7c8f6e0266348dba570c0c8f7effd7bcddc`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:28:xiang_classical_text:4` | 棟隆之吉不橈乎下也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第28卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_benyi:卷1:28:yao_classical_text:4` | 九四棟隆吉有它吝 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第28卦块 yao_classical_text 第4爻 | machine_verified |
| `runtime_ws_sibu:卷三:28:xiang_classical_text:4` | 棟隆之吉不橈乎下也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%89)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷三；卷三 第8卦块 xiang_classical_text 第4爻 | machine_verified |
| `runtime_ws_sibu:卷三:28:yao_classical_text:4` | 九四棟隆吉有它吝 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%89)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷三；卷三 第8卦块 yao_classical_text 第4爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| support_without_bending | scope_selector | 栋隆、不桡乎下的范围。 | 棟隆之吉不橈乎下也 | runtime_ws_benyi:卷1:28:xiang_classical_text:4, runtime_ws_sibu:卷三:28:xiang_classical_text:4 |
| other_entanglement | scope_selector | 另有牵累的范围。 | 有它吝 | runtime_ws_benyi:卷1:28:yao_classical_text:4, runtime_ws_sibu:卷三:28:yao_classical_text:4 |
| support | traditional_judgement | 栋隆范围内有利，但不知道实际是否属于这一范围。 | 棟隆吉 | runtime_ws_benyi:卷1:28:yao_classical_text:4, runtime_ws_sibu:卷三:28:yao_classical_text:4 |
| entanglement_limit | outcome_limit | 有它时保留憾惜限制，不能推定用户已有牵累。 | 有它吝 | runtime_ws_benyi:卷1:28:yao_classical_text:4, runtime_ws_sibu:卷三:28:yao_classical_text:4 |


## 坎九五（L29-5）

资格：可供本轮离线条件裁决。effect=`action_restriction`。

核对结论：坎不盈、中未大与既平无咎仅支持有限缓解，不推出危难全面结束。

- 原 Frame ID：`efb5d2f8f368b41646b277abeb9d8becfc9e749ce69113f2606ae60cf2f684f7`。
- 原 source fingerprint：`673987b55da5f556fffb18b49169b53f18912e0b9e2ecf466ef26e0c5e3a1072`。
- 原签名记录：`386d6ba5bd142a91bb418c627e6a011f11716c14d46af1e0c156b15aae5f81f4`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷1:29:xiang_classical_text:5` | 坎不盈中未大也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第29卦块 xiang_classical_text 第5爻 | machine_verified |
| `runtime_ws_benyi:卷1:29:yao_classical_text:5` | 九五坎不盈祗既平无咎 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B71)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷1；卷1 第29卦块 yao_classical_text 第5爻 | machine_verified |
| `runtime_ws_sibu:卷三:29:xiang_classical_text:5` | 坎不盈中未大也 | [周易（四部叢刊本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E4%B8%89)；上海涵芬樓景宋刊本；維基文庫逐卷電子轉錄；卷三；卷三 第9卦块 xiang_classical_text 第5爻 | machine_verified |
| `runtime_ws_zhengyi:卷05:29:yao_classical_text:5` | 九五坎不盈祗既平无咎 | [周易注疏（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%B3%A8%E7%96%8F_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B705)；景印文淵閣四庫全書第七冊；維基文庫逐卷電子轉錄；卷05；卷05 h29.l5.yao_classical_text；全文唯一定位且末端有明确经注/章节边界 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| not_full | prerequisite | 坎不盈、中未大的语境。 | 坎不盈中未大也 | runtime_ws_benyi:卷1:29:xiang_classical_text:5, runtime_ws_sibu:卷三:29:xiang_classical_text:5 |
| limited_relief | outcome_limit | 既平无咎限制在免咎范围，不等于完全脱险或胜利。 | 祗既平无咎 | runtime_ws_benyi:卷1:29:yao_classical_text:5, runtime_ws_zhengyi:卷05:29:yao_classical_text:5 |


## 困上六（L47-6）

资格：可供本轮离线条件裁决。effect=`conditional_support`。

核对结论：困于葛藟、臲卼背景下的动悔、有悔、征吉，必须保留悔的前提与适用范围。

- 原 Frame ID：`d15a46d0d85b1d1f1a013ef21ca5d053bc1532411a7eee88ae857da61e1b8b3a`。
- 原 source fingerprint：`2488c156032c0a7e23ecc37ae82894fb12a15eb1e84bb23d70c338d783fe6093`。
- 原签名记录：`b38a059ef8b732e0bee28c646564d53fb81663f6b9ad52a8a54a8989ff93f0d0`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷2:47:xiang_classical_text:6` | 困于葛藟未當也動悔有悔吉行也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B72)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷2；卷2 第17卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_benyi:卷2:47:yao_classical_text:6` | 上六困于葛藟于臲卼曰動悔有悔征吉 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B72)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷2；卷2 第17卦块 yao_classical_text 第6爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| recognize_regret | prerequisite | 动悔而有悔的语境；不确认用户已经反省。 | 動悔有悔征吉 | runtime_ws_benyi:卷2:47:yao_classical_text:6 |
| regret_progress | traditional_judgement | 原典有条件性前行线索，不用征吉保证现实结果。 | 動悔有悔吉行也 | runtime_ws_benyi:卷2:47:xiang_classical_text:6 |


## 节上六（L60-6）

资格：尚不具备新裁决资格。effect=`unresolved_encoding`。

核对结论：Frame 的若能因此悔悟是一种条件解释；本轮原文仅明示苦节贞凶、悔亡，悔亡是否以悔悟为条件尚未取得足够支持。

- 原 Frame ID：`204bd593fd52b28fc396dd061f61b831cc724b129273f3d4f9d2c06196e73a32`。
- 原 source fingerprint：`33276801ab84c49b79c33da546a614688be6f7c1d97666ebe7c13c0e5019aa13`。
- 原签名记录：`afbde527966e7cf52ec4c98ca240c9e91697cfd0f3dc9293f5e2243be2cd78e2`。
- 新编码版本：`moving_line_condition_review_v1`；审核方式：`explicit_source_and_signed_frame_condition_review`。
- 现实条件：未评估；未推定用户满足。完整 Frame core/conditions/cautions、引用哈希与本轮审核 receipt 见 [条件记录](../data/day6a_condition_reviews.json)。

### 原典依据（字形原样保留）

| Evidence | 完整原典字段 | 来源、版本与位置 | 原状态 |
| --- | --- | --- | --- |
| `runtime_ws_benyi:卷2:60:xiang_classical_text:6` | 苦節貞凶其道窮也 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B72)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷2；卷2 第30卦块 xiang_classical_text 第6爻 | machine_verified |
| `runtime_ws_benyi:卷2:60:yao_classical_text:6` | 上六苦節貞凶悔亡 | [周易本義（四庫全書本）](https://zh.wikisource.org/wiki/%E5%91%A8%E6%98%93%E6%9C%AC%E7%BE%A9_(%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC)/%E5%8D%B72)；景印文淵閣四庫全書本；維基文庫電子轉錄；卷2；卷2 第30卦块 yao_classical_text 第6爻 | machine_verified |

### 条件与判断范围

| 编码 | 类别 | 条件/限定义 | 原文定位摘录 | Evidence IDs |
| --- | --- | --- | --- | --- |
| 无 | 待研究 | 未自动编入新极性层 | — | 原典与 Frame 保留 |
