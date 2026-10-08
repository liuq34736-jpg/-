# Day 1–2 交付记录

日期：2026-10-08。仅新项目本地预览，未提前进入 Day 3–7。

## 目录与 Git

- 新项目：`D:\算卦工具\divination-web`，完整独立克隆。
- 分支：`week1/day1-day2`；上游 HEAD `2b73870e5400811f6f5172259d15aa767e06d194`。
- 原 origin 改名 upstream；本轮改动处于未提交工作区，未 commit、未 push、未部署。
- 原 LICENSE、src/、src-tauri/、assets、根 main.py/requirements 保留。新运行入口与这些旧 AI 路由隔离。

## 实际完成

- 两项目目录、起卦边界、问事审核、签名、缓存、历史回放、依赖及许可审查；后续复用清单见 architecture_and_migration_risks.md。
- 生产文件与历史只读 SHA-256 基线，后验全部一致。
- 新 FastAPI preview 服务与 React/TypeScript/Vite 前端运行成功，独立依赖环境及锁文件完成。
- 首页、设置、历史、梅花/塔罗/八字/姓名/解梦/起名/姻缘七个入口可打开；所有占筮执行能力明确标记未接入。
- 本地前后端只监听 127.0.0.1:5173 / 127.0.0.1:8765。
- Key环境变量检查、真实调用、生产服务适配、历史数据迁移均未执行。

## 成功及失败结果

| 检查 | 实际结果 |
|---|---|
| 新preview API unittest | 12/12 PASS |
| 真实Chrome smoke | 最终23/23 PASS；无额外AI调用 |
| TypeScript + Vite build | PASS；203.04kB JS，65.72kB CSS（未gzip） |
| pip check | PASS，无依赖冲突 |
| 启动 / 停止 / 再启动 | PASS；隐藏窗口、健康检查、正确地址 |
| 已占用端口再次启动 | 按预期拒绝，中文提示，不杀其他进程 |
| 模拟后端离线 | 页面中文非敏感提示；1条预期Chrome网络console error，0 page error |
| 外部页面请求 / 认证头 / localStorage | 0 / 0 / 空 |
| 生产文件 / 签名缓存 | 157/157、509/509 哈希相同 |
| 生产历史 | 42条，schema、逐行hash、数据库字节hash均相同 |
| 首次pnpm install | FAIL：构建脚本默认禁用；只允许esbuild后恢复 |
| 首次启动Windows PowerShell5 | FAIL：UTF-8无BOM中文脚本误读；已改UTF-8 BOM，复测PASS |
| 首次Chrome smoke | 22/23，标题换行导致测试可访问名称匹配错误；直接比对标题文本后23/23 |
| pnpm lint | FAIL：上游ESLint9缺少flat config；尚未修复，不声称全绿 |
| pnpm audit | 非零：仍有1 high、3 moderate，见依赖审查 |
| 旧系统全回归 | **本轮未验证**，之前报告893/893；按Day7计划后续执行 |
| 真机手机、真实AI、真实生产历史、完整新梅花结果 | **未验证 / 未接入** |

本轮新测试合计35项通过，不将它们计入旧系统893项，也不宣称平台全部业务功能已经完成。

## 页面截图

- 首页桌面：screenshots/home-desktop.png（1440px窗口）
- 首页窄屏：screenshots/home-mobile.png（390px窗口，非手机真机）
- 梅花入口：screenshots/meihua-preview.png
- 设置：screenshots/settings.png
- 隔离历史：screenshots/history.png

截图内容无Key、Authorization或原始AI响应；原Key存在性也尚未检查，不能把mock页面的结果用于证明真实Provider绝不会泄漏。

## 验收前需知

本地访问首页：http://127.0.0.1:5173/。启动详见 LOCAL_START.md。

后续风险：现有v1.2问事发布验收FAIL、4条依赖告警、ESLint缺配置、开发CSP不等于生产CSP、历史受控服务边界尚需实现、真实Provider兼容/密钥保护未验证、图像素材及Rust依赖许可未验证。

本轮已停止推进 Day 3–7，等待用户验收；不执行真实连通性测试。
