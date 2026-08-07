/**
 * PM2 process file for the Nuxt Nitro SSR bundle.
 * Place this next to `server/index.mjs` and `.env` in the deploy directory
 * (e.g. /var/www/github-ranking), then:
 *
 *   pm2 startOrReload ecosystem.config.cjs --update-env
 *   pm2 save
 *   pm2 startup
 */
const fs = require('node:fs')
const path = require('node:path')

function loadEnvFile(filePath) {
  const env = {}
  if (!fs.existsSync(filePath)) return env

  for (const line of fs.readFileSync(filePath, 'utf8').split(/\r?\n/)) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eq = trimmed.indexOf('=')
    if (eq <= 0) continue
    const key = trimmed.slice(0, eq).trim()
    let value = trimmed.slice(eq + 1).trim()
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1)
    }
    env[key] = value
  }
  return env
}

const cwd = __dirname
const fileEnv = loadEnvFile(path.join(cwd, '.env'))

module.exports = {
  apps: [
    {
      name: 'github-ranking',
      cwd,
      script: 'server/index.mjs',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'production',
        PORT: '3000',
        ...fileEnv,
      },
    },
  ],
}
