import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const boards = [
  { file: 'index.vue', type: 'total', title: '总 Star 榜' },
  { file: 'daily.vue', type: 'daily', title: '日增速榜' },
  { file: 'weekly.vue', type: 'weekly', title: '周增速榜' },
  { file: 'monthly.vue', type: 'monthly', title: '月增速榜' },
  { file: 'yearly.vue', type: 'yearly', title: '年增速榜' },
] as const

function readPage(file: string): string {
  return readFileSync(resolve(process.cwd(), 'app/pages', file), 'utf8')
}

describe.each(boards)('$file', ({ file, type, title }) => {
  it('uses shared typography and Alert states without changing board wiring', () => {
    const page = readPage(file)

    expect(page).toContain(`/api/leaderboards/${type}`)
    expect(page).toContain(`<h1 class="text-lg font-semibold text-foreground">${title}</h1>`)
    expect(page).toContain('class="text-xs text-muted-foreground"')
    expect(page).toContain('<Alert v-if="error" variant="destructive">')
    expect(page).toContain('<AlertDescription>加载失败，请稍后重试。</AlertDescription>')
    expect(page).toContain('class="board-toolbar mb-4 flex flex-wrap items-center gap-2"')
    expect(page).toContain('class="board-grid grid gap-4 md:grid-cols-2"')
    expect(page).toContain('<Alert v-else>')
    expect(page).toContain(
      '<AlertDescription>该榜单暂无数据（历史数据积累中），请明天再来看看。</AlertDescription>',
    )
    expect(page).toContain(`board-type="${type}"`)
    expect(page).toContain('class="board-page"')
  })
})
