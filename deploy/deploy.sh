#!/usr/bin/env bash
set -euo pipefail

# Rsync Nitro SSR bundle (frontend/.output/) to the server, then restart the Node process.
# Default process unit/name: github-ranking
# Override with DEPLOY_RESTART_CMD, e.g.:
#   systemctl restart github-ranking
#   pm2 restart github-ranking

if [ -z "${SSH_PRIVATE_KEY:-}" ] || [ -z "${DEPLOY_HOST:-}" ] || [ -z "${DEPLOY_USER:-}" ] || [ -z "${DEPLOY_PATH:-}" ]; then
  echo "Deploy skipped: missing SSH_PRIVATE_KEY / DEPLOY_HOST / DEPLOY_USER / DEPLOY_PATH"
  exit 0
fi

mkdir -p ~/.ssh
echo "$SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
chmod 600 ~/.ssh/deploy_key
ssh-keyscan -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts 2>/dev/null

RSYNC_SSH='ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=yes'

rsync -az --delete -e "$RSYNC_SSH" \
  frontend/.output/ "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}"

RESTART_CMD="${DEPLOY_RESTART_CMD:-systemctl restart github-ranking}"
ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=yes \
  "${DEPLOY_USER}@${DEPLOY_HOST}" "$RESTART_CMD"

echo "deploy ok: ${DEPLOY_HOST}:${DEPLOY_PATH} (restart: ${RESTART_CMD})"
