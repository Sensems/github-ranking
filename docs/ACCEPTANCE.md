# 验收记录

对应 PRD v2.0 第八章验收标准。状态：✅ 已在本机验证；⏳ 待远程（推送 + Actions 运行后）验证。

| 模块 | 验收标准 | 状态 | 证据 |
|------|---------|------|------|
| 数据采集 | 候选池 ≥ 10,000；每日更新成功率 ≥ 95%；Search API 在限流内 | ⏳ | 需真实 GitHub API 运行 sync |
| 增速计算 | 四榜单可生成；抽样核对误差 ≤ 5%；缺失显示"数据积累中" | ✅ | `pytest tests/` 30 项通过（含 build_boards / tolerance / eligible 用例） |
| AI 摘要 | 重试后成功率 ≥ 95%；JSON 结构校验 100%；降级可用 | ✅/⏳ | 单测 4 项通过；真实调用待密钥配置 |
| 榜单页面 | 5 页可访问；首屏 < 2s；筛选/搜索/排序正常 | ✅ | `nuxi generate` 预渲染验证：5 页面、摘要、降级、sitemap 均确认 |
| 部署 | 静态站点自动更新；内网访问正常；失败时显示上次数据 | ⏳ | 需配置 Secrets 后手动触发 |
| 告警 | 人为失败一次，告警送达 | ⏳ | 流程见 docs/DEPLOY.md §5 |
| 年榜回溯 | 上线 2 周内年榜 Top 100 覆盖 ≥ 80% | ⏳ | backfill 单测通过；需线上运行积累 |

## 本机已验证明细

- `python -m pytest`：30 passed
- `cd frontend && npm test`：8 passed
- `npm run generate`：5 个榜单页 + 404/200 + sitemap.xml（5 个 loc）
- 预渲染 HTML 含：榜单标题、仓库名、Star 数、四维度增速、AI 摘要、"数据更新于"时间
- 摘要缺失时降级显示 description（Task 17 验证）
