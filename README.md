# GitHub Star 趋势排行榜

团队内部使用的 GitHub 项目发现与趋势分析工具：

- 每日采集按 Star 排序的 **Top 10,000** 仓库，沉淀滚动历史快照（400 天）
- 计算 **日 / 周 / 月 / 年** 四维度增速榜单（Top 100）
- 调用**讯飞星辰 MaaS（Astron）**大模型对榜单仓库生成中文摘要
- Nuxt 3 静态站点（预渲染、SEO 友好），部署到团队 nginx
- 全程 GitHub Actions 驱动，无常驻服务端

## 目录结构

```
scripts/    Python 数据管道（config/data_files/github_client/pool/snapshot/growth/summary/backfill/main）
tests/      pytest 测试
frontend/   Nuxt 3 静态站点（app/ 为 srcDir）
data/       管道产物：repos.json、history/*.csv、readmes/、summaries/、leaderboards/
deploy/     rsync 部署脚本与 nginx 示例配置
.github/    sync.yml（每日同步）、backfill.yml（历史回溯）
```

## 本地开发

```bash
# Python 管道
pip install -r requirements.txt
python scripts/main.py sync       # 每日全流程（需要 GITHUB_TOKEN 环境变量）
python scripts/main.py stage      # 榜单 JSON 复制到 frontend/app/data/leaderboards
python scripts/main.py backfill   # 365 天历史回溯（按批）

# 前端
cd frontend
npm install
npm run dev        # 开发服务器
npm run generate   # 静态构建，产物在 frontend/.output/public
npm test           # Vitest

# 全部 Python 测试
python -m pytest
```

## GitHub Actions Secrets

| Secret | 用途 |
|--------|------|
| `GH_TOKEN` | GitHub PAT（public_repo 读取权限） |
| `XFYUN_API_KEY` | 讯飞星辰 MaaS API Key |
| `XFYUN_BASE_URL` | 讯飞 API Base URL（以官方文档为准） |
| `XFYUN_MODEL` | 模型 modelId（默认 xsparkx2） |
| `DEPLOY_HOST` / `DEPLOY_USER` / `DEPLOY_PATH` | 目标服务器与 nginx 静态目录 |
| `SSH_PRIVATE_KEY` | 部署用 SSH 私钥 |
| `NOTIFY_WEBHOOK` | 失败告警 Webhook |

## 文档

- [部署文档](docs/DEPLOY.md)
- [日常运维](docs/OPERATIONS.md)
- [验收记录](docs/ACCEPTANCE.md)
