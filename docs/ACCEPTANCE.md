# 验收记录

对应 PRD v2.0 第八章验收标准，适配 **PostgreSQL + Nuxt Nitro SSR** 架构。  
状态：✅ 本机单测/构建已验；⏳ 待生产（Actions → Postgres → 服务器部署）联调。

| 模块 | 验收标准 | 状态 | 证据 |
|------|---------|------|------|
| 网络 | Actions runner 能 TCP 连接 Postgres | ⏳ | 见 docs/DEPLOY.md §0；上线前必测 |
| 数据采集 | 观察集写入 DB；每日 sync 成功率 ≥ 95% | ⏳ | 需配置 `DATABASE_URL` + `GITHUB_TOKEN`（Actions 用 secret `GH_TOKEN`）跑 sync |
| 增速计算 | 四增长榜 + 总榜可生成；误差 ≤ 5%；缺失显示「数据积累中」 | ✅/⏳ | `pytest tests/`；冷启动年榜 sparse 为预期 |
| AI 摘要 | 重试后成功率 ≥ 95%；JSON 校验；降级可用 | ✅/⏳ | 单测通过；真实调用待密钥 |
| API | `/api/health`、`/api/leaderboards/*` 读 Postgres | ✅/⏳ | Nitro 路由单测；联调待 DB |
| 榜单页面 | 5 页 SSR 可访问；筛选/搜索/排序正常 | ✅/⏳ | `npm run build` + `npm run preview` 或 dev |
| 部署 | Daily Sync 成功后 SSH 部署 Nitro；失败保留 DB 中上次数据 | ⏳ | 需 `DEPLOY_*` + 服务器 systemd/pm2 |
| 告警 | 人为失败一次，Webhook 送达 | ⏳ | 流程见 docs/DEPLOY.md §3 |
| 年榜回溯 | 上线 2 周内年榜 Top 100 覆盖 ≥ 80% | ⏳ | backfill 写 `snapshots`；需线上积累 |

## 冷启动验收（空库 → 首次 sync）

1. `python scripts/main.py migrate` 成功
2. `python scripts/main.py sync` 成功
3. 五个 `GET /api/leaderboards/{type}` 返回 200（yearly 可能 `items: []`）
4. UI 五 tab 可切换，空榜显示友好文案
5. 第二日 sync 后，watch set 含前日增长榜成员（观察 `repos` / 榜单变化）

## 本机已验证明细

- `python -m pytest`：管道与 DB 层单测
- `cd frontend && npm test`：composable / API 路由单测
- `npm run build`：Nuxt SSR 产物在 `frontend/.output/`
- 摘要缺失时 UI 降级显示 description

## 已退役路径（不再验收）

- GitHub Pages 作为主站点
- `python scripts/main.py stage` 复制 JSON 到 frontend
- `data/` 文件作为数据源或 git 恢复手段
