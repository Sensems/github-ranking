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
  growth: Growth
  summary: Summary | null
}

export interface LeaderboardPayload {
  type: string
  generated_at: string
  items: LeaderboardItem[]
}

export type BoardType = 'total' | 'daily' | 'weekly' | 'monthly' | 'yearly'
