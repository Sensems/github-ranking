import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getPool } from '../../utils/db'
import {
  chatCompletionsUrl,
  parseSummaryContent,
} from '../../utils/summary'
import { getRepoSummary } from './[repoId]/summary.get'
import postSummaryHandler, { postRepoSummary } from './[repoId]/summary.post'

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

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

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

  it.each([
    ['project_positioning', { ...sampleSummary, project_positioning: null }],
    ['core_features', { ...sampleSummary, core_features: null }],
    ['core_features items', { ...sampleSummary, core_features: ['a', 1] }],
    ['use_cases', { ...sampleSummary, use_cases: 'u' }],
    ['use_cases items', { ...sampleSummary, use_cases: ['u', null] }],
    ['tech_stack', { ...sampleSummary, tech_stack: {} }],
    ['tech_stack items', { ...sampleSummary, tech_stack: ['t', false] }],
  ])('rejects invalid %s types', (_field, value) => {
    expect(() => parseSummaryContent(JSON.stringify(value))).toThrow()
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

  it.each([1.5, Number.MAX_SAFE_INTEGER + 1])(
    'rejects non-safe-integer repo id %s',
    async (repoId) => {
      const query = vi.fn().mockResolvedValue({ rows: [] })
      mockedGetPool.mockReturnValue({ query } as never)

      await expect(getRepoSummary(repoId)).rejects.toMatchObject({ statusCode: 400 })
      expect(query).not.toHaveBeenCalled()
    },
  )
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

  it.each([1.5, Number.MAX_SAFE_INTEGER + 1])(
    'rejects non-safe-integer repo id %s',
    async (repoId) => {
      const query = vi.fn().mockResolvedValue({ rows: [] })
      mockedGetPool.mockReturnValue({ query } as never)

      await expect(
        postRepoSummary(repoId, {
          apiKey: 'k',
          baseUrl: 'https://example.com/v1/',
          model: 'm',
        }),
      ).rejects.toMatchObject({ statusCode: 400 })
      expect(query).not.toHaveBeenCalled()
    },
  )

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

  it('fetches and upserts a missing README before generating', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
    mockedGetPool.mockReturnValue({ query } as never)

    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce({
        status: 200,
        text: async () => '# Fresh README',
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          choices: [{ message: { content: JSON.stringify(sampleSummary) } }],
        }),
      })

    await expect(
      postRepoSummary(
        10,
        { apiKey: 'k', baseUrl: 'https://example.com/v1/', model: 'm' },
        fetchImpl as unknown as typeof fetch,
      ),
    ).resolves.toEqual({ repo_id: 10, summary: sampleSummary })

    expect(fetchImpl).toHaveBeenCalledTimes(2)
    expect(String(fetchImpl.mock.calls[0][0])).toContain(
      'raw.githubusercontent.com/a/b/HEAD/README.md',
    )
    expect(String(query.mock.calls[3][0])).toContain('INSERT INTO readmes')
    expect(query.mock.calls[3][1]).toMatchObject([10, expect.any(String), '# Fresh README'])
    expect(String(query.mock.calls[4][0])).toContain('INSERT INTO summaries')
  })

  it('reports a README lookup database failure as a database error', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockRejectedValueOnce(new Error('database unavailable'))
    mockedGetPool.mockReturnValue({ query } as never)

    await expect(
      postRepoSummary(13, {
        apiKey: 'k',
        baseUrl: 'https://example.com/v1/',
        model: 'm',
      }),
    ).rejects.toMatchObject({
      statusCode: 500,
      statusMessage: 'Database error',
    })
  })

  it('reports a README upsert failure as a database error', async () => {
    const query = vi
      .fn()
      .mockResolvedValueOnce({ rows: [{ repo_name: 'a/b' }] })
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })
      .mockRejectedValueOnce(new Error('database unavailable'))
    mockedGetPool.mockReturnValue({ query } as never)
    const fetchImpl = vi.fn().mockResolvedValue({
      status: 200,
      text: async () => '# Fresh README',
    })

    await expect(
      postRepoSummary(
        14,
        { apiKey: 'k', baseUrl: 'https://example.com/v1/', model: 'm' },
        fetchImpl as unknown as typeof fetch,
      ),
    ).rejects.toMatchObject({
      statusCode: 500,
      statusMessage: 'Database error',
    })
  })

  it('coalesces concurrent generation for the same repo', async () => {
    const query = vi.fn(async (sql: unknown) => {
      const text = String(sql)
      if (text.includes('SELECT repo_name')) {
        return { rows: [{ repo_name: 'a/b' }] }
      }
      if (text.includes('SELECT summary')) {
        return { rows: [] }
      }
      if (text.includes('SELECT hash, excerpt')) {
        return { rows: [{ hash: 'h1', excerpt: '# Hello' }] }
      }
      return { rows: [] }
    })
    mockedGetPool.mockReturnValue({ query } as never)

    let releaseFetch!: (value: unknown) => void
    const fetchResult = new Promise((resolve) => {
      releaseFetch = resolve
    })
    const fetchImpl = vi.fn().mockReturnValue(fetchResult)
    const cfg = {
      apiKey: 'k',
      baseUrl: 'https://example.com/v1/',
      model: 'm',
    }

    const first = postRepoSummary(11, cfg, fetchImpl as unknown as typeof fetch)
    const second = postRepoSummary(11, cfg, fetchImpl as unknown as typeof fetch)

    await vi.waitFor(() => expect(fetchImpl).toHaveBeenCalled())
    releaseFetch({
      ok: true,
      json: async () => ({
        choices: [{ message: { content: JSON.stringify(sampleSummary) } }],
      }),
    })

    await expect(Promise.all([first, second])).resolves.toEqual([
      { repo_id: 11, summary: sampleSummary },
      { repo_id: 11, summary: sampleSummary },
    ])
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    expect(query).toHaveBeenCalledTimes(4)
  })

  it('reads plain XFYUN variables from the request-time environment', async () => {
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
    vi.stubEnv('XFYUN_API_KEY', 'runtime-key')
    vi.stubEnv('XFYUN_BASE_URL', 'https://runtime.example/v1/')
    vi.stubEnv('XFYUN_MODEL', 'runtime-model')
    vi.stubGlobal('useRuntimeConfig', () => ({
      xfyunApiKey: '',
      xfyunBaseUrl: '',
      xfyunModel: '',
    }))
    vi.stubGlobal('fetch', fetchImpl)

    await expect(
      postSummaryHandler({
        context: { params: { repoId: '12' } },
      } as never),
    ).resolves.toEqual({ repo_id: 12, summary: sampleSummary })

    expect(String(fetchImpl.mock.calls[0][0])).toBe(
      'https://runtime.example/v1/chat/completions',
    )
    expect(fetchImpl.mock.calls[0][1]).toMatchObject({
      headers: {
        Authorization: 'Bearer runtime-key',
      },
    })
    expect(JSON.parse(String(fetchImpl.mock.calls[0][1]?.body))).toMatchObject({
      model: 'runtime-model',
    })
  })
})
