import type { BoardType } from '~/types/leaderboard'

export const BOARD_META: Record<
  BoardType,
  { title: string; eyebrow: string; description: string; emptyHint: string; growthCol: string }
> = {
  total: {
    title: '总排名',
    eyebrow: 'OVERALL',
    description: '按当前 Star 总数排序的 Top 100。每日从 GitHub 同步快照。',
    emptyHint: '总榜暂无数据，请确认同步任务已运行。',
    growthCol: '',
  },
  daily: {
    title: '日增速榜',
    eyebrow: 'GROWTH · DAILY',
    description: '观察池（Top 500 + 新晋 + 既往增速成员）中，近 1 日 Star 增量 Top 100。',
    emptyHint: '日增速需要至少两天快照，请明天再来看看。',
    growthCol: '今日增速',
  },
  weekly: {
    title: '周增速榜',
    eyebrow: 'GROWTH · WEEKLY',
    description: '观察池中近 7 日 Star 增量 Top 100。历史不足时显示「数据积累中」。',
    emptyHint: '周增速约需积累 7 天快照，请稍后再来。',
    growthCol: '本周增速',
  },
  monthly: {
    title: '月增速榜',
    eyebrow: 'GROWTH · MONTHLY',
    description: '观察池中近 30 日 Star 增量 Top 100。历史不足时显示「数据积累中」。',
    emptyHint: '月增速约需积累 30 天快照，请稍后再来。',
    growthCol: '本月增速',
  },
  yearly: {
    title: '年增速榜',
    eyebrow: 'GROWTH · YEARLY',
    description: '观察池中近 365 日 Star 增量 Top 100。历史不足时显示「数据积累中」。',
    emptyHint: '年增速约需积累较长时间的快照，请稍后再来。',
    growthCol: '今年增速',
  },
}

export function formatGeneratedAt(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(d)
}
