export interface Growth {
  daily: number | null
  weekly: number | null
  monthly: number | null
  yearly: number | null
}

export interface Summary {
  project_positioning: string
  core_features: string[]
  use_cases: string[]
  tech_stack: string[]
}

export interface LeaderboardItem {
  rank: number
  repo_id: number
  repo_name: string
  description: string
  language: string | null
  stars: number
  forks: number
  html_url: string
  open_issues?: number
  pushed_at?: string | null
  growth: Growth
  has_summary?: boolean
  /** Present when Nitro joined a cached row from `summaries`. */
  summary?: Summary
}

export interface LeaderboardPayload {
  type: string
  generated_at: string | null
  items: LeaderboardItem[]
}

export type BoardType = 'total' | 'daily' | 'weekly' | 'monthly' | 'yearly'
