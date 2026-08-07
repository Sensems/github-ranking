import { copyFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const src = join(root, 'deploy', 'ecosystem.config.cjs')
const dest = join(root, 'frontend', '.output', 'ecosystem.config.cjs')

mkdirSync(dirname(dest), { recursive: true })
copyFileSync(src, dest)
console.log(`copied ${src} -> ${dest}`)
