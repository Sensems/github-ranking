import pg from 'pg'

let pool: pg.Pool | null = null

/** Strip Prisma-only `schema=` query param that node-pg / libpq reject. */
export function normalizeDatabaseUrl(url: string): string {
  try {
    const parsed = new URL(url)
    const schema = parsed.searchParams.get('schema')
    parsed.searchParams.delete('schema')
    if (schema && schema !== 'public' && !parsed.searchParams.get('options')?.includes('search_path')) {
      parsed.searchParams.set('options', `-csearch_path=${schema}`)
    }
    return parsed.toString()
  } catch {
    return url
  }
}

function resolveDatabaseUrl(): string {
  const fromConfig = useRuntimeConfig().databaseUrl
  if (typeof fromConfig === 'string' && fromConfig.trim()) {
    return normalizeDatabaseUrl(fromConfig.trim())
  }
  // After `nuxt build`, plain DATABASE_URL is not auto-mapped unless NUXT_DATABASE_URL is set.
  const fromEnv =
    process.env.NUXT_DATABASE_URL ||
    process.env.DATABASE_URL ||
    ''
  return typeof fromEnv === 'string' ? normalizeDatabaseUrl(fromEnv.trim()) : ''
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
