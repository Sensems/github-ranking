import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getPool } from '../../utils/db'
import {
  chatCompletionsUrl,
  parseSummaryContent,
} from '../../utils/summary'
import { getRepoSummary } from './[repoId]/summary.get'
import { postRepoSummary } from './[repoId]/summary.post'

vi.mock('../../utils/db', () => ({
  getPool: vi.fn(),
}))

const mockedGetPool = vi.mocked(getPool)

const sampleSummary = {
  project_positioning: 'p',
  core_features: ['a'],
  use_cases: ['u'],
  tech_stack: ['t'],
}

describe('parseSummaryContent', () => {
  it('parses fenced json', () => {
    const s = parseSummaryContent(
      '```json\n{"project_positioning":"p","core_features":["a"],"use_cases":["u"],"tech_stack":["t"]}\n```',
    )
    expect(s.project_positioning).toBe('p')
  })

  it('rejects missing keys', () => {
    expect(() => parseSummaryContent('{"project_positioning":"p"}')).toThrow(/missing key/)
  })
})

describe('chatCompletionsUrl', () => {
  it('appends chat/completions without double slash', () => {
    expect(chatCompletionsUrl('https://spark-api-open.xf-yun.com/agent/v1/')).toBe(
      'https://spark-api-open.xf-yun.com/agent/v1/chat/completions',
    )
    expect(chatCompletionsUrl('https://spark-api-open.xf-yun.com/agent/v1')).toBe(
      'https://spark-api-open.xf-yun.com/agent/v1/chat/completions',
    )
  })
})

describe('GET /api/repos/:repoId/summary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 404 when summary row is missing', async () => {
    mockedGetPool.mockReturnValue({
      query: vi.fn().mockResolvedValue({ rows: [] }),
    } as never)

    await expect(getRepoSummary(1)).rejects.toMatchObject({ statusCode: 404 })
  })

  it('returns cached summary', async () => {
    mockedGetPool.mockReturnValue({
      query: vi.fn().mockResolvedValue({ rows: [{ summary: sampleSummary }] }),
    } as never)

    await expect(getRepoSummary(42)).resolves.toEqual({
      repo_id: 42,
      summary: sampleSummary,
    })
  })
})

describe('POST /api/repos/:repoId/summary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 404 when repo is missing', async () => {
    mockedGetPool.mockReturnValue({
      query: vi.fn().mockResolvedValue({ rows: [] }),
    } as never)

    await expect(
      postRepoSummary(1, { apiKey: 'k', baseUrl: 'https://example.com/v1/', model: 'm' }),
    ).rejects.toMatchObject({ statusCode: 404 })
  })

  it('returns cached summary without calling the model', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [{ summary: sampleSummary }] })
    mockedGetPool.mockReturnValue({ query } as never)
    const fetchImpl = vi.fn()

    await expect(
      postRepoSummary(
        7,
        { apiKey: 'k', baseUrl: 'https://example.com/v1/', model: 'm' },
        fetchImpl as unknown as typeof fetch,
      ),
    ).resolves.toEqual({ repo_id: 7, summary: sampleSummary })
    expect(fetchImpl).not.toHaveBeenCalled()
  })

  it('returns 503 when api key is missing and no cache', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [] })
    mockedGetPool.mockReturnValue({ query } as never)

    await expect(
      postRepoSummary(7, { apiKey: '', baseUrl: 'https://example.com/v1/', model: 'm' }),
    ).rejects.toMatchObject({ statusCode: 503 })
  })

  it('generates, upserts, and returns summary when readme is in DB', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ hash: 'h1', excerpt: '# Hello' }] })
      .mockResolvedValueOnce({ rows: [] })
    mockedGetPool.mockReturnValue({ query } as never)

    const fetchImpl = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: JSON.stringify(sampleSummary) } }],
      }),
    })

    await expect(
      postRepoSummary(
        9,
        { apiKey: 'k', baseUrl: 'https://spark-api-open.xf-yun.com/agent/v1/', model: 'spark-x' },
        fetchImpl as unknown as typeof fetch,
      ),
    ).resolves.toEqual({ repo_id: 9, summary: sampleSummary })

    expect(fetchImpl).toHaveBeenCalledTimes(1)
    expect(String(fetchImpl.mock.calls[0][0])).toBe(
      'https://spark-api-open.xf-yun.com/agent/v1/chat/completions',
    )
    expect(query).toHaveBeenCalledTimes(4)
  })
})
