# Day 3 DeepSeek 配置来源与职责

## 复用依据

只读查看原生产系统 `iching/narration/providers/configurable.py`，SHA-256：

`784a445f927ef184bec8294a277328ebf2b612e6298a9edd9b02ea1473a43a6e`

本轮复用已验收的公开配置：

- provider：`deepseek`。
- endpoint：`https://api.deepseek.com/chat/completions`。
- model：`deepseek-flash`。
- 服务器环境变量：`DEEPSEEK_API_KEY`。
- 进程环境优先，Windows 用户环境作为补充。
- HTTPS、禁止重定向、20 秒超时、隐藏凭据的配置 repr 和安全错误分类。

本轮没有导入或执行原生产包，不向生产目录写入 pycache，不修改原配置文件。

官方接口与模型信息亦经 [DeepSeek 官方入门文档](https://api-docs.deepseek.com/) 核对；实际一次请求成功验证当前兼容性。访问日期：2026-10-08。

## Day 3 专用边界

`backend/app/deepseek.py` 是连通性诊断实现，不是正式问事或解卦实现。

- 固定诊断消息，只请求 `{"status":"ok"}`；不接受调用者传入普通 prompt。
- JSON object、thinking disabled、stream false、max_tokens 32。
- 一次尝试、零重试，区别于生产 Provider 的其他用途/预算策略。
- 请求只到锁定的官方地址；不接受客户端或环境变量指定其他 endpoint/model。
- 所有重定向均拒绝，环境代理不被使用；TLS 证书校验保持启用。
- 响应限制 64,000 字节，重复 JSON key、非 JSON、额外诊断字段、自由文本、截断响应均不通过。
- 诊断原文不返回网页、不保存为正式解读，不创建生产历史。

公开状态接口只输出配置状态，不验证在线认证、不调用上游。一次真实诊断结果单独记录于 `day3_api_connectivity_result.json`，不能用它推定正式问事解读质量。

## 下一阶段必须保留的约束

正式服务若接入，仍须使用现有受控请求类型、证据核验、签名、缓存和安全回退。不得把本诊断类扩展成接收任意字符串的自由问答接口；不得用连通性响应或未经审核的模型正文替代梅花结果。
