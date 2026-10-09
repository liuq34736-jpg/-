# 问象纪 Day 4 API 契约

适配版本：`meihua_service_adapter_v1`。实际后端仅监听 `127.0.0.1:8765`；网页通过 Vite 的本机 `/api` 代理访问。没有付费 AI HTTP 入口，也没有生产历史写入入口。

## 入口与请求白名单

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/v1/health` | 本地健康，stage=day4，real_ai_enabled=false |
| GET | `/api/v1/meihua/catalog` | 冻结 64 卦目录、上下卦、六爻及六/九标准名称 |
| POST | `/api/v1/readings` | 手动卦象或冻结时间起卦，以及标准结构分析 |
| GET | `/api/v1/ai/status` | Day 3 安全配置状态，不调用厂商 |
| GET | `/api/v1/history` | 隔离的空网页历史；不读取生产记录 |

POST 必须是 `application/json`，实际请求体上限 8,192 字节。重复 JSON 键、非有限数字、未知字段、类型强制转换均拒绝。

手动示例：

```json
{
  "input_mode": "manual_hexagram",
  "question_text": "近期推进一件事情，应当留意什么？",
  "hexagram_id": 20,
  "moving_line": 4,
  "cast_at": "2026-09-24T19:45:35+08:00"
}
```

时间示例：

```json
{
  "input_mode": "time_cast",
  "question_text": "近期推进一件事情，应当留意什么？",
  "cast_at": "2026-09-24T19:45:35+08:00"
}
```

| 字段 | 规则 |
| --- | --- |
| input_mode | 必填，只有上述两个枚举 |
| question_text | 可选，默认空字符串；严格字符串，最多 500 个字符；首尾空白去除；拒绝非法控制字和代理字符 |
| hexagram_id | 手动模式必填，严格整数 1–64；拒绝 bool、float、数字字符串 |
| moving_line | 手动模式必填，严格整数 1–6；位置 1 最下、6 最上 |
| cast_at | 可选，默认当前中国时间；ISO 8601 字符串，必须带 Z 或明确偏移；支持分钟/秒精度，拒绝不存在的日期 |

时间模式禁止提交 hexagram_id/moving_line。偏移绝对值不能超过 14 小时；统一换算到中国标准时间后限定在 2000–2099 年。此日期范围是网页接口限制，不是修改生产算法。

模型名、模块路径、文件路径、SQL、prompt、API URL、密钥、请求头等均不在输入模型中。浏览器提交认证配置会拒绝。问题文本不发给计算子进程、模型或生产仓储；它只在响应中原样作为上下文文本显示。

## 时间定义

- 计算时区固定为 UTC+08:00，返回 `timezone=Asia/Shanghai`，不采用服务器当前时区来决定起卦。
- 农历日期在 **00:00** 换日。**23:00–00:59** 为子时，不把 23 点自动当下一农历日。
- 时间起卦直接调用 `traditional_meihua_datetime_v1`，保留农历、年支、时支、上下卦总数及取余结果。
- `%8=0` 的取卦及 `%6=0` 的动爻由冻结算法执行；页面只显示结果。
- 手动模式只调用冻结的 `manual_hexagram_v1`。更换时间不会重新选择本卦、动爻、互卦、变卦或体用；只影响时令分析。
- 旺衰调用 `meihua_strength_v1`；返回节气交接时间统一为 +08:00，数值和状态不修改。

## 响应白名单

响应由 Pydantic 严格固定结构生成，网页再用 Zod 严格结构校验。没有直接返回生产 dict、模型原始返回、审核 receipt、签名、密钥、缓存内容或路径。

| 字段 | 含义 |
| --- | --- |
| api_version / input_mode / cast_at / timezone / line_order | 适配版本、方式、中国时间、bottom_up 顺序 |
| question_text / question_applied_to_calculation | 用户问题；后者固定 false |
| original_hexagram / mutual_hexagram / changed_hexagram | id、name、full_name、lines、binary、upper_trigram、lower_trigram |
| moving_line | position、自动校验的六/九名称、polarity（严格 0/1） |
| body_use | 固定规则版本、体用卦与五行、关系标签、冻结关系文字 |
| strength | 月建、当令五行、当前/下一节气及交接时刻、体/用状态、互/变辅助状态、来源 |
| time_calculation | 手动为 null；时间模式保留农历、年支时支数字、卦数取余、midnight 换日模式 |
| interpretation_units | 冻结中性结构陈述；每条带类型与规则版本依据 |
| standard_meanings | original_hexagram、moving_line、mutual_hexagram、changed_hexagram 四角色 |
| source_references | 原典文字、书名、版本、卷次、页面/段落位置、HTTPS 来源链接、核验状态、异文存在标记 |
| versions | 生产、起卦、分析、解释、体用、旺衰、来源与 Frame 版本 |
| ai_used / history_saved | 本轮均固定 false |

`standard_meanings.status=SEMANTIC_APPROVED` 表示读取现有已批准 Frame，经现有证据、来源指纹和签名规则验证后使用既有 renderer。未找到合法 Frame 时只能 `structure_fallback`，不调用 AI 补写。

资料引用只来自可用的 machine_verified/verified 原典。引用位置取原始 witness 元数据；没有确定的原书连续页码保持 `original_pages=null`，不把电子文本卷次/段落假称为印刷页码。正文只显示已批准的基础含义，没有按用户问题重新解释古籍或生成 Frame。

版本固定如下：

```text
production_version       1.2.0
casting_version          manual_hexagram_v1 或 traditional_meihua_datetime_v1
analysis_version         meihua_analysis_v1
interpretation_version   meihua_interpretation_v1
body_use_version         moving_trigram_is_yong_v1
strength_version         meihua_strength_v1
source_corpus_version    canonical_meihua_corpus_v1
semantic_frame_version   verified_semantic_frame_v1
```

## 安全失败

| 状态 | 情形 | 页面/响应行为 |
| --- | --- | --- |
| 400 | 客户端认证配置 | 固定中文拒绝，不回显值 |
| 403 | 未允许 Origin | 拒绝其他来源 |
| 413 | 请求体超限 | 提示缩短问题 |
| 415 | 非 JSON | 提示提交格式 |
| 422 | 未知字段、非法类型/范围/时间、重复键等 | 固定中文；不输出校验对象或问题文本 |
| 503 | 冻结基线不符、进程超时、并发容量或输出校验失败 | 不输出不完整结果；固定中文服务提示 |
| 500 | 意外错误 | 固定中文，不回显异常和内部路径 |

计算子进程最多同时 2 个，20 秒超时；网页 25 秒超时，提交期间锁定按钮。子进程固定路径、固定解释器，使用 `-I -B`，不继承 API/签名环境变量。运行期禁止文件写入、SQLite 连接、子进程再创建和网络连接；启动先核对冻结文件 SHA-256。此隔离是针对受信任冻结代码的副作用保护，不宣称 Python audit hook 是运行任意恶意代码的操作系统沙箱。

完整实际成功样例：[day4_api_success_examples.json](day4_api_success_examples.json)。离线失败样例：[day4_api_failure_examples.json](day4_api_failure_examples.json)。没有新建数据库、保存网页历史或连接个性化 AI 正文。
