import pg from 'pg'

let pool: pg.Pool | null = null

function resolveDatabaseUrl(): string {
  const fromConfig = useRuntimeConfig().databaseUrl
  if (typeof fromConfig === 'string' && fromConfig.trim()) {
    return fromConfig.trim()
  }
  // After `nuxt build`, plain DATABASE_URL is not auto-mapped unless NUXT_DATABASE_URL is set.
  const fromEnv =
    process.env.NUXT_DATABASE_URL ||
    process.env.DATABASE_URL ||
    ''
  return typeof fromEnv === 'string' ? fromEnv.trim() : ''
}

export function getPool() {
  const url = resolveDatabaseUrl()
  if (!url) {
    throw createError({ statusCode: 500, statusMessage: 'DATABASE_URL not configured' })
  }
  if (!pool) {
    pool = new pg.Pool({ connectionString: url, max: 5 })
  }
  return pool
}
