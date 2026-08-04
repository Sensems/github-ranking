# 日常运维

## 数据更新节奏

- 每日 08:00 北京时间 `sync.yml` 自动运行（UTC 00:00 cron，可能延迟 15-30 分钟）
- 每日 08:30 北京时间 `backfill.yml` 自动运行小批量回溯
- 失败自动重试 1 次；仍失败发送 `NOTIFY_WEBHOOK` 告警并保留上次数据
- 可用 `workflow_dispatch` 手动补跑任意一次

## 失败排查清单

| 现象 | 排查 |
|------|------|
| Search API 报 403 | `GH_TOKEN` 过期或权限不足（需 public_repo 读权限） |
| AI 摘要全部失败 | `XFYUN_API_KEY` / `XFYUN_BASE_URL` / `XFYUN_MODEL` 配置或额度问题 |
| 构建失败 | 前端依赖版本变化，检查 `npm ci` 日志 |
| 部署失败 | SSH 密钥、服务器 rsync、目录权限 |
| 告警未收到 | `NOTIFY_WEBHOOK` 失效或 Notify 步骤被跳过 |

## 数据文件说明

- `data/repos.json`：候选池元数据 + 最新快照（含摘要仓库的 readme_hash）
- `data/history/<repo_id>.csv`：滚动快照（date,stars,forks），**自动保留 400 天**，无需人工清理
- `data/readmes/<repo_id>.json`：README 截断内容 + sha256（仅榜单 Top 100 候选）
- `data/summaries/<repo_id>.json`：AI 摘要缓存（绑定 readme_hash）
- `data/leaderboards/*.json`：5 个榜单（Top 100），前端构建时直接读取

## 讯飞额度对账

- 官方控制台查看 tokens 消耗（免费额度数值以官方最新为准）
- 摘要仅对进入任一榜单 Top 100 的仓库生成（批次上限 100/天）
- 如需更换模型：只改 `XFYUN_MODEL` Secret 与 `XFYUN_BASE_URL`，代码无需变更

## 模型/接口变更

模型 ID、Base URL、免费额度均可能随官方调整。升级前：

1. 核对讯飞官方文档（https://www.xfyun.cn/doc）
2. 更新 Secrets
3. 手动触发一次 sync，确认摘要生成成功率

## 仓库维护

- 历史数据由滚动窗口自动裁剪；如 git 仓库过大可执行 `git gc --aggressive`
- 每日 data 提交是常规噪音，无需处理
