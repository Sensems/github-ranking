import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const boards = [
  { file: 'index.vue', type: 'total', title: '总排名' },
  { file: 'daily.vue', type: 'daily', title: '日增速榜' },
  { file: 'weekly.vue', type: 'weekly', title: '周增速榜' },
  { file: 'monthly.vue', type: 'monthly', title: '月增速榜' },
  { file: 'yearly.vue', type: 'yearly', title: '年增速榜' },
] as const

function readPage(file: string): string {
  return readFileSync(resolve(process.cwd(), 'app/pages', file), 'utf8')
}

describe.each(boards)('$file', ({ file, type, title }) => {
  it('wires board type through LeaderboardView', () => {
    const page = readPage(file)

    expect(page).toContain('`/api/leaderboards/${boardType}`')
    expect(page).toContain(`boardType = '${type}'`)
    expect(page).toContain('<LeaderboardView')
    expect(page).toContain(':board-type="boardType"')
    expect(page).toContain(':payload="payload"')
    expect(page).toContain(':error="error"')
    expect(page).toContain('BOARD_META')
    expect(title.length).toBeGreaterThan(0)
  })
})
