#!/usr/bin/env bash
# 一键：构建前端并用 PM2 启动（可在本机或服务器上直接跑）
#
# 用法：
#   bash deploy/one-click.sh
#
# 可选环境变量：
#   DEPLOY_PATH   部署目录（默认：frontend/.output，即构建产物目录）
#   SKIP_INSTALL  设为 1 时跳过 npm ci
#   SKIP_BUILD    设为 1 时跳过 build（已有 .output 时）
#
# 部署目录需要 .env（含 NUXT_DATABASE_URL、PORT 等）。
# 若部署目录没有 .env 且 frontend/.env 存在，会自动复制一份。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
OUTPUT="$FRONTEND/.output"
DEPLOY_PATH="${DEPLOY_PATH:-$OUTPUT}"

echo "==> repo: $ROOT"
echo "==> deploy path: $DEPLOY_PATH"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "pm2 未安装，正在安装（npm i -g pm2）..."
  npm i -g pm2
fi

if ! command -v node >/dev/null 2>&1; then
  echo "错误：未找到 node，请先安装 Node 20+"
  exit 1
fi

cd "$FRONTEND"

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  echo "==> npm ci"
  npm ci
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "==> npm run build（含拷贝 ecosystem.config.cjs）"
  npm run build
else
  echo "==> 跳过 build"
  if [[ ! -f "$OUTPUT/server/index.mjs" ]]; then
    echo "错误：未找到 $OUTPUT/server/index.mjs，请去掉 SKIP_BUILD 重新构建"
    exit 1
  fi
  # 即使跳过 build，也确保 ecosystem 在产物里
  node "$ROOT/deploy/copy-ecosystem.mjs"
fi

if [[ "$DEPLOY_PATH" != "$OUTPUT" ]]; then
  echo "==> 同步 .output/ -> $DEPLOY_PATH"
  mkdir -p "$DEPLOY_PATH"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "$OUTPUT/" "$DEPLOY_PATH/"
  else
    # 无 rsync 时退化为 cp（不删除目标多余文件）
    cp -a "$OUTPUT/." "$DEPLOY_PATH/"
  fi
fi

if [[ ! -f "$DEPLOY_PATH/server/index.mjs" ]]; then
  echo "错误：部署目录缺少 server/index.mjs：$DEPLOY_PATH"
  exit 1
fi

if [[ ! -f "$DEPLOY_PATH/ecosystem.config.cjs" ]]; then
  echo "==> 拷贝 ecosystem.config.cjs"
  cp "$ROOT/deploy/ecosystem.config.cjs" "$DEPLOY_PATH/ecosystem.config.cjs"
fi

if [[ ! -f "$DEPLOY_PATH/.env" ]]; then
  if [[ -f "$FRONTEND/.env" ]]; then
    echo "==> 复制 frontend/.env -> $DEPLOY_PATH/.env"
    cp "$FRONTEND/.env" "$DEPLOY_PATH/.env"
  else
    echo "错误：缺少 $DEPLOY_PATH/.env"
    echo "请先创建，至少包含："
    echo "  NUXT_DATABASE_URL=postgresql://..."
    echo "  PORT=3000"
    exit 1
  fi
fi

echo "==> PM2 startOrReload"
cd "$DEPLOY_PATH"
pm2 startOrReload ecosystem.config.cjs --update-env
pm2 save

echo ""
echo "完成。常用命令："
echo "  pm2 status"
echo "  pm2 logs github-ranking"
echo "  curl -s \"http://127.0.0.1:\${PORT:-3000}/api/health\""
pm2 status
