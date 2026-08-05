import { createError, defineEventHandler, getRouterParam } from 'h3'
import { getPool } from '../../utils/db'

const BOARD_TYPES = new Set(['total', 'daily', 'weekly', 'monthly', 'yearly'])

export async function getLeaderboardByType(type: string) {
  if (!BOARD_TYPES.has(type)) {
    throw createError({ statusCode: 404, statusMessage: 'Unknown leaderboard type' })
  }

  try {
    const { rows } = await getPool().query(
      'SELECT generated_at, items FROM leaderboards WHERE type = $1',
      [type],
    )
    const row = rows[0]
    if (!row) {
      return { type, generated_at: null, items: [] }
    }
    const generatedAt =
      row.generated_at instanceof Date ? row.generated_at.toISOString() : row.generated_at
    return {
      type,
      generated_at: generatedAt,
      items: row.items ?? [],
    }
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'statusCode' in err) {
      throw err
    }
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }
}

export default defineEventHandler(async (event) => {
  const type = getRouterParam(event, 'type') ?? ''
  return getLeaderboardByType(type)
})
