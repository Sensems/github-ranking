# 部署文档

## 目标架构

```
GitHub Actions（每日 08:00 北京时间）
  → migrate → sync（写 Postgres）→ npm ci/build → SSH 部署 Nuxt SSR
  → backfill：migrate → 小批量回溯 365 天锚点（写 Postgres）
```

生产站点由服务器上的 Nuxt Nitro（Node）提供；nginx 反代到 `127.0.0.1:3000`。不再使用 GitHub Pages 作为主路径。

## 1. 首次配置（一次性）

1. 确认 Actions runner 能连上 Postgres（公网放行 / self-hosted runner / 隧道，三选一）
2. 服务器安装 Node、nginx；用 systemd 或 pm2 跑 Nitro：`node .output/server/index.mjs`（工作目录为部署路径）
3. 进程名/单元名约定为 **`github-ranking`**（`systemctl restart github-ranking` 或 `pm2 restart github-ranking`）
4. 参考 `deploy/nginx.conf.example` 配置反代到 `127.0.0.1:3000`
5. 生成 SSH 密钥对，公钥加入服务器 `~/.ssh/authorized_keys`
6. 仓库 Settings → Secrets and variables → Actions 配置（勿把真实值写入仓库文件）：
   - `DATABASE_URL`（pipeline 读写）
   - `GH_TOKEN`、`XFYUN_API_KEY`、`XFYUN_BASE_URL`、`XFYUN_MODEL`（可选默认）
   - `DEPLOY_HOST`、`DEPLOY_USER`、`DEPLOY_PATH`、`SSH_PRIVATE_KEY`
   - `DEPLOY_RESTART_CMD`（可选；默认 `systemctl restart github-ranking`）
   - `NOTIFY_WEBHOOK`（可选，失败告警）
7. 服务器进程环境提供运行时 `DATABASE_URL`（建议只读角色）；**不要**依赖 build 时注入
8. Actions 手动触发 **Daily Sync**，确认 migrate → sync → build → deploy 全绿
9. 访问站点，确认 5 个榜单页与 `/api/health`、`/api/leaderboards/*` 正常

## 2. 构建与部署路径

- CI：`npm ci` + `npm run build`（产出 `frontend/.output/`）
- `deploy/deploy.sh` rsync **整个** `frontend/.output/` 到 `DEPLOY_PATH`，再执行 `DEPLOY_RESTART_CMD`
- `baseURL` 默认 `/`（域名根路径）；`SITE_URL` 用于 sitemap
- `DATABASE_URL` 仅服务端运行时需要，构建步骤不要求

## 3. 告警验证

1. 设置 `NOTIFY_WEBHOOK`
2. 临时改坏一步命令，手动触发 Daily Sync
3. 确认失败且 **Notify on failure** 执行成功
4. 撤销改动，再次触发确认恢复

## 4. 常见问题

- Sync 连不上库：检查 runner → Postgres 网络与 `DATABASE_URL`
- 部署后 502：确认 Node 已监听 3000，且 restart 命令对应的 unit/pm2 名正确
- API 5xx：服务器进程是否配置了可读的 `DATABASE_URL`
