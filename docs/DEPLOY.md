# 部署文档

## 目标架构

```
GitHub Actions（每日 08:00 北京时间）
  → sync：采集 → 计算 → 摘要 → 提交 data/ → nuxi generate → rsync 部署
  → backfill：每日小批量回溯 365 天历史
nginx（团队公网服务器）静态目录
  → 服务 frontend/.output/public 的产物
```

## 1. 服务器 nginx 配置

参考 `deploy/nginx.conf.example`：

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/github-star-trend
sudo ln -s /etc/nginx/sites-available/github-star-trend /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

创建静态目录并授权：

```bash
sudo mkdir -p /var/www/github-star-trend
sudo chown -R <deploy_user> /var/www/github-star-trend
```

## 2. 生成部署 SSH 密钥

在任意机器生成一对密钥（或复用现有密钥），把**公钥**添加到服务器 `~/.ssh/authorized_keys`：

```bash
ssh-keygen -t ed25519 -f deploy_key -N ""
ssh-copy-id -i deploy_key.pub <deploy_user>@<deploy_host>
```

把**私钥全文**配置为 GitHub Actions Secret `SSH_PRIVATE_KEY`，并设置：

- `DEPLOY_HOST`：服务器 IP/域名
- `DEPLOY_USER`：SSH 用户
- `DEPLOY_PATH`：nginx 静态目录，如 `/var/www/github-star-trend`

## 3. 配置 GitHub Secrets

仓库 Settings → Secrets and variables → Actions，配置 README 中的 Secrets 清单。

## 4. 首次部署验证

1. 推送代码到仓库
2. Actions 页面手动触发 **Daily Sync**（Run workflow）
3. 观察步骤：Run pipeline → Commit data → build → Deploy 全绿
4. 浏览器访问 nginx 地址，确认 5 个榜单页可打开

## 5. 告警验证（Task 22）

1. 设置 `NOTIFY_WEBHOOK`（团队群机器人或自建 Webhook）
2. 临时改坏一步命令（如给 sync 加不存在的参数），手动触发
3. 确认 Actions 失败且 **Notify on failure** 步骤执行成功（curl 200），收到告警
4. 撤销临时改动，再次手动触发确认恢复

## 6. 常见问题

- 部署失败 `Permission denied (publickey)`：SSH 私钥与服务器 authorized_keys 不匹配
- `rsync: command not found`：服务器需安装 rsync（`sudo apt install rsync`）
- 页面显示旧数据：数据提交成功但构建/部署失败，查看 Actions 日志
