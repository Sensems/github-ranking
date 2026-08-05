import { createError, defineEventHandler, getRouterParam } from 'h3'
import { getPool } from '../../../utils/db'
import {
  fetchReadmeFromGithub,
  generateSummary,
  hashReadme,
  type XfyunConfig,
} from '../../../utils/summary'

export type SummaryPostConfig = XfyunConfig

export async function postRepoSummary(
  repoId: number,
  cfg: SummaryPostConfig,
  fetchImpl: typeof fetch = fetch,
) {
  if (!Number.isFinite(repoId) || repoId <= 0) {
    throw createError({ statusCode: 400, statusMessage: 'Invalid repo id' })
  }

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
      const fetched = await fetchReadmeFromGithub(repoName, undefined, fetchImpl)
      if (!fetched) {
        throw createError({ statusCode: 404, statusMessage: 'README not found' })
      }
      excerpt = fetched
      readmeHash = hashReadme(excerpt)
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
    }
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'statusCode' in err) {
      throw err
    }
    throw createError({ statusCode: 502, statusMessage: 'Failed to load README' })
  }

  let summary
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

export default defineEventHandler(async (event) => {
  const raw = getRouterParam(event, 'repoId') ?? ''
  const repoId = Number(raw)
  const runtime = useRuntimeConfig()
  return postRepoSummary(repoId, {
    apiKey: String(runtime.xfyunApiKey || ''),
    baseUrl: String(runtime.xfyunBaseUrl || ''),
    model: String(runtime.xfyunModel || ''),
  })
})
