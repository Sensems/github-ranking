import { createError, defineEventHandler, getRouterParam } from 'h3'
import { getPool } from '../../../utils/db'
import {
  fetchReadmeFromGithub,
  generateSummary,
  hashReadme,
  resolveXfyunConfig,
  type XfyunConfig,
} from '../../../utils/summary'

export type SummaryPostConfig = XfyunConfig

type SummaryPostResponse = {
  repo_id: number
  summary: Awaited<ReturnType<typeof generateSummary>>
}

const inFlightByRepo = new Map<number, Promise<SummaryPostResponse>>()

async function postRepoSummaryOnce(
  repoId: number,
  cfg: SummaryPostConfig,
  fetchImpl: typeof fetch = fetch,
): Promise<SummaryPostResponse> {
  const pool = getPool()

  let repoName: string
  try {
    const { rows: repoRows } = await pool.query(
      'SELECT repo_name FROM repos WHERE repo_id = $1',
      [repoId],
    )
    if (!repoRows[0]) {
      throw createError({ statusCode: 404, statusMessage: 'Repo not found' })
    }
    repoName = repoRows[0].repo_name as string
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'statusCode' in err) {
      throw err
    }
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }

  try {
    const { rows: summaryRows } = await pool.query(
      'SELECT summary FROM summaries WHERE repo_id = $1',
      [repoId],
    )
    if (summaryRows[0]) {
      return { repo_id: repoId, summary: summaryRows[0].summary }
    }
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'statusCode' in err) {
      throw err
    }
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }

  if (!cfg.apiKey?.trim()) {
    throw createError({ statusCode: 503, statusMessage: 'XFYUN API key not configured' })
  }

  let excerpt: string
  let readmeHash: string
  try {
    const { rows: readmeRows } = await pool.query(
      'SELECT hash, excerpt FROM readmes WHERE repo_id = $1',
      [repoId],
    )
    if (readmeRows[0]?.excerpt) {
      excerpt = readmeRows[0].excerpt as string
      readmeHash = (readmeRows[0].hash as string) || hashReadme(excerpt)
    } else {
      excerpt = ''
      readmeHash = ''
    }
  } catch {
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }

  if (!excerpt) {
    let fetched: string | null
    try {
      fetched = await fetchReadmeFromGithub(repoName, undefined, fetchImpl)
    } catch {
      throw createError({ statusCode: 502, statusMessage: 'Failed to load README' })
    }
    if (!fetched) {
      throw createError({ statusCode: 404, statusMessage: 'README not found' })
    }
    excerpt = fetched
    readmeHash = hashReadme(excerpt)
    try {
      await pool.query(
        `
        INSERT INTO readmes (repo_id, hash, excerpt)
        VALUES ($1, $2, $3)
        ON CONFLICT (repo_id) DO UPDATE SET
          hash = EXCLUDED.hash,
          excerpt = EXCLUDED.excerpt
        `,
        [repoId, readmeHash, excerpt],
      )
    } catch {
      throw createError({ statusCode: 500, statusMessage: 'Database error' })
    }
  }

  let summary: SummaryPostResponse['summary']
  try {
    summary = await generateSummary(excerpt, cfg, fetchImpl)
  } catch {
    throw createError({ statusCode: 502, statusMessage: 'Summary generation failed' })
  }

  const generatedAt = new Date().toISOString().slice(0, 10)
  try {
    await pool.query(
      `
      INSERT INTO summaries (repo_id, readme_hash, summary, generated_at)
      VALUES ($1, $2, $3::jsonb, $4)
      ON CONFLICT (repo_id) DO UPDATE SET
        readme_hash = EXCLUDED.readme_hash,
        summary = EXCLUDED.summary,
        generated_at = EXCLUDED.generated_at
      `,
      [repoId, readmeHash, JSON.stringify(summary), generatedAt],
    )
  } catch {
    throw createError({ statusCode: 500, statusMessage: 'Database error' })
  }

  return { repo_id: repoId, summary }
}

export async function postRepoSummary(
  repoId: number,
  cfg: SummaryPostConfig,
  fetchImpl: typeof fetch = fetch,
): Promise<SummaryPostResponse> {
  if (!Number.isSafeInteger(repoId) || repoId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'Invalid repo id' })
  }

  const existing = inFlightByRepo.get(repoId)
  if (existing) {
    return existing
  }

  // The cache lookup is inside the flight, so the winner re-checks it before model use.
  const flight = postRepoSummaryOnce(repoId, cfg, fetchImpl)
  inFlightByRepo.set(repoId, flight)
  try {
    return await flight
  } finally {
    if (inFlightByRepo.get(repoId) === flight) {
      inFlightByRepo.delete(repoId)
    }
  }
}

export default defineEventHandler(async (event) => {
  const raw = getRouterParam(event, 'repoId') ?? ''
  const repoId = Number(raw)
  return postRepoSummary(repoId, resolveXfyunConfig(useRuntimeConfig()))
})
