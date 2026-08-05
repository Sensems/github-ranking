# 日常运维

## 数据更新节奏

- 每日 **08:00 北京时间** `sync.yml` 自动运行（UTC 00:00 cron，可能延迟 15–30 分钟）
  - `migrate` → `sync`（写 Postgres）→ 构建 Nuxt → SSH 部署
- 每日 **08:30 北京时间** `backfill.yml` 自动运行小批量 365 天锚点回溯（仅写 DB）
- 失败自动重试 1 次；仍失败发送 `NOTIFY_WEBHOOK` 告警
- 可用 `workflow_dispatch` 手动补跑任意一次
- `sync` 与 `backfill` 使用 **独立并发组**，可同时运行；快照按 `(repo_id, date)` upsert，榜单按 type 整行替换，设计上可重叠

## 数据源说明（Postgres）

系统唯一数据源为 PostgreSQL，表结构见 `db/migrations/`：

| 表 | 用途 |
|----|------|
| `repos` | 观察集元数据 |
| `snapshots` | 每日 star/fork 快照（约 400 天滚动保留） |
| `readmes` | README 摘录（榜单候选） |
| `summaries` | AI 摘要缓存 |
| `leaderboards` | 预计算的五个榜单 JSON |

**不再有** 每日 `data/` git 提交；仓库中的 `data/` 目录已退出版本控制（本地调试产物可 gitignore 忽略）。

## 失败排查清单

| 现象 | 排查 |
|------|------|
| Search API 报 403 | Actions secret `GH_TOKEN`（映射为 `GITHUB_TOKEN`）过期或权限不足（需 public_repo 读权限） |
| Sync 数据库错误 | `DATABASE_URL`、runner → Postgres 网络、migrate 是否成功 |
| 按需 AI 摘要失败 | Nuxt 服务器进程的 `XFYUN_API_KEY` / `XFYUN_BASE_URL` / `XFYUN_MODEL` 配置或额度（与 Actions sync 无关） |
| 构建失败 | 前端依赖变化，检查 `npm ci` / `npm run build` 日志 |
| 部署失败 | SSH 密钥、`DEPLOY_*`、远端目录权限、`DEPLOY_RESTART_CMD` 单元名 |
| 站点旧数据 | 确认 sync 成功且 deploy 步骤执行；查 DB `leaderboards.generated_at` |
| 告警未收到 | `NOTIFY_WEBHOOK` 失效或 Notify 步骤被跳过 |

## 故障恢复（无 data/ 回滚）

旧版通过 git 历史恢复 `data/` 文件；**新架构不支持此路径**。

| 场景 | 做法 |
|------|------|
| 单次 sync 失败 | 修复根因后 `workflow_dispatch` 重跑 Daily Sync；DB 保留上次成功写入的榜单 |
| 部署失败但 sync 成功 | 手动重跑 deploy 或仅 re-run deploy 相关 job；数据已在 Postgres |
| 数据库损坏 / 误删 | 从 Postgres 备份恢复（需自行配置 `pg_dump` 等）；**不**从 git 恢复 `data/` |
| 需要全量重建 | 空库或 drop schema 后：`migrate` → `sync` → 等待 backfill 积累年榜 |

建议：对 `github-ranking` 库配置定期备份（cron + 异地存储）。

## 讯飞额度对账

- 官方控制台查看 tokens 消耗（免费额度以官方最新为准）
- **Actions `sync` 不再调用讯飞**；摘要仅在用户点击按需生成时由 Nuxt Nitro 调用
- 更换模型：更新 Nuxt 服务器环境变量 `XFYUN_MODEL` 与 `XFYUN_BASE_URL` 后重启进程

## 模型/接口变更

1. 核对讯飞官方文档（https://www.xfyun.cn/doc）
2. 更新 Nuxt 服务器上的 `XFYUN_*` 环境变量并重启 `github-ranking`
3. 在站点上对某仓库点按需摘要，确认生成成功（无需重跑 sync）

## 仓库维护

- 不再因每日 data 提交膨胀；若历史 clone 仍很大，可在迁移后执行 `git gc --aggressive`
- 本地 `data/` 若存在，已在 `.gitignore` 中忽略，勿提交
