#!/usr/bin/env bash
set -euo pipefail

if [ -z "${SSH_PRIVATE_KEY:-}" ] || [ -z "${DEPLOY_HOST:-}" ] || [ -z "${DEPLOY_USER:-}" ] || [ -z "${DEPLOY_PATH:-}" ]; then
  echo "Missing deploy env: SSH_PRIVATE_KEY / DEPLOY_HOST / DEPLOY_USER / DEPLOY_PATH" >&2
  exit 1
fi

mkdir -p ~/.ssh
echo "$SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
chmod 600 ~/.ssh/deploy_key
ssh-keyscan -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts 2>/dev/null

rsync -az --delete -e "ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=yes" \
  frontend/.output/public/ "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}"

echo "deploy ok: ${DEPLOY_HOST}:${DEPLOY_PATH}"
