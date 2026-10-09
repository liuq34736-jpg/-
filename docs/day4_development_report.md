# 问象纪 Day 4 开发交付

项目：`D:\算卦工具\divination-web`。完成日期：2026-10-09。阶段范围：冻结确定性计算 API + 已批准标准解释 + 网页操作；没有实施 Day 5。

## 分支与回退

工作分支：`day4/meihua-deterministic-api`。

Day 3 独立分支仍为 `day3/deepseek-security`，回退点 `c096ccd946ed926cf2161d0a9b6180d22c91bd9c`，未重写。品牌基线仍为 `e75fe153822348d79055668df9d0d63567ceae68`。本轮只做本地提交，无推送、无部署；提交记录见 [day4_git_commit_records.md](day4_git_commit_records.md)。

## 真正接入的能力

| 能力 | 实际状态 |
| --- | --- |
| 64 卦手动选择、六爻位置及六/九校验 | 已接入，目录/名称直接由冻结 Python 提供 |
| 时间起卦 | 已接入 traditional_meihua_datetime_v1，显式中国时间，midnight 换日 |
| 互卦、变卦、体用、生克、旺衰 | 已接入现有冻结模块，无算法复制或改写 |
| 标准结构解释 | 已接入 meihua_interpretation_v1，中性结构关系及规则依据 |
| 四角色已批准卦义 | 已接入现有签名/证据审核后的 Frame 及既有 renderer，仅基础含义 |
| 古籍引用与来源版本 | 已接入公开原典引用、版本、位置、核验状态和异文存在标记 |
| 用户问题 | 仅保留并安全展示；完全不参与计算或新的解释生成 |
| DeepSeek 安全配置状态 | 保留 Day 3；网页操作不调用厂商 |
| AI 个性化问事正文 | **未接入**，旧质量验收未通过，不作为本轮完成能力 |
| traditional_judgement_v1 | **未接入**，没有临时 AI 替代 |
| 网页历史保存 / 生产历史读取 | **未接入**；网页历史保持隔离空列表 |
| 塔罗、八字、六爻等扩展模块 | 仅保留入口，继续开发中 |
| 外网或手机真机联网 | **未验证 / 未部署**；只监听 127.0.0.1 |

## 适配层实现

```text
backend/app/
  main.py                 本机 API 与通用错误、安全边界
  meihua_models.py         严格请求/响应契约，中国时间输入
  meihua_adapter.py        固定解释器/路径、限并发、超时、安全公共输出
  meihua_worker.py         基线校验 + 只读调用冻结生产代码
frontend/src/platform/
  MeihuaPage.tsx           实际手动/时间表单、六爻图、结果与依据
  meihuaContract.ts        逐字段严格响应校验
  meihua.css               问象纪品牌下的响应式布局
tests/test_meihua_day4.py  37 项新增自动测试
scripts/
  day4_offline_checks.py          只读旧回归与 384 组合矩阵
  day4_api_failure_examples.py   离线拒收/失败样例
  day4_new_project_integrity.py  Day 3 保护文件与分支比对
```

普通请求链：严格 JSON 输入 → 固定子进程 → 核对冻结生产基线 → 原生产手动/时间算法 → analysis → strength → interpretation → 现有已批准 Frame/证据校验 → 原 renderer → 白名单公共响应 → 网页再次结构校验与纯文本显示。

没有导入生产 HistoryRepository，没有启动迁移，也没有调用 provider、语义生成、资料获取或缓存保存。现有 Frame 的角色包装和校验发生在内存中，不改原文本、receipt、签名、缓存或历史定义。Frame 不可用时用结构描述安全回退，不创造替代卦义。

子进程 `-I -B` 禁止写字节码，去掉 API/签名凭据环境变量；运行期拦截写文件、SQLite、网络等副作用。冻结生产文件变化时请求失败并给固定中文提示，不自动适配新算法。脚本只是适配边界，不声称 Python 层保护可安全执行任意恶意程序。

## 时间与黄金案例

网页支持 2000–2099 年带偏移的时间输入，归一为 UTC+08:00。23 点属于子时，农历日期仍在 00:00 换日。手动模式时间只用于时令；问题不送入计算子进程。

| 中国时间 2026-09-24 19:45:35 | 确定性结果 |
| --- | --- |
| 观第四爻 | 观六四，互剥、变否；体坤土，用巽木；用克体；酉月金当令、体平用衰 |
| 随第二爻 | 随六二，互渐、变兑；体兑金，用震木；体克用；酉月金当令、体旺用衰 |
| 时间起卦 | 观六四，互剥、变否；与冻结黄金案例一致 |

四角色基础文本均来自现有批准 Frame。不同问题在同卦同时间下得到相同全部计算和标准解释，只问事文本不同。

## 测试与安全现状

- 新项目：**94 tests passed**，其中 Day 4 新增 37；保留原 57。
- 允许范围旧回归：**99 passed**，没有运行整个旧生产测试全集或真实问事质量验收。
- 全量手动组合：**384/384** 正常，**384/384** 四角色均获批，0 crash。
- Chrome：**92/92**；build、lint、pip check 通过。
- 16 个离线失败样例通过；子进程写入与网络探测均被拦截。
- 前端无密钥、认证头或原始模型 JSON，精确密钥内存扫描 0 命中；本阶段真实 AI 请求 **0**。
- 依赖仍有此前的 **braces 1 high**，目前没有发布补丁。构建工具不接受用户 glob，告警保留未隐藏；不能把 audit 写成全绿。详见 [当前 audit](day4_dependency_audit.json) 和 [原安全分析](day3_security_dependency_report.md)。
- 新增 zod 3.25.76 与 lunar-python 1.4.8 均锁定，安装元数据为 MIT；前端 317 包、独立后端 19 包的许可证清单已更新。MIT 原版权声明不变。
- Chrome 是桌面浏览器与手机尺寸模拟；手机真机、Linux/远端服务器及公开 HTTPS 部署均未验证。

## 新旧项目完整性

最终检查见 [生产完整性](day4_production_integrity_result.json)、[新项目完整性](day4_new_project_integrity.json)。

- 157 个冻结生产文件 SHA-256：0 改变。
- 509 个签名缓存：0 改变。
- 42 条原历史：表结构、逐行哈希、数据库文件字节均一致。没有回写或重新解释。
- Day 3 已跟踪 181 个文件中只有列明的适配/UI/依赖/测试/报告工具预期改动，无非预期改动。
- DeepSeek Provider 实现、原连通性证据、一次调用保护脚本、生产基线、MIT、品牌配置、Vite CSP/代理和启动脚本均不变。
- Git 不包含运行日志、用户数据库、cache、.env、密钥或虚拟环境；截图和 API 示例只含合成测试问题。

检查范围是已记录基线及本轮新增内容，不宣称扫描了 Windows 的所有系统文件、日志或环境变量。

## 启动和访问

双击新项目的 `启动网页.bat`，或：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\算卦工具\divination-web\scripts\start-local.ps1"
```

- 梅花易数：[http://127.0.0.1:5173/modules/meihua](http://127.0.0.1:5173/modules/meihua)
- 首页：[http://127.0.0.1:5173/](http://127.0.0.1:5173/)
- 健康：[http://127.0.0.1:8765/api/v1/health](http://127.0.0.1:8765/api/v1/health)

已重新运行本项目停止/启动并通过 Chrome 检查。启动器/端口不改，只停止了本项目所有权已确认的服务，没有停止其他程序。当前端口均只在 127.0.0.1 监听。

## 交付与下一阶段

- [API 契约](day4_api_contract.md)
- [测试结果与截图](day4_test_results.md)
- [实际成功样例](day4_api_success_examples.json)
- [离线失败样例](day4_api_failure_examples.json)
- [问事解释质量修复建议](day4_question_quality_next_steps.md)

下一阶段建议仅是计划：先修复问事事实/条件/预测边界并独立验收，再决定是否接入正式个性化正文。Day 3 的连通成功、Day 4 的确定性计算通过都不改变旧问事质量 FAIL。到此停止，等待 Day 4 验收。
