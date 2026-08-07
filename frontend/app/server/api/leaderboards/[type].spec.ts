import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getPool } from '../../utils/db'
import { getLeaderboardByType } from './[type].get'

vi.mock('../../utils/db', () => ({
  getPool: vi.fn(),
}))

const mockedGetPool = vi.mocked(getPool)

describe('GET /api/leaderboards/:type', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 404 for unknown type', async () => {
    await expect(getLeaderboardByType('nope')).rejects.toMatchObject({ statusCode: 404 })
    expect(mockedGetPool).not.toHaveBeenCalled()
  })

  it('returns empty payload when row is missing', async () => {
    mockedGetPool.mockReturnValue({
      query: vi.fn().mockResolvedValue({ rows: [] }),
    } as never)

    await expect(getLeaderboardByType('daily')).resolves.toEqual({
      type: 'daily',
      generated_at: null,
      items: [],
    })
  })

  it('attaches summaries from summaries table onto items', async () => {
    const items = [
      { rank: 1, repo_id: 42, repo_name: 'a/b', has_summary: true },
      { rank: 2, repo_id: 7, repo_name: 'c/d', has_summary: false },
    ]
    const summary = {
      project_positioning: '工具库',
      core_features: ['快'],
      use_cases: ['CLI'],
      tech_stack: ['Go'],
    }
    const query = vi
      .fn()
      .mockResolvedValueOnce({
        rows: [{ generated_at: '2026-08-05T12:00:00.000Z', items }],
      })
      .mockResolvedValueOnce({
        rows: [{ repo_id: 42, summary }],
      })
    mockedGetPool.mockReturnValue({ query } as never)

    await expect(getLeaderboardByType('total')).resolves.toEqual({
      type: 'total',
      generated_at: '2026-08-05T12:00:00.000Z',
      items: [
        { ...items[0], summary, has_summary: true },
        { ...items[1], has_summary: false },
      ],
    })
    expect(query).toHaveBeenCalledTimes(2)
    expect(query.mock.calls[1][0]).toContain('FROM summaries')
  })

  it('returns 500 on database error', async () => {
    mockedGetPool.mockReturnValue({
      query: vi.fn().mockRejectedValue(new Error('connection refused')),
    } as never)

    await expect(getLeaderboardByType('weekly')).rejects.toMatchObject({ statusCode: 500 })
  })
})
