# 依赖与许可证审查（Day 1–2）

## 上游许可证

[上游 MIT License](https://github.com/dreamhunter2333/chatgpt-tarot-divination/blob/2b73870e5400811f6f5172259d15aa767e06d194/LICENSE)：Copyright (c) 2023 dreamhunter2333。根 LICENSE 原样保留；页面 footer 保留作者及 MIT 来源。不得去掉版权/许可全文。

上游 assets 图像本轮未使用。软件 MIT 不能单独证明所有第三方牌面/素材权利，素材许可证与未来 Tauri/Rust 全传递依赖仍为 **未验证**。本轮不构建桌面版、不打包上述图像。

## 已安装许可证清单

`docs/dependency_licenses.json` 根据 pnpm 当前解析图（排除更新后残留包）与 Python importlib.metadata 生成：

- 前端 315 个 name/version 对：MIT 267，Apache-2.0 18，ISC 15，BSD-2-Clause 8，BSD-3-Clause 3，0BSD 1，Python-2.0 1，CC-BY-4.0 1，BlueOak-1.0.0 1。
- 后端虚拟环境 18 个包（含 pip），许可证元数据均能读取。
- 特别记录：argparse 2.0.1 为 Python-2.0；caniuse-lite 1.0.30001814 数据为 CC-BY-4.0；minimatch 10.2.6 为 BlueOak-1.0.0。不能把所有依赖笼统称为 MIT。
- 本轮属于包元数据检查，不能代替最终分发附件/NOTICE 审查。发布时需保留相关 license/copyright/attribution；未做法律意见或独立逐字许可证评审。

React 18.3.1 / TypeScript 5.9.3 / Vite 6.4.4 / Tailwind 3.4.19；backend FastAPI 0.142.4 / uvicorn 0.54.0 / httpx 0.28.1。全部当前实际版本已固定，构建及本地测试兼容；生产 Streamlit 依赖未改变。

## 依赖安全结果

首次冻结上游 lock 安装：pnpm 报 esbuild 未授权构建；仅加入 esbuild allowBuilds 后安装成功。[pnpm 官方构建策略说明](https://pnpm.io/blog/releases/11.0)。

初次 pnpm audit 返回：38 high、23 moderate、2 low、0 critical；仅在原 package.json 兼容区间更新后复查：**1 high、3 moderate、0 critical、0 low**。保留首次和最终完整机器报告，没有把网络错误当作 0 漏洞。

| 依赖 | 风险级别 | 审计结果 / 处理边界 |
|---|---|---|
| react-router 6.30.6 | moderate ×2 | [反斜线重定向](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6)、[SSR错误反序列化](https://github.com/advisories/GHSA-337j-9hxr-rhxg)。公告需 >=7.18；本轮固定6.x，不贸然大版本迁移。预览仅固定本地route，无SSR，但未独立复现两项漏洞。 |
| braces 3.0.3 | high | [深层模式栈耗尽](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)。属于构建链；audit未给出修复版本。当前不接收外部模式输入，未独立证明绝对无影响。 |
| postcss-selector-parser 6.0.10 / 6.1.4 | moderate | [解析CPU耗尽](https://github.com/advisories/GHSA-rj75-hqrm-r3gf)，公告 >=7.1.6 修复。传递依赖升级兼容性尚未验证。 |

因此 **依赖安全检查未全绿，禁止对外发布**。后续应分别升级验证，不得把 mock 冒烟通过解释为真实问事服务已安全。

其他已知限制：ESLint 9.39.5 安装提示不再受支持，且上游没有 ESLint flat config，lint失败；Starlette TestClient 使用 httpx 有弃用警告但12项测试通过。Python依赖安全漏洞扫描本轮 **未执行**（pip check只验证依赖兼容，不是漏洞扫描）。
