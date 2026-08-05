import { createError, defineEventHandler, getRouterParam } from 'h3'
import { getPool } from '../../../utils/db'

export async function getRepoSummary(repoId: number) {
  if (!Number.isSafeInteger(repoId) || repoId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'Invalid repo id' })
  }

  try {
    const { rows } = await getPool().query(
      'SELECT summary FROM summaries WHERE repo_id = $1',
      [repoId],
    )
    const row = rows[0]
    if (!row) {
      throw createError({ statusCode: 404, statusMessage: 'Summary not found' })
    }
    return { repo_id: repoId, summary: row.summary }
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'statusCode' in err) {
      throw err
    }
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }
}

export default defineEventHandler(async (event) => {
  const raw = getRouterParam(event, 'repoId') ?? ''
  const repoId = Number(raw)
  return getRepoSummary(repoId)
})
