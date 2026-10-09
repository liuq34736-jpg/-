# Day 6A：离线引擎报告

## 已实现

独立包：[backend/traditional_conditions_v1](../backend/traditional_conditions_v1/)，不改 Day 5 包。入口 `ConditionalJudgementEngine.evaluate(ValidatedJudgementInput)`，复用旧 guarded adapter 与原签名校验，不接受外部任意 JSON 作为可信输入。

数据：[day6a_condition_review_definitions.json](../data/day6a_condition_review_definitions.json) 为明确逐条审核定义；[day6a_condition_reviews.json](../data/day6a_condition_reviews.json) 为绑定证据和 Frame 后的固定目录。没有生产接口、数据库迁移、缓存写入或 AI 调用。

输出包含：有条件传统倾向、体用基础与时令修饰、动爻审核记录、原典完整引用、互变阶段辅助、条件性主要张力、未决分支、规则来源和版本。原始 calculation、原 Frame core/conditions/cautions、来源状态均原样保留。

## 实际覆盖与不能判断的原因

- 384 条原 Frame 读取通过，24 条新条件核对，23 条获得本轮离线条件裁决资格。
- 下列 20 条可形成**有范围限制的综合倾向**：乾初九、乾上九、坤六二、屯六三、讼九四、师初六、比六二、小畜九三、履九四、否初六、否上九、大有初九、豫九四、随六二、观六四、贲九三、复上六、无妄初九、坎九五、困上六。
- 以下 3 条证据可用但无法选定分支：屯九五、随九四、大过九四。仍保留来源条件及体用基础，不能给单一综合方向。
- 节上六因前提编码尚无足够支持仅保留结构层和原有语义。
- 其余 360 个未审核爻位没有新综合裁决资格；不是缺古籍或缺 Frame，而是缺逐爻条件/范围审核。
- 任何案例都没有程序认可的现实条件满足证据；这里的方向只是规则层分析，不是实际事件的终判。

## 必须验收的案例

### 观六四

体用基础偏不利；利用宾于王仅在观国之光、尚宾的参与角色中有利；不越界推断所问事情整体成功。克体一方衰，其作用受限，但用克体仍在，不能当成不利已消除。互变的不同方向仅作阶段辅助分歧，不单独改判混合。未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。

本卦观、六四、互剥、变否完全不变；用克体、体土平、用木衰、酉月金当令保持。新方向：`adverse`，范围 `bounded_reviewed_synthesis`。宾参与的局部机会单独列为 favorable factor，但不是整件事反转依据。互剥土比和与变否乾金耗体作为辅助分歧，不再自动制造 mixed。

### 随六二

体用基础偏有利；系小子、失丈夫与弗兼与明确提示不能兼顾；没有整爻吉凶许可。未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。

本卦随、六二、互渐、变兑不变；体兑金、用震木、体克用、体旺用衰保持。新方向 `favorable`，必须带“弗兼与”的取舍限制；没有利用关键词给整爻添加吉凶。

### 比和但动爻不利限制：乾上九

体用基础偏有利；亢极而有悔、盈不可久，是比和基础之外的明确不利限制。主要依据存在条件性张力，保留两种优先解释，暂不选定单一结果。未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。

比和基础有利与亢极不可久的警示形成条件性主要张力，输出 mixed，保留优先级争议，不推定用户已亢极。

### 用生体但有前提：讼九四

体用基础偏有利；不克讼后的复即命、渝安贞是吉的前提，不是用生体便可继续争讼。互变的不同方向仅作阶段辅助分歧，不单独改判混合。未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。

不能用用生体替代复即命、渝安贞；现实前提未评估。

### 体用不利但条件性转机：比六二

体用基础偏不利；比之自内、贞吉与不自失相连，是用克体之外的条件性有利线索。主要依据存在条件性张力，保留两种优先解释，暂不选定单一结果。互变的不同方向仅作阶段辅助分歧，不单独改判混合。未确认现实前提已满足；以上是有范围限制的传统规则分析，不是事情必然成功或失败的预测。

用克体不消失，贞吉、不自失的原爻条件亦保留；mixed 是未决规则张力，不作现实好坏裁定。

### 乾坤互卦与来源不足

乾、坤的冻结互卦仍按 v1 计算，原典“乾坤无互、互其变卦”继续 reference_only，不改变计算。缺规则影像、原签名无效、来源被排除等情况均已通过测试撤去条件资格；有结构则仅保留结构，不用别的资料补证。

## 24 条代表性案例（统一验收时刻 2026-09-24 19:45:35 +08:00）

| 对象 | 体用关系 | 体/用状态 | 条件资格 | 综合方向 | 范围 |
| --- | --- | --- | --- | --- | --- |
| 1:1 乾初九 | same_element | wang/wang | 有 | favorable | bounded_reviewed_synthesis |
| 1:6 乾上九 | same_element | wang/wang | 有 | mixed | bounded_reviewed_synthesis |
| 2:2 坤六二 | same_element | neutral/neutral | 有 | favorable | bounded_reviewed_synthesis |
| 3:3 屯六三 | body_generates_yong | neutral/shuai | 有 | adverse | bounded_reviewed_synthesis |
| 3:5 屯九五 | yong_generates_body | shuai/neutral | 有 | insufficient_evidence | bounded_reviewed_synthesis |
| 6:4 讼九四 | yong_generates_body | neutral/wang | 有 | favorable | bounded_reviewed_synthesis |
| 7:1 师初六 | body_controls_yong | neutral/neutral | 有 | mixed | bounded_reviewed_synthesis |
| 8:2 比六二 | yong_controls_body | neutral/neutral | 有 | mixed | bounded_reviewed_synthesis |
| 9:3 小畜九三 | yong_controls_body | shuai/wang | 有 | adverse | bounded_reviewed_synthesis |
| 10:4 履九四 | same_element | wang/wang | 有 | favorable | bounded_reviewed_synthesis |
| 12:1 否初六 | yong_generates_body | wang/neutral | 有 | favorable | bounded_reviewed_synthesis |
| 12:6 否上九 | body_generates_yong | neutral/wang | 有 | mixed | bounded_reviewed_synthesis |
| 14:1 大有初九 | body_controls_yong | neutral/wang | 有 | favorable | bounded_reviewed_synthesis |
| 16:4 豫九四 | yong_controls_body | neutral/shuai | 有 | mixed | bounded_reviewed_synthesis |
| 17:2 随六二 | body_controls_yong | wang/shuai | 有 | favorable | bounded_reviewed_synthesis |
| 17:4 随九四 | yong_controls_body | shuai/wang | 有 | insufficient_evidence | bounded_reviewed_synthesis |
| 20:4 观六四 | yong_controls_body | neutral/shuai | 有 | adverse | bounded_reviewed_synthesis |
| 22:3 贲九三 | yong_generates_body | neutral/neutral | 有 | favorable | bounded_reviewed_synthesis |
| 24:6 复上六 | body_controls_yong | shuai/neutral | 有 | mixed | bounded_reviewed_synthesis |
| 25:1 无妄初九 | body_controls_yong | wang/shuai | 有 | favorable | bounded_reviewed_synthesis |
| 28:4 大过九四 | yong_controls_body | shuai/wang | 有 | insufficient_evidence | bounded_reviewed_synthesis |
| 29:5 坎九五 | same_element | neutral/neutral | 有 | favorable | bounded_reviewed_synthesis |
| 47:6 困上六 | yong_generates_body | neutral/wang | 有 | favorable | bounded_reviewed_synthesis |
| 60:6 节上六 | body_generates_yong | wang/neutral | 无 | insufficient_evidence | structure_only |

完整结构结果及逐项依据：[day6a_examples.json](day6a_examples.json)。当前标签定义与 Day 5 不同：旧版只综合结构/辅助，新版对未审核爻位不授予整体综合标签。不能把标签变化夸称为修正了算法。

## 完整性

Day 5 回退提交：`d3c721095f30d1e72ea85f498ade35e4fe1188f1`；独立分支 `day6a/condition-adjudication-offline`。

Day 5 的 248 个 tracked 文件、生产 157 个冻结文件、509 个签名缓存文件均未改变；42 条历史的 schema、逐行 hash、数据库字节 hash 一致。完整记录：[day6a_integrity_results.json](day6a_integrity_results.json)。

## 明确尚未实现

其余爻位条件裁决、现实前提自动认定、唯一传统优先级、外应/克应、应期、专业问事断法、正式网页接入。未做前端构建/浏览器验收，因为前端及原路由完全未改；不能把本离线原型宣传为正式上线。
