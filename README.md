# GitHub Star 趋势排行榜

面向开源项目发现与趋势分析的 GitHub 排行榜。系统每日维护一组有限观察集，用本地快照计算 Star 增长，并通过 Nuxt SSR 提供总榜、日榜、周榜、月榜和年榜。

## 核心能力

- **五类 Top 100 榜单**：总 Star、日增、周增、月增、年增
- **本地增长快照**：只跟踪观察集，保留约 400 天，不依赖 GH Archive / BigQuery
- **按需中文概况**：用户点击生成后调用讯飞服务，结果写入 PostgreSQL；已有概况随榜单直接返回
- **SSR 数据台界面**：Nuxt 3 + Nitro + Tailwind CSS v4 + shadcn-vue
- **数据库单一事实源**：PostgreSQL 保存仓库、快照、概况和预计算榜单

## 当前架构

```text
GitHub Search / Repository API / Stargazers API
                        │
                        ▼
GitHub Actions
  08:00 migrate → sync        08:30 migrate → backfill
                        │
                        │ psycopg（pipeline 读写）
                        ▼
                  PostgreSQL
                        ▲
                        │ pg（榜单读取；按需概况读写）
                        │
Users ──► nginx / TLS ──► Nuxt Nitro SSR
                          ├─ 页面渲染
                          ├─ /api/leaderboards/*
                          └─ /api/repos/*/summary
```

运行边界：

- GitHub Actions 只负责迁移、同步和回溯，**不部署前端**
- Python 是定时 CLI 管道，**不是常驻 API 服务**
- Nuxt Nitro 与 PostgreSQL 部署在可稳定互通的服务器环境
- 前端通过人工或自有脚本构建并部署 `.output/`
- 旧 `data/` JSON/CSV 不迁移、不再作为数据源

## 排名与数据流

### 观察集

每日观察集取以下集合的并集并按 `repo_id` 去重：

1. GitHub Search 当前 Star Top 500
2. 最近 30 天创建且 Star ≥ 500 的新项目
3. 上一次日 / 周 / 月 / 年增长榜成员

仅观察集仓库会更新元数据并写入当天快照；离开观察集的历史行不会物理删除。

### 榜单

- **总榜**：观察集按当前 Star 降序取 Top 100
- **增长榜**：当前 Star 减去目标日期附近（±3 天）的最近快照
- 时间窗口：日 `1` 天、周 `7` 天、月 `30` 天、年 `365` 天
- 增长榜参与门槛：Star ≥ 1000，且仓库年龄不小于对应窗口
- sync 计算后整行覆盖 `leaderboards` 中的五个预计算榜单；Nitro 请求时不重新计算增长
- 冷启动后各增长榜会随每日快照逐步出现；年榜需要长期积累或由 backfill 补充约 365 天前的锚点

### 按需概况

每日 sync 不批量刷新 README 或生成 AI 概况：

1. 榜单 API 批量读取已有 `summaries`，有缓存的卡片直接展示
2. 没有缓存时，用户点击“生成概况”
3. Nitro 获取 / 复用 README，调用讯飞 API
4. `readmes` 与 `summaries` 持久化到 PostgreSQL
5. 后续请求直接复用缓存

## 数据模型

SQL 迁移位于 `db/migrations/`，是 Python 与 Nuxt 共用的 schema 来源。

| 表 | 用途 |
|---|---|
| `repos` | 观察集仓库元数据 |
| `snapshots` | 每日 Star / Fork 快照，主键 `(repo_id, date)` |
| `readmes` | 按需获取的 README 摘要原文与 hash |
| `summaries` | AI 中文概况 JSON 与生成日期 |
| `leaderboards` | 五类预计算榜单 JSON |
| `schema_migrations` | 已应用迁移记录 |

## 目录结构

```text
.
├─ scripts/                 Python 数据管道与 CLI
│  ├─ github_client.py      GitHub API 封装
│  ├─ pool.py               观察集构建
│  ├─ growth.py             增长计算与榜单生成
│  ├─ db.py                 PostgreSQL 领域操作
│  ├─ migrate.py            SQL 迁移执行器
│  └─ main.py               migrate / sync / backfill 入口
├─ db/migrations/           幂等 SQL 迁移
├─ tests/                   Python pytest
├─ frontend/                Nuxt 3 + Nitro SSR
│  ├─ app/pages/            五个榜单页
│  ├─ app/components/       业务组件
│  ├─ app/components/ui/    shadcn-vue 基础组件
│  ├─ app/server/api/       榜单、健康检查、按需概况 API
│  └─ app/server/utils/     pg 连接与概况服务
├─ .github/workflows/       Daily Sync / Backfill History
├─ deploy/                  rsync 脚本与 nginx 示例
└─ docs/                    部署、运维与验收文档
```

## 本地启动

### 1. 环境要求

- Python 3.12
- Node.js 22（推荐）
- PostgreSQL，数据库名建议为 `github-ranking`、schema 为 `public`
- 可访问 GitHub API 的网络；sync / backfill 推荐配置 PAT

> 不要提交真实数据库 URL、GitHub Token 或讯飞密钥。

### 2. 初始化数据库与数据

在仓库根目录：

```bash
python -m pip install -r requirements.txt

export DATABASE_URL='postgresql://pipeline_user:YOUR_PASSWORD@127.0.0.1:5432/github-ranking'
export GITHUB_TOKEN='github_pat_...'

python scripts/main.py migrate
python scripts/main.py sync
```

PowerShell 对应写法：

```powershell
$env:DATABASE_URL = 'postgresql://pipeline_user:YOUR_PASSWORD@127.0.0.1:5432/github-ranking'
$env:GITHUB_TOKEN = 'github_pat_...'

python scripts/main.py migrate
python scripts/main.py sync
```

可选回溯：

```bash
python scripts/main.py backfill
```

### 3. 启动 Nuxt

```bash
cd frontend
cp .env.example .env       # PowerShell: Copy-Item .env.example .env
# 编辑 .env，至少填写 NUXT_DATABASE_URL

npm ci
npm run dev
```

访问：

- 页面：<http://localhost:3000>
- 健康检查：<http://localhost:3000/api/health>
- 总榜 API：<http://localhost:3000/api/leaderboards/total>

如果 API 返回 `DATABASE_URL not configured`，确认 `frontend/.env` 中存在 `NUXT_DATABASE_URL`，然后完全重启 dev server。

## 环境变量

### Pipeline / GitHub Actions

| 变量或 Secret | 必需 | 用途 |
|---|---:|---|
| `DATABASE_URL` | 是 | Python 管道读写 PostgreSQL |
| `GITHUB_TOKEN` | 本地推荐 | Python CLI 使用的 GitHub PAT |
| `GH_TOKEN` | Actions 是 | Actions Secret，workflow 映射为 `GITHUB_TOKEN` |
| `NOTIFY_WEBHOOK` | 否 | Daily Sync 失败通知 |

Actions 中不需要配置讯飞变量；sync / backfill 不生成概况。

### Nuxt Nitro

| 变量 | 必需 | 用途 |
|---|---:|---|
| `NUXT_DATABASE_URL` | 是 | Nitro 连接 PostgreSQL；也兼容 `DATABASE_URL` |
| `PORT` | 否 | 监听端口，默认 `3000`（dev 也可用 `NUXT_PORT`；生产也可用 `NITRO_PORT`） |
| `NUXT_XFYUN_API_KEY` | 生成概况时 | 讯飞 API Key |
| `NUXT_XFYUN_BASE_URL` | 否 | 讯飞 API 地址 |
| `NUXT_XFYUN_MODEL` | 否 | 模型 ID |
| `SITE_URL` | 否 | sitemap / SEO 站点地址 |
| `NUXT_APP_BASE_URL` | 否 | 非根路径部署时的应用 base URL |

启用按需概况时，Nitro 数据库角色需要读取 `repos`、`leaderboards`、`readmes`、`summaries`，并能写入 `readmes`、`summaries`。

## API

| Method | Path | 说明 |
|---|---|---|
| `GET` | `/api/health` | PostgreSQL 连通性检查 |
| `GET` | `/api/leaderboards/:type` | 返回 `total/daily/weekly/monthly/yearly` 预计算榜单，并附加已有概况 |
| `GET` | `/api/repos/:repoId/summary` | 读取已缓存概况 |
| `POST` | `/api/repos/:repoId/summary` | 获取 README、按需生成并持久化概况；已有缓存时直接返回 |
| `GET` | `/sitemap.xml` | 服务端 sitemap |

未知榜单类型返回 `404`；数据库不可用返回 `5xx`；首次 sync 前缺少榜单行时返回空数组。

## 常用命令

```bash
# Python
python scripts/main.py migrate
python scripts/main.py sync
python scripts/main.py backfill
python -m pytest

# Frontend
cd frontend
npm run dev
npm run test
npm run build
npm run preview
```

## 自动任务与部署

- `Daily Sync`：每天 UTC `00:00`（北京时间 `08:00`）执行 migrate + sync
- `Backfill History`：每天 UTC `00:30`（北京时间 `08:30`）执行 migrate + backfill
- 两个 workflow 使用不同 concurrency group，可能重叠；快照写入和榜单替换均设计为幂等
- GitHub-hosted runner 必须能访问 PostgreSQL；可选公网防火墙、self-hosted runner 或隧道 / VPN
- 生产前端由运维手动执行 `npm ci && npm run build`，同步 `frontend/.output/` 内容并重启 Nitro
- nginx 负责 TLS 与反向代理；systemd / pm2 运行 `server/index.mjs`

详细步骤见 [部署文档](docs/DEPLOY.md)。

## 测试

```bash
python -m pytest

cd frontend
npm test
npm run build
```

Python 测试覆盖观察集、增长计算、迁移和管道流程；Vitest 覆盖筛选逻辑、RepoCard、Nitro 路由与页面契约。

## 文档

- [部署文档](docs/DEPLOY.md) — 网络前置、数据库权限、systemd / pm2 与手动部署
- [日常运维](docs/OPERATIONS.md) — sync、backfill、故障恢复与数据检查
- [验收记录](docs/ACCEPTANCE.md) — 当前验收项和上线检查
- [PostgreSQL + Nitro 架构设计](docs/superpowers/specs/2026-08-05-postgres-nitro-architecture-design.md) — 初始设计记录；当前运行方式以本 README 和部署文档为准
- [shadcn-vue 前端设计](docs/superpowers/specs/2026-08-06-shadcn-vue-frontend-design.md)

## 安全说明

- `.env`、连接串、PAT 和 API Key 不得提交到 Git
- 生产建议拆分 pipeline 读写用户与 Nuxt 最小权限用户
- PostgreSQL 若暴露公网，应启用 TLS、强密码和防火墙限制
- 任何曾出现在日志、截图或聊天中的真实凭据都应立即轮换
