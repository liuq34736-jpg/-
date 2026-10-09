# Day 4 实际测试结果

验收日期：2026-10-09。独立目录 `D:\算卦工具\divination-web`。本轮真实付费 AI 调用 **0 次**。

## 已执行

| 检查 | 实际结果 | 范围 |
| --- | --- | --- |
| 新项目 unittest | **94 collected / 94 passed / 0 failed / 0 skipped** | 保留 Day 3 的 57 项，新增 Day 4 的 37 项 |
| 旧系统允许范围回归 | **99 / 99 / 0 / 0** | 起卦、分析、旺衰、结构解释、daily_reading 五个测试模块；只读保护下运行 |
| 384 组合矩阵 | **384 passed / 0 failed** | 每例确定性结果正确，384/384 均有四角色已批准解释 |
| Chrome 浏览器 | **92 passed / 0 failed** | 保留并更新原 64 项；新增 28 项实际起卦/安全/响应式检查 |
| 离线 API 失败样例 | **16 passed / 0 failed** | 请求拒收及 503；明确未访问厂商 |
| ESLint | **通过，0 error / 0 warning** | ESLint 9 配置保持有效 |
| TypeScript + Vite build | **通过** | 当前入口构建；JS 297.43 kB、CSS 76.40 kB（未压缩体积） |
| pip check | **通过** | 独立虚拟环境依赖一致性 |
| pnpm audit | **1 high，0 moderate，0 critical** | 已知 braces，无已发布补丁；audit 按预期返回非零，不能描述为全绿 |
| Git 候选 / 暂存安全扫描 | **通过** | 只输出命中数和路径，不输出密钥 |
| 密钥精确内存比对 | **0 命中** | 当前新项目 Git 候选、runtime 日志/收据和前端构建产物 |
| 生产完整性 | **通过** | 157 个基线文件、509 签名缓存、42 历史记录均未改变 |

没有重新运行原生产测试全集或真实问事 AI 质量验收。选择的 99 项回归不应被写成整个生产测试全集通过。没有运行整套 Python CVE 审计，`pip check` 不证明所有 Python 包无漏洞。

机器可读：[新项目单元测试](day4_unit_results.json)、[旧系统回归](day4_legacy_results.json)、[384 组合](day4_matrix_results.json)、[Chrome 逐项](day4_browser_results.json)、[依赖 audit](day4_dependency_audit.json)、[密钥边界](day4_secret_boundary_result.json)、[生产完整性](day4_production_integrity_result.json)、[新项目保护](day4_new_project_integrity.json)。

## 黄金案例

同一时间均为 `2026-09-24T19:45:35+08:00`。

| 输入 | 本卦/动爻 | 互卦 | 变卦 | 体/用 | 生克 | 时令 |
| --- | --- | --- | --- | --- | --- | --- |
| 手动 20 / 4 | 观 / 六四 | 剥 | 否 | 坤土 / 巽木 | 用木克体土 | 酉月、金当令、体平、用衰 |
| 手动 17 / 2 | 随 / 六二 | 渐 | 兑 | 兑金 / 震木 | 体金克用木 | 酉月、金当令、体旺、用衰 |
| 时间起卦 | 观 / 六四 | 剥 | 否 | 坤土 / 巽木 | 用木克体土 | 酉月、金当令、体平、用衰 |

三个样例均由真实 Chrome 页面发往实际本机后端，四角色均为 SEMANTIC_APPROVED。具体 API 响应见 [成功样例](day4_api_success_examples.json)，只包含合成测试问题和公开资料。

## 覆盖详情

- 64 卦覆盖全部 8 个上卦和下卦、64 种组合、6 个爻位、阴阳爻标准名。
- 384 例逐一验证本卦不变、动爻位不变、只翻转该爻、互卦取爻顺序、体用所属三爻卦、五种关系标签及四角色证据。
- 22:59、23:00、00:00、01:00 边界；23 点时支进入子但农历日期仍是十四，午夜进入十五；Z/+08:00 同瞬间结果相同。
- 更换问题不改变任何计算字段和标准解释。更换手动起卦时间只改变时令，不改变本卦/动爻/互卦/变卦/体用。
- 0、65、负数、爻 0/7、bool/float/字符串整数、缺失字段、未知字段、超长问题、非法日期/偏移、无时区等全部拒绝。
- 生产子进程写入试探和网络试探均被阻止；无迁移、无生产 DB 连接；无来源/Frame 生成。
- 可靠解释不可用的内存 fixture，四角色安全退回冻结结构描述，不发 AI 请求。
- 页面实测 6 条爻、第四爻朱砂高亮、底部为第 1 爻、资料/版本默认折叠。
- React 纯文本问题展示；HTML 事件注入未执行；非法状态字段、客户端认证、外部 Origin 和异常回显继续拒绝。
- 模拟 503 后移除旧结果并显示固定中文错误，不显示原始异常/JSON。
- Chrome 154.0.8037.99：桌面 1440×1100、移动模拟 390×844、窄窗口 320px 无水平溢出；页面错误 0、外部浏览器请求 0、客户端认证头 0。
- 3 条 console error 来自 2 个故意断网检查和 1 个模拟 503，不是额外异常。手机是 Chrome 模拟，手机真机和远程部署 **未验证**。
- FastAPI/Starlette TestClient 的 httpx 迁移弃用提示仍存在；不影响本轮结果。

## 复现命令

```powershell
Set-Location -LiteralPath 'D:\算卦工具\divination-web'
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -X utf8 scripts/day4_offline_checks.py legacy
.\.venv\Scripts\python.exe -X utf8 scripts/day4_offline_checks.py matrix
.\.venv\Scripts\python.exe -X utf8 scripts/day4_api_failure_examples.py
.\.venv\Scripts\python.exe -X utf8 scripts/browser_smoke.py --playwright-path 'D:\算卦工具\streamlit_mvp\.test_tools\v1_final_browser'
.\.venv\Scripts\python.exe -X utf8 scripts/verify_production.py --day4
.\.venv\Scripts\python.exe -X utf8 scripts/day4_new_project_integrity.py
.\.venv\Scripts\python.exe -X utf8 scripts/day3_security_check.py --day4
.\.venv\Scripts\python.exe -m pip check
pnpm --dir frontend lint
pnpm --dir frontend build
pnpm --dir frontend audit
```

Playwright 工具只读借用原有测试目录，未安装到生产环境。回归只允许临时测试数据库，禁止生产/资料源写入以及网络连接。

## 截图

- [桌面手动表单](screenshots/day4-meihua-form.png)
- [观六四实际结果](screenshots/day4-meihua-guan-desktop.png)
- [随六二实际结果](screenshots/day4-meihua-sui-desktop.png)
- [冻结时间起卦](screenshots/day4-meihua-time-desktop.png)
- [390px 正常手机尺寸结果](screenshots/day4-meihua-mobile.png)
- [手机尺寸 XSS 测试，合成字符串](screenshots/day4-meihua-mobile-xss-check.png)
- [安全设置](screenshots/day4-settings.png)
- [隔离历史](screenshots/day4-history.png)
