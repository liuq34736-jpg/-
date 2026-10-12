# Day 8B-1：完整性与隔离

日期：2026-10-12。基线提交 `0944d7d`，回退点保留；分支 `day8b1/budget-executor`。

| 保护对象 | 本轮实际结果 |
|---|---|
| Day8B已有427个Git文件 | 开始前记录SHA256；最终全部一致，旧文档/前后端代码/依赖/许可证未修改 |
| Streamlit生产157个关键文件 | 与原production_baseline.json完全一致 |
| 原509个签名缓存文件 | 与原基线一致 |
| 原42条历史 | 只读mode=ro查询；表结构、每行SHA256、SQLite文件字节SHA256全部一致 |
| Day6A/Day6B审核目录 | 属于原Git基线，未改变；没有扩大剩余爻资格 |
| Git候选安全检查 | 未发现凭据模式或数据库、日志、runtime/private文件加入候选 |
| 新公开接口/公开部署/生产写入 | 0 |
| 真实付费模型请求 | 0 |

本轮只新增独立工具和报告。原起卦、互变、体用、旺衰、古籍、SemanticFrame、签名及历史未编辑。完整性机器记录见 `day8b1_acceptance_results.json`；Git暂存安全记录及最终检查见 `day8b1_final_integrity_results.json`。

Mock账本、登记及锚点位于Git忽略的private目录；官方Tokenizer及临时依赖继续留在原runtime内。没有将Key、Windows环境变量、完整认证头或敏感原始请求备份进Git。

未验证：真实厂商usage/schema兼容、真实模型质量、外部账户账单、公开部署权限与浏览器新视觉表现。本轮没有以计划或Mock代替这些验证。
