# 部署文档

## 目标架构

```
GitHub Actions（每日 08:00 北京时间）
  → migrate → sync（写 Postgres）
  → backfill：migrate → 小批量回溯 365 天锚点（写 Postgres）

前端部署：人工 / 自有脚本（本仓库不通过 Actions SSH 部署）
  → 本机或服务器：npm ci && npm run build → 拷贝 frontend/.output/ → 重启 Node

PostgreSQL（系统唯一数据源）
  ↑ 读写（Actions pipeline）  ↑ 只读（Nuxt Nitro）
```

生产站点由服务器上的 **Nuxt Nitro（Node SSR）** 提供；nginx 反代到 `127.0.0.1:3000`。  
**不再使用 GitHub Pages**；**Daily Sync 只写库，不部署前端**。`data/` 历史不迁移，从空库重新积累。

## 0. 网络前置条件（上线前必须满足）

GitHub-hosted Actions runner 必须能 **TCP 连接** 到 Postgres 主机与端口。  
若 runner 连不上数据库，sync 无法成为数据源，请勿上线。

任选一种方案（详见架构设计文档）：

| 方案 | 说明 |
|------|------|
| **A. 公网 + 防火墙** | Postgres 监听可达地址；防火墙仅放行 GitHub Actions 出口 IP 段（及运维 IP）。建议使用独立 DB 用户、强密码、TLS。 |
| **B. Self-hosted runner** | 在与 Postgres 同网段的服务器上安装 Actions runner；`DATABASE_URL` 指向内网地址。 |
| **C. 隧道 / VPN** | 通过 WireGuard、Cloudflare Tunnel 等，让 runner 获得到 DB 的稳定路径。 |

角色建议（可选但推荐）：

- **pipeline 用户**：读写（Actions `DATABASE_URL`）
- **nuxt 用户**：只读（服务器进程 `DATABASE_URL`）

## 1. 首次配置（一次性）

### 1.1 数据库

1. 创建数据库 `github-ranking`（schema `public`）
2. 创建 pipeline 读写用户与 Nuxt 只读用户（或暂用同一用户，生产建议拆分）
3. 确认 runner → Postgres 连通（见 §0）

### 1.2 服务器

1. 安装 Node 20+、nginx
2. 创建部署目录，例如 `/var/www/github-ranking`
3. 在部署目录或 systemd/pm2 环境中配置 **运行时** DB URL（只读角色），**不要**在 `npm run build` 时依赖真实连接串。推荐设置 `NUXT_DATABASE_URL`；也可设置 `DATABASE_URL`（`getPool()` 会回退读取）
4. 参考 `deploy/nginx.conf.example` 配置反代到 `127.0.0.1:3000`
5. 用 systemd 或 pm2 跑 Nitro，进程/单元名约定为 **`github-ranking`**

> **入口路径**：将 `frontend/.output/` **内容**放到部署目录后，工作目录入口是 `server/index.mjs`（不是 `.output/server/index.mjs`）。可选使用 `deploy/deploy.sh` 做本机 rsync（需自备环境变量，Actions 不会调用）。

**systemd 示例**（`/etc/systemd/system/github-ranking.service`）：

```ini
[Unit]
Description=GitHub Star Trend (Nuxt Nitro)
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/github-ranking
Environment=NUXT_DATABASE_URL=postgresql://nuxt_readonly:YOUR_PASSWORD@127.0.0.1:5432/github-ranking
# 也可用 Environment=DATABASE_URL=...（getPool 回退）
Environment=PORT=3000
ExecStart=/usr/bin/node server/index.mjs
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now github-ranking
```

**pm2 示例**：

```bash
cd /var/www/github-ranking
export NUXT_DATABASE_URL='postgresql://nuxt_readonly:YOUR_PASSWORD@127.0.0.1:5432/github-ranking'
# 或: export DATABASE_URL='...'
export PORT=3000
pm2 start server/index.mjs --name github-ranking
pm2 save
```

### 1.3 GitHub Actions Secrets（仅管道写库）

仓库 **Settings → Secrets and variables → Actions**（勿把真实值写入仓库）：

| Secret | 用途 |
|--------|------|
| `DATABASE_URL` | Pipeline 读写 Postgres（`postgresql://user:pass@host:5432/github-ranking`）。可带 Prisma 风格 `?schema=public`，管道会自动去掉；推荐不写 `schema` |
| `GH_TOKEN` | GitHub PAT（Actions secret）；workflow 映射为环境变量 `GITHUB_TOKEN` |
| `XFYUN_API_KEY` | 讯飞星火 / 星辰 API Key（APIpassword） |
| `XFYUN_BASE_URL` | 如 `https://spark-api-open.xf-yun.com/agent/v1/` |
| `XFYUN_MODEL` | 如 `spark-x`（可选） |
| `NOTIFY_WEBHOOK` | （可选）失败告警 Webhook |

前端部署不需要 `DEPLOY_*` / `SSH_PRIVATE_KEY`。

### 1.4 首次 migrate + sync

在 **能访问 Postgres 的环境**（本机、服务器或手动触发 Actions）执行：

```bash
export DATABASE_URL='postgresql://pipeline_user:YOUR_PASSWORD@db-host:5432/github-ranking'
export GITHUB_TOKEN='ghp_...'   # 本地/脚本读取 GITHUB_TOKEN（非 GH_TOKEN）

pip install -r requirements.txt
python scripts/main.py migrate
python scripts/main.py sync
```

**冷启动预期**（空库第一次 sync 后）：

- 五个 API `/api/leaderboards/{total,daily,weekly,monthly,yearly}` 均可访问
- **总榜 / 日榜 / 周榜** 应有数据；**月榜** 可能较 sparse
- **年榜** 在首日通常条目很少或为空（需多日快照 + backfill 365 天锚点），UI 显示「数据积累中」属正常
- 第二次 sync 起，watch set 会合并前一日增长榜成员，行为逐渐稳定

然后手动触发 **Daily Sync** workflow，确认 migrate → sync 全绿（**不含**前端部署）。

### 1.5 手动部署前端

在能访问代码与服务器的机器上：

```bash
cd frontend
npm ci
npm run build
# 将 .output/ 内容同步到服务器部署目录，例如：
# rsync -az --delete .output/ user@host:/var/www/github-ranking/
# 或本机：bash ../deploy/deploy.sh（需自行 export DEPLOY_* / SSH_PRIVATE_KEY）

sudo systemctl restart github-ranking   # 或 pm2 restart github-ranking
```

### 1.6 验收访问

- 站点 5 个榜单页可打开
- `GET /api/health` 返回 DB 连通
- `GET /api/leaderboards/total` 等返回 JSON

## 2. 构建与部署路径

- **Actions**：只做 migrate + sync（写库）
- **前端**：人工 `npm run build`，把 `frontend/.output/` 内容放到部署目录后重启 Node
- DB URL 仅 **Nitro 进程运行时** 需要（推荐 `NUXT_DATABASE_URL`，或 `DATABASE_URL`）

## 3. 告警验证

1. 设置 `NOTIFY_WEBHOOK`
2. 临时改坏一步命令，手动触发 Daily Sync
3. 确认失败且 **Notify on failure** 执行成功
4. 撤销改动，再次触发确认恢复

## 4. 常见问题

| 现象 | 排查 |
|------|------|
| Sync 连不上库 | runner → Postgres 网络、`DATABASE_URL`、防火墙、TLS |
| 部署后 502 | Node 是否监听 3000；`systemctl status github-ranking` 或 `pm2 status` |
| API 5xx | 服务器进程是否配置了可读的 `NUXT_DATABASE_URL` / `DATABASE_URL`；入口是否为 `node server/index.mjs`；Postgres 是否可达 |
| 年榜长期为空 | 正常冷启动；确认 backfill workflow 在跑且 `repos.backfilled_365` 在增长 |
| 仍看到 GitHub Pages | 产品路径已切换 SSR；Pages 可关闭或仅作镜像，非主路径 |
