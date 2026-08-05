import pg from 'pg'

let pool: pg.Pool | null = null

export function getPool() {
  const url = useRuntimeConfig().databaseUrl
  if (!url) {
    throw createError({ statusCode: 500, statusMessage: 'DATABASE_URL not configured' })
  }
  if (!pool) {
    pool = new pg.Pool({ connectionString: url, max: 5 })
  }
  return pool
}
