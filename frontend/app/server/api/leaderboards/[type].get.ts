import { createError, defineEventHandler, getRouterParam } from 'h3'
import { getPool } from '../../utils/db'
import type { LeaderboardItem, Summary } from '~/types/leaderboard'

const BOARD_TYPES = new Set(['total', 'daily', 'weekly', 'monthly', 'yearly'])

async function attachSummaries(items: LeaderboardItem[]): Promise<LeaderboardItem[]> {
  if (!items.length) return items

  const ids = [...new Set(items.map((i) => i.repo_id).filter((id) => Number.isFinite(id)))]
  if (!ids.length) return items

  const { rows } = await getPool().query<{ repo_id: number; summary: Summary }>(
    'SELECT repo_id, summary FROM summaries WHERE repo_id = ANY($1::bigint[])',
    [ids],
  )
  const byId = new Map(rows.map((r) => [Number(r.repo_id), r.summary]))

  return items.map((item) => {
    const summary = byId.get(item.repo_id)
    if (!summary) {
      return { ...item, has_summary: item.has_summary ?? false }
    }
    return { ...item, summary, has_summary: true }
  })
}

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
    const rawItems = (row.items ?? []) as LeaderboardItem[]
    const items = await attachSummaries(rawItems)
    return {
      type,
      generated_at: generatedAt,
      items,
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
