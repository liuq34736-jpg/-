# Day 3 安全与依赖修复报告

日期：2026-10-08。范围：新项目本机运行链。结论：本阶段功能与安全回归通过，但保留一项明确的依赖 high 告警；不作为公开部署许可。

## Git 与密钥

- 品牌基线提交前检查候选文件及暂存区，未发现真实凭据格式；数据库、运行日志、缓存、Secrets 和私有文件禁止加入 Git。
- 上游两个已跟踪 `.env` 文件移出当前跟踪，本地文件保留并忽略；没有改写上游历史。
- `scripts/audit_git_safety.py` 持续检查候选/暂存区。源码中的 `src/cache/*.py` 是实现代码，区别于缓存数据。
- `scripts/day3_security_check.py` 只在内存中用当前凭据检查新项目 Git 候选、运行日志/收据和前端构建产物，报告不输出凭据或匹配内容。
- 本轮没有把配置对象、请求头或原始模型响应序列化；配置 repr 隐藏密钥。
- 真实请求仅一次、无重试；诊断脚本有排他创建的本阶段标记，浏览器无法发起诊断调用。

当前检查结果见 `day3_secret_boundary_result.json`。这不是对 Windows 所有进程、系统日志或浏览器扩展的审计。

## 已修复的依赖告警

| 原告警 | 原依赖 | 处理 | 最终情况 |
| --- | --- | --- | --- |
| GHSA-wrjc-x8rr-h8h6，moderate，Link/useNavigate 开放重定向 | react-router 6.30.6 | react-router-dom 固定升级到 7.18.4 | 原告警消除 |
| GHSA-337j-9hxr-rhxg，moderate，SSR 错误反序列化构造器注入 | react-router 6.30.6 | 同上，普通 BrowserRouter 保持兼容 | 原告警消除 |
| GHSA-rj75-hqrm-r3gf，moderate，选择器解析 CPU 耗尽 | postcss-selector-parser 6.x | workspace override 固定到 7.1.6，构建复测 | 原告警消除 |

升级中发现 7.18.0 尚有 RSC CSRF 告警 GHSA-qwww-vcr4-c8h2，继续升级至 7.18.4 后消除，没有保留这个中间风险版本。

依据：[React Router 重定向公告](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6)、[构造器注入公告](https://github.com/advisories/GHSA-337j-9hxr-rhxg)、[RSC CSRF 公告](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)、[PostCSS 公告](https://github.com/advisories/GHSA-rj75-hqrm-r3gf)。

## 无法彻底消除的告警

`braces 3.0.3`：GHSA-vfj7-8cjw-p6xm，high。审计数据库与 npm 发布状态未提供已发布修复版本，因此没有伪造补丁版本或隐藏该告警。[GitHub 公告](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) 明确列出暂无补丁。

- 在本项目，它由 Tailwind → chokidar/fast-glob/micromatch 的构建依赖引入。
- 已挂载 React 运行链和 Python API 不向它传入用户问题、模型响应或用户上传的 glob。
- Tailwind content 为仓库控制的固定扫描模式；没有用户上传源码、CSS 或 glob 的 HTTP 功能。
- 影响仍是构建/开发工具遇到恶意深层花括号模式时可能堆栈耗尽。不能据此宣称依赖已修复，也不能将本地输入边界视作公共服务安全证明。
- 下一步跟踪上游补丁；若另行升级 Tailwind 主版本，应独立验收样式与构建，不能在本阶段未经验证地换掉整个工具链。

最终 pnpm audit：**1 high / 0 moderate / 0 critical**。`pnpm audit` 因该 high 仍返回非零，报告原样保存于 `day3_dependency_audit.json`，不列为全绿。

## ESLint 与许可证

- 增加 ESLint 9 flat config，实际 lint 通过，0 error / 0 warning。配置按 [ESLint 官方迁移文档](https://eslint.org/docs/latest/use/configure/migration-guide) 使用。
- 修复类型、hook 依赖、无效 TS 抑制注释和异常反射，没有通过大范围忽略旧文件来伪造 lint 通过。
- ESLint 9.39.5 安装元数据仍提示该版本不再受支持。本轮按指定 ESLint 9 修复；未来工具链维护应另评估受支持版本。
- 前端新/升级依赖许可证经安装元数据核对；`dependency_licenses.json` 已更新：316 个前端包、18 个独立 Python 包，无 backend UNVERIFIED。
- 根 MIT License 和 Copyright (c) 2023 dreamhunter2333 保持原样，页面保留署名。没有安装新的 Python 网络 SDK。
- `pip check` 通过。未新增整套 Python CVE 扫描，不能把依赖一致性检查描述为 Python 所有漏洞审计。

## XSS / CSP / CORS / 异常

- 当前界面使用 React 文本节点显示公共状态；Chrome 注入 HTML 状态测试通过，无事件执行。
- 移除遗留 ResultDrawer 的 `dangerouslySetInnerHTML`，按纯文本处理。
- 禁用遗留 useDivination 的浏览器密钥及未经审核流式网络路径；原实现仍可在上游 Git 追溯。
- 当前入口仍只挂载独立 PlatformPreview；lint 限制重新导入旧凭据 store、旧占筮 hooks、旧页面/历史路径。
- CSP 不再允许任意内联脚本或 unsafe-eval：开发环境仅对 Vite/React 注入的实际脚本生成 SHA-256 许可，构建后脚本仅 self。样式仍允许 inline，以支持现有 React 布局；不能宣称 style-src 完全严格。
- 浏览器 connect-src 仅 self 与本机 HMR，不包含 DeepSeek。Chrome 实测无外部请求、无客户端认证头。
- CORS 仅允许两个明确的本机前端来源，无 wildcard、无凭据许可。陌生 Origin、客户端认证头与非法预检拒绝。
- 后端意外异常、验证错误仅给固定中文提示，不回显错误对象、请求体、认证头或上游错误体。日志不打印 provider config/request/response。
- 前后端保持 nosniff、no-referrer；增加 DENY 防嵌入。开发服务器仅监听 127.0.0.1。

## 仍未接入的部分

正式解卦、问事应用核验、生产历史、历史写入、登录、多用户权限和公开部署均未接入。旧上游设置/store 等参考代码仍留存但不挂载；未来不能绕过独立安全接口重新挂载它们。

后续如增加收费调用或写历史 HTTP 接口，须另验收受控请求、限额/并发、CSRF/会话、请求大小和快照白名单；本次只读状态接口不代替这些验收。
