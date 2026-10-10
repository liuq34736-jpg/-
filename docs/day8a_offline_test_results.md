# Day 8A：实际离线验收结果

日期：2026-10-10。付费 AI 请求：0。没有公开部署，没有生产资料/签名/历史写入。

## 结果汇总

| 检查 | 结果 | 机器证据 |
| --- | --- | --- |
| 新项目全部单元测试 | **458 collected / 458 passed / 0 failed / 0 skipped** | day8a_unit_results.json |
| 保留旧 Day7A 测试 | 405项全部保留；新增53项 | tests/test_day8a_quality.py |
| 生产允许范围内只读回归 | 99 collected / 99 passed / 0 failed / 0 skipped | day8a_legacy_results.json |
| 384冻结计算及四角色签名 | 384/384通过，0缺失Frame | day8a_frozen_matrix_results.json |
| 384预览路由 | 384/384通过，0 crash | day8a_preview_matrix_results.json |
| 原71完整条件判断回归 | 71/71完整结果SHA不变 | day8a_old71_results.json |
| 384公开预览结果与Day7A比较 | 384/384完整响应SHA不变 | day8a_integrity_results.json |
| 写入/网络/SQLite/签名损坏探针 | 全部阻止，原计算保留 | day8a_probes_results.json |
| 旧真实失败与新增对抗/Mock正例 | 30/30检查通过 | day8a_quality_evaluation_results.json |
| 实际回环HTTP取消/清理/504 | 4/4通过 | day8a_cancellation_probe_results.json |
| Chrome传统预览与展示修复 | 66/66通过 | day8a_preview_browser_results.json |
| Chrome原品牌/Day4页面 | 92/92通过 | day8a_base_browser_results.json |
| TypeScript+Vite production build | 通过 | 实际执行pnpm build |
| ESLint | 通过，0 error/0 warning | 实际执行pnpm lint |
| pip check | No broken requirements found | 兼容性检查，不等于完整CVE审计 |
| pnpm audit | 1 high / 0 moderate / 0 critical | day8a_dependency_audit.json；原braces告警 |
| 凭据/Git候选/前端产物/日志检查 | 凭据匹配0，私有运行文件未加入Git | day8a_security_results.json |
| 生产保护 | 157文件、509签名缓存、42历史不变 | day8a_integrity_results.json |

上表不同测试层有交叉覆盖，不将384矩阵、浏览器检查或测试子案例累加成“单元测试数量”。旧Streamlit全套872历史验收不是本轮执行结果，本轮执行其允许范围内99项只读回归。

## 资格与判断不变

| 原状态 | Day8A数量 |
| --- | ---: |
| 有限综合判断 bounded | 38 |
| 条件分支未决 | 14 |
| 未取得资格 | 4 |
| 未审核 | 328 |

资格仍52条；没有扩大到384爻。本轮样例包含观六四、随六二、乾上九、乾九四、明夷上六、解初六、屯九五、未审核案例及损坏证据安全回退。

## 测试方法与范围

384路由检查在内存ASGI执行实际请求校验、service、引擎、注册及响应模型；只将重复子进程运输替换为刚取得的384个受控签名输入。另独立重跑原冻结worker矩阵。不是384次浏览器点击，也没有付费API。

Chrome真实表单经运行中的127.0.0.1:5173/Vite→8765后端与原固定worker。状态损坏/额外字段/503/504与客户端挂起使用明确标记的浏览器传输替身，对应服务端来源损坏及取消另有真实代码探针；未改任何正式审核数据。

回环取消探针在临时本地端口运行实际ASGI及共享Vite取消处理器，只替换worker为测试sleeper。最后取消释放延迟0.082秒（直连）/0.061秒（代理）；压缩0.2秒期限返回504，实际约0.276秒。不能把压缩探针数字当成正常计算耗时或任何OS环境硬期限。临时服务已停止，原5173/8765未换端口。

新问事管线输入来源由原worker校验，只使用Mock。经营/关系两例的冻结计算与批准Frame相同；应用不同、全有证据、条件保留。离线结果`OFFLINE_ACCEPTED`不等于正式语义批准；真实AI的准确率、token、耗时、缓存零调用与历史重放未验证。

## 浏览器与截图

Chrome 154.0.8037.99；桌面1600×1100；窄屏390×844/320×740，Chrome移动模拟，实体手机未验证。

- `docs/screenshots/day8a-judgement-desktop-viewport.png`
- `docs/screenshots/day8a-judgement-mobile-viewport.png`
- `docs/screenshots/day8a-guan-evidence-desktop.png`
- 另存分支未决、随六二、乾上九、未审核和证据回退截图。

实测无外部浏览器请求、0敏感认证头、0页面错误；无Key/Authorization/模型原始JSON/人工确认按钮。原典摘录保持原字形标点。默认总论不重复完整动爻提醒；因素改编号参见；完整规则折叠保留。

## 发现过的失败及处理

1. 初版模拟取消通过、真实HTTP取消失败：补外层ASGI断连事件及代理上游关闭，复跑4/4。
2. 多段总论使旧浏览器单元素定位器失效：更新测试为验证每一段字体，不放宽检查；66/66。
3. “已经审核”资格声明变体漏检：新契约加拦截与回归，30/30。
4. 古老Day5基线将Day7A已有UI改动误算为新损坏：以本轮开始的Day7A 357文件基线审查，保留原生产基线；只允许6个运输/展示集成文件改动，其他全部不变。

## 剩余限制

- 保守词表不证明开放语义可靠；Mock六项true不证明真实核验器可靠。
- 固定Q14范围hold仅阻止已知语义扩大，不修补其他Frame隐含限制。
- 原braces high安全告警保留，没有安装新依赖或降低安全门槛；暂不适合公开部署。
- Starlette TestClient发出httpx兼容性弃用提醒，测试仍通过，本轮未升级依赖。
- 新AI契约未接入网页/API/生产历史；旧42历史只核对schema、每行SHA与数据库文件SHA，均相同。

## 复跑命令

在项目根目录执行：

```powershell
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_acceptance.py all
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_quality_evaluation.py
. scripts/local-runtime.ps1
$taskNode = Resolve-LocalNode
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_cancellation_probe.py --node $taskNode
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_integrity_check.py
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_security_check.py
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_preview_browser.py --playwright-path 'D:\算卦工具\streamlit_mvp\.test_tools\v1_final_browser'
.venv\Scripts\python.exe -B -X utf8 scripts/day8a_base_browser.py --playwright-path 'D:\算卦工具\streamlit_mvp\.test_tools\v1_final_browser'
```

前端在`frontend`目录执行`pnpm build`与`pnpm lint`，使用现有Node24。复跑证据仍仅写Day8A报告，不覆盖旧阶段交付。
