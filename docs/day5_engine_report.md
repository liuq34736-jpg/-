# Day 5：独立离线引擎报告

状态：**原型实现完成，等待独立验收；未接入网页**。规则版本 `traditional_judgement_v1`。本轮实际 AI 调用 **0**。

## Git 与保护

- 开发分支：`day5/traditional-judgement-offline`。
- Day 4 回退提交：`d8227cbe740d6a22f7a4b2890ecd4ab1ba6ddd6c`。
- Day 3 回退点仍保留：`c096ccd946ed926cf2161d0a9b6180d22c91bd9c`。
- Day 5 只新增独立文件。Day 4 的 218 个已有受版本管理文件，包括网页、API、启动器、Provider、依赖和旧测试，未修改。
- 生产基线 157 文件、509 个签名缓存与 42 条旧历史保持一致；数据库字节、表结构和逐行指纹一致。核验范围及结果见 [完整性报告](day5_integrity_results.json)。

## 文件结构

```text
backend/traditional_judgement_v1/
  __init__.py
  trusted_input.py  # 白名单请求 → 固定受保护子进程 → 不可变签发输入
  worker.py         # 直接复用 Day 4 FrozenRuntime 与原签名 Frame 校验
  rulebook.py       # 固定规则书与扫描页指纹，来源不足撤去规则资格
  engine.py         # 离线规则、定性修饰、语义保留、辅助分析与冲突
data/day5_judgement_rulebook.json
tests/test_traditional_judgement_day5.py
scripts/day5_offline_acceptance.py
scripts/day5_integrity_check.py
docs/day5_source_pages/   # 九张公共领域相关原页
```

没有复制/改写起卦、互卦、变卦、体用、五行或旺衰算法。新 worker 引用原 `FrozenRuntime`，原规则数据和原签名审核；辅助关系调用原 `relation_between`。

## 调用方式

```python
from backend.app.meihua_models import ManualInput
from backend.traditional_judgement_v1 import OfflineJudgementAdapter, TraditionalJudgementEngine

request = ManualInput(input_mode="manual_hexagram", hexagram_id=20, moving_line=4,
                      cast_at="2026-09-24T19:45:35+08:00")
trusted = OfflineJudgementAdapter().calculate(request)
result = TraditionalJudgementEngine().evaluate(trusted).to_dict()
```

这是开发者离线调用，没有 HTTP 路由。调用者不能向引擎提交任意原始计算 dict。输入包含签发封印、Day 4 输出、四个已校验 Frame、原体到辅助五行的冻结关系。

输入封印用于防止误传原始 dict 或无意改动，不是对同一 Python 进程内恶意代码的安全沙箱。实际隔离依靠固定只读子进程、原生产签名校验、固定规则指纹和不开放网页入口；测试中的私有签发调用仅用于构造不利 fixture。

## 主要输出

| 字段 | 内容 |
| --- | --- |
| traditional_tendency | 基础关系、基础方向、限定范围的 combined_tendency、原型限制 |
| body_use_and_strength | 原体用、原时令结果、修饰因子 ID；原关系不变 |
| key_moving_line | 已批准动爻原子语义、条件、禁忌及逐项证据 |
| semantic_context | 四角色已批准内容；不可用时结构 fallback |
| auxiliary_analysis | 原互/变数据、上下卦对原体关系、重复/冲突标记 |
| favorable_factors / adverse_factors | 每项含规则 ID 和原计算输入依据 |
| conflicts / uncertainties | 相反条件、缺失来源、未解决爻义极性和乾坤冲突 |
| rule_trace | DIRECT_SOURCE/现代解释/项目约定与原页引用 |
| semantic_source_references | 实际被 Frame 引用的可靠证据，区别于判断规则书 |
| calculation | Day 4 原输出，未改写 |

相同输入与相同来源状态返回相同 JSON，不生成动态随机结果或“当前生成时间”。输入和返回均作防御性复制。

## 黄金案例一：观六四

起卦时间 `2026-09-24T19:45:35+08:00`。本卦观、六四、互剥、变否、体坤土、用巽木、用克体；酉月金当令，体平、用衰。所有计算字段与 Day 4 相同。

- 基础传统方向：用克体，偏不利。
- 旺衰修饰：克体一方木衰，作用有时令限制；不改成生助，不推出“无事”。
- 关键动爻：直接保留已批准语义“看到国家的光彩景象，适合做宾客去辅佐君王”“这说明看重的是以宾客身份参与”，带四条爻辞/小象证据 ID。
- 互卦关系：艮土、坤土对体土均比和，为辅助有利因素。
- 变卦关系：未动体坤不重复；乾金对体土为体生用，保留辅助耗用提醒。
- 结构层综合：`mixed`，同时记录不利基础、弱克限制和辅助相反因素。
- **尚无动爻极性与体用的裁决**；以上不是全卦最终成败结论。

## 黄金案例二：随六二

相同时间。随、六二、互渐、变兑、体兑金、用震木、体克用；酉月金当令，体旺、用衰。所有计算字段与 Day 4 相同。

- 体用基础方向：体克用，偏有利；体旺为时令有利条件。
- 动爻提示：“顾着小的，就顾不上大的”“亲近这一边，另一边便失去，两者不能同时兼顾”，直接来自原批准 Frame，不能因体用偏利而抹掉取舍提醒。
- 互渐：艮土生体金、体金克巽木，作为辅助关系。
- 变兑：未动原体部分只作背景，另一兑金比和。
- 输出 `combined_tendency=favorable` **只表示上述生克层**；`semantic_polarity_included=false`，并不等于“六二全卦判断有利”。

完整可复查 JSON：[三个黄金输出](day5_golden_examples.json)。这里的 Frame 现代摘要不是新抄入的古籍原文，旧内容与批准状态未改动。

## 安全与失败处理

- 原守卫实际阻止生产写入、新项目 worker 写入、网络解析以及 SQLite 连接。不是仅模拟调用权限函数。
- 对真实已签名 Frame 改字后，原签名/语义工厂拒绝；该爻 fallback，另外三角色保留，全部冻结计算不变。
- 资料标 `needs_manual_check/rejected`、证据 ID 为空/错目标/内容指纹变化，不能进入具体语义。
- 规则来源不足时不生成该因素；缺少五关系来源时不凭辅助项生成总判断。
- 不读取 Provider 凭据，不接受模型名、API URL、模块路径、SQL 或原始 prompt，不显示底层异常。
- 不打开生产数据库进行业务操作；完整性工具仅 `mode=ro` 核对摘要，不输出历史内容。
- 网页没有新 route、没有启动时新 import、没有状态迁移或付费 AI 请求。

## 未完成且不应宣传完成

动爻语义的条件极性与跨层冲突裁决、传统“圆机”完整综合、领域占法、外应/克应、应期、个性化现实应用。判断原型未通过产品发布验收，现有 Day 4 正式页面保持原样。
