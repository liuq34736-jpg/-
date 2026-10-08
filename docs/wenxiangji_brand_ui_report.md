# 问象纪 · 品牌与界面验收

验收日期：2026-10-08。范围：独立网页的品牌、界面、测试及对应文档。

## 已完成

- 中文名称：问象纪；英文名称：WEN XIANG JI；标语：一事一问，观象明理。
- 左上角、手机顶部、首页、浏览器标题、网页元信息、页脚和当前项目说明均使用新品牌。
- 品牌文字与主色集中在 `frontend/src/config/brand.json`。页面初始化与 Vite HTML 处理共用该配置，不在各页面重复维护品牌名称。
- 主色 `#253934`，背景 `#F5F1E9`，强调色 `#A34F41`。标题使用系统宋体/衬线回退，正文使用系统字体，没有下载字体或背景图片。
- 桌面：左侧功能导航、右侧操作区；手机：顶部品牌栏、可展开的左侧导航抽屉。抽屉支持关闭、Escape、焦点循环与关闭后焦点恢复。
- 保留梅花易数、八字、塔罗、姓名分析、解梦、起名、姻缘；增加六爻的前端预留入口。八个入口均明确标注“开发中”，没有新增可执行占筮能力。

## 原创 Logo 与 favicon

本轮直接绘制 SVG 几何图形，未参考或下载其他网站的标志。开口框形表示提问与观察，内部短线表示整理与记录，朱砂圆点形成视觉锚点。没有使用龙凤、祥云、复杂纹饰或位图。

- `frontend/public/brand/mark.svg`：透明背景浅色图形，用于深绿色品牌栏。
- `frontend/public/brand/favicon.svg`：深绿色圆角底图，用于浏览器图标。
- 两个文件均为本地矢量资源，不含脚本、外部图片或外部依赖。

## 修改文件

| 文件 | 修改内容 |
| --- | --- |
| frontend/src/config/brand.json | 新增集中品牌配置 |
| frontend/src/config/brand.ts | 页面标题与品牌样式变量初始化 |
| frontend/src/config/modules.ts | 前端入口配置，含六爻开发中占位 |
| frontend/src/platform/PlatformPreview.tsx | 左侧导航、主页、移动抽屉、预览页面布局 |
| frontend/src/platform/preview.css | 品牌样式与响应式布局 |
| frontend/src/main.tsx | 初始化公共品牌配置 |
| frontend/index.html | 标题、favicon 和公共品牌元信息 |
| frontend/vite.config.ts | 构建/开发时从品牌配置生成 HTML 元信息 |
| frontend/public/brand/mark.svg | 原创 Logo 图形 |
| frontend/public/brand/favicon.svg | 浏览器图标 |
| tests/test_brand_ui.py | 新增 10 项自动回归测试 |
| scripts/browser_smoke.py | 扩充真实 Chrome 界面回归及截图 |
| README.md、docs/LOCAL_START.md | 当前品牌与启动说明 |

测试结果、截图和本报告均生成于新项目的 `docs/`。

## 构建与测试实测

| 检查 | 结果 |
| --- | --- |
| pnpm build | 通过；TypeScript 编译与 Vite 构建成功 |
| Python unittest | 26 通过 / 0 失败，包含原有 16 项与新增 10 项 |
| Chrome 浏览器检查 | 56 通过 / 0 失败，较原有 23 项增加 33 项检查 |
| 桌面视口 | Chrome 154.0.8037.99，1440 × 1100 |
| 手机视口 | 同一真实 Chrome 的移动设备模拟，390 × 844，触屏、DPR 2 |
| 窄窗口 | 320px 检查通过，无横向溢出 |
| 外部浏览器请求 | 0 |
| 客户端认证头 | 0 |
| JavaScript 页面错误 | 0 |
| 控制台错误 | 仅两次主动中断后端请求测试产生的预期网络错误 |

覆盖品牌名称、英文标识、浏览器标题、三种品牌颜色、Logo 加载、favicon、桌面左右布局、八个模块、开发中标识、禁用执行按钮、手机导航、设置、历史、路由刷新、失败提示、无密钥输入/原始 JSON、无客户端认证头及无外部请求。

首次 Chrome 检查发现 Vite 对子页面的 favicon 路径重写产生多余斜杠。品牌替换改为 HTML 预处理阶段执行，增加子页面刷新回归；最终复测全部通过。

浏览器结果：`docs/wenxiangji_browser_results.json`。

原有 ESLint 9 配置问题未在本轮处理，不能将本次构建和测试通过描述为 lint 已通过。Python 测试存在既有 Starlette/httpx 弃用提示，不影响测试通过。

## 真实浏览器截图

所有截图由本机安装的 Chrome 渲染并保存，没有使用设计稿模拟网页。

- 桌面首页：`docs/screenshots/wenxiangji-desktop.png`
- 手机首页：`docs/screenshots/wenxiangji-mobile.png`
- 手机导航：`docs/screenshots/wenxiangji-mobile-navigation.png`
- 梅花入口：`docs/screenshots/wenxiangji-meihua.png`
- 设置：`docs/screenshots/wenxiangji-settings.png`
- 历史：`docs/screenshots/wenxiangji-history.png`

手机截图属于浏览器设备模拟，不代表手机真机访问验收。当前只监听本机，未开放局域网或外网。

## 本地服务与隔离

- 原启动器复测通过，识别现有服务并复用，没有启动重复进程。
- 前端：`http://127.0.0.1:5173/`。
- 后端：`http://127.0.0.1:8765/api/v1/health`。
- 两个端口仅监听 `127.0.0.1`。没有变更端口、启动脚本或后端行为。
- CSP、前端环境变量前缀、同源代理及原有安全隔离保持不变。
- 真实 Provider、API 环境变量、生产数据库均未接入。本轮没有读取真实 Key 或调用付费 AI。
- 六爻是前端开发中入口，后端原有七模块接口与测试结果不变。
- 上游 MIT License 和 Copyright (c) 2023 dreamhunter2333 保留，页面页脚仍显示版权来源。

## 完整性比对

`scripts/verify_production.py` 实测：

- 157 个生产文件：全部不变。
- 509 个已签名/语义缓存文件：全部不变。
- 42 条生产历史记录：数据库结构、记录哈希和数据库字节全部不变。

本轮开始时额外记录新项目 9 个保护文件的 SHA-256；结束比对全部一致，包含后端实现、后端锁文件、前端 package/lock、MIT License 和四个启动服务脚本。

结果记录：`docs/production_integrity_result.json`、`docs/wenxiangji_protected_files_result.json`。

本轮没有修改 Streamlit 生产系统、任何梅花算法或历史数据，没有提前执行 Day 3 API 开发。当前 Git 分支仍为 `week1/day1-day2`，修改留在本地工作区，未提交或推送。

状态：品牌与界面改造完成，等待用户验收。
