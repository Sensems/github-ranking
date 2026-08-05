import { defineEventHandler } from 'h3'
import { getPool } from '../utils/db'

export default defineEventHandler(async () => {
  await getPool().query('SELECT 1')
  return { ok: true }
})
