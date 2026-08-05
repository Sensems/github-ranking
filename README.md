# GitHub Star 趋势排行榜

团队内部使用的 GitHub 项目发现与趋势分析工具：

- 每日采集 **观察集** 仓库（Top 500 ∪ 新秀 ∪ 前日增长榜成员），沉淀滚动快照（约 400 天）
- 计算 **日 / 周 / 月 / 年 / 总** 五维度榜单（Top 100）
- 调用**讯飞星辰 MaaS（Astron）**大模型对榜单仓库生成中文摘要
- **PostgreSQL** 为唯一数据源；**Nuxt 3 Nitro SSR** 提供页面与只读 API
- **GitHub Actions** 每日 sync/backfill 写库并 SSH 部署前端到自建服务器

## 目录结构

```
scripts/    Python 数据管道（config/db/github_client/pool/growth/summary/backfill/migrate/main）
db/         SQL 迁移（db/migrations/）
tests/      pytest 测试
frontend/   Nuxt 3 SSR（app/ 为 srcDir；server/api 读 Postgres）
deploy/     rsync 部署脚本与 nginx 示例
.github/    sync.yml（每日同步+部署）、backfill.yml（历史回溯）
docs/       DEPLOY / OPERATIONS / ACCEPTANCE
```

`data/` 为旧版文件管道产物目录，**已退出 git**；本地若存在仅供调试，勿提交。

## 本地开发

### 前置

- PostgreSQL 实例与空库 `github-ranking`
- 环境变量 `DATABASE_URL`（本地可用读写用户）

### Python 管道

```bash
pip install -r requirements.txt

export DATABASE_URL='postgresql://user:pass@localhost:5432/github-ranking'
export GITHUB_TOKEN='ghp_...'   # sync/backfill 需要

python scripts/main.py migrate    # 应用 db/migrations/
python scripts/main.py sync       # 每日全流程
python scripts/main.py backfill   # 365 天锚点小批量回溯
```

### 前端（Nitro SSR）

```bash
cd frontend
npm install

export DATABASE_URL='postgresql://user:pass@localhost:5432/github-ranking'
npm run dev        # 开发服务器（SSR + /api/*）
npm run build      # 生产构建 → .output/
npm run preview    # 本地预览构建结果
npm test           # Vitest
```

### 测试

```bash
python -m pytest
```

## GitHub Actions Secrets

| Secret | 用途 |
|--------|------|
| `DATABASE_URL` | Pipeline 读写 Postgres |
| `GH_TOKEN` | GitHub PAT（Actions secret → workflow 注入为环境变量 `GITHUB_TOKEN`） |

本地跑 sync/backfill 请设置环境变量 `GITHUB_TOKEN`（`scripts/config.py` 只读该名，裸 `GH_TOKEN` 无效）。
| `XFYUN_API_KEY` | 讯飞星辰 MaaS API Key |
| `XFYUN_BASE_URL` | 讯飞 API Base URL |
| `XFYUN_MODEL` | 模型 modelId（默认 xsparkx2） |
| `DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_PATH` / `SSH_PRIVATE_KEY` | SSH 部署 Nitro SSR，见 docs/DEPLOY.md |
| `DEPLOY_RESTART_CMD` | （可选）默认 `systemctl restart github-ranking` |
| `NOTIFY_WEBHOOK` | 失败告警 Webhook |

仓库级变量（Settings → Variables）：

| Variable | 默认值 |
|----------|--------|
| `SITE_URL` | `https://github-trend.example.com` |
| `NUXT_APP_BASE_URL` | `/` |

## 文档

- [部署文档](docs/DEPLOY.md) — 网络前置、Secrets、systemd/pm2、首次 migrate+sync
- [日常运维](docs/OPERATIONS.md) — sync/backfill、故障恢复（无 data/ 回滚）
- [验收记录](docs/ACCEPTANCE.md)
