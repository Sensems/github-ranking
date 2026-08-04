# 部署文档

## 目标架构

```
GitHub Actions（每日 08:00 北京时间）
  → sync：采集 → 计算 → 摘要 → 提交 data/ → nuxi generate → 部署 GitHub Pages
  → backfill：每日小批量回溯 365 天历史
```

站点地址：`https://Sensems.github.io/github-ranking/`

## 1. 首次配置（一次性）

1. 推送代码到仓库
2. 仓库 Settings → Pages → **Source 选择 "GitHub Actions"**
3. 在仓库 Settings → Secrets and variables → Actions 配置：
   - Secrets：`GH_TOKEN`、`XFYUN_API_KEY`、`XFYUN_BASE_URL`、`XFYUN_MODEL`、`NOTIFY_WEBHOOK`（后两个可选）
   - Variables（可留默认值）：`NUXT_APP_BASE_URL=/github-ranking/`、`SITE_URL=https://Sensems.github.io/github-ranking`
4. Actions 页面手动触发 **Daily Sync**（Run workflow）
5. 观察步骤：Run pipeline → Commit data → build → Upload artifact → Deploy to GitHub Pages 全绿
6. 访问站点地址，确认 5 个榜单页可打开

> 站点是公网公开的（GitHub Pages 免费/Pro 计划不支持私有站点）。如需内网部署，见 §4。

## 2. 构建路径说明

- `nuxt.config.ts` 中 `baseURL` 取环境变量 `NUXT_APP_BASE_URL`，工作流默认 `/github-ranking/`
- 若部署到用户页（`Sensems.github.io` 根路径），把 Variable 改为 `/`
- `SITE_URL` 仅用于 sitemap.xml 生成

## 3. 告警验证

1. 设置 `NOTIFY_WEBHOOK`（团队群机器人或自建 Webhook）
2. 临时改坏一步命令（如给 sync 加不存在的参数），手动触发
3. 确认 Actions 失败且 **Notify on failure** 步骤执行成功（curl 200），收到告警
4. 撤销临时改动，再次手动触发确认恢复

## 4. （可选）自建 nginx 部署

如需部署到团队内网服务器：

1. 服务器安装 nginx + rsync，参考 `deploy/nginx.conf.example` 配置静态目录
2. 生成 SSH 密钥对，公钥加入服务器 `~/.ssh/authorized_keys`
3. 配置 Secrets：`DEPLOY_HOST`、`DEPLOY_USER`、`DEPLOY_PATH`、`SSH_PRIVATE_KEY`
4. 在 `sync.yml` 中把 GitHub Pages 两步（Upload artifact / Deploy）替换为：

```yaml
      - name: Deploy to nginx
        run: bash deploy/deploy.sh
        env:
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
          DEPLOY_PATH: ${{ secrets.DEPLOY_PATH }}
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
```

5. 同时把 `NUXT_APP_BASE_URL` 改为 `/`（nginx 部署在域名根路径）

## 5. 常见问题

- Deploy 步骤报 "not allowed"：Settings → Pages → Source 未设为 GitHub Actions
- 页面样式错乱/404：`NUXT_APP_BASE_URL` 与实际路径不一致，重新生成并部署
- 页面显示旧数据：数据提交成功但构建/部署失败，查看 Actions 日志
