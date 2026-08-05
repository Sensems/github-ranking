import { createHash } from 'node:crypto'
import type { Summary } from '~/types/leaderboard'

export const README_TRUNCATE_CHARS = 30_000

/** Identical intent / schema to scripts/summary.py SYSTEM_PROMPT. */
export const SYSTEM_PROMPT =
  '你是一个技术文档摘要专家，请用简洁的中文概括以下GitHub项目的README内容。' +
  '严格输出 JSON，格式为：{"project_positioning": "一句话定位", ' +
  '"core_features": ["功能1", "功能2", "功能3"], ' +
  '"use_cases": ["场景1", "场景2"], ' +
  '"tech_stack": ["技术栈1", "技术栈2"]}'

const SUMMARY_KEYS = [
  'project_positioning',
  'core_features',
  'use_cases',
  'tech_stack',
] as const

export type XfyunConfig = {
  apiKey: string
  baseUrl: string
  model: string
}

/** Join base URL to chat/completions without double slashes. */
export function chatCompletionsUrl(baseUrl: string): string {
  return `${baseUrl.replace(/\/?$/, '/')}chat/completions`
}

export function parseSummaryContent(content: string): Summary {
  let text = content.trim()
  if (text.startsWith('```')) {
    const lines = text.split(/\r?\n/)
    lines.shift()
    if (lines.length && lines[lines.length - 1].trim() === '```') {
      lines.pop()
    }
    text = lines.join('\n').trim()
  }
  const data = JSON.parse(text) as unknown
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('summary is not a JSON object')
  }
  const obj = data as Record<string, unknown>
  for (const key of SUMMARY_KEYS) {
    if (!(key in obj)) {
      throw new Error(`missing key: ${key}`)
    }
  }
  return obj as Summary
}

export function hashReadme(content: string): string {
  return createHash('sha256').update(content, 'utf8').digest('hex')
}

export async function callXfyunChat(
  readme: string,
  cfg: XfyunConfig,
  fetchImpl: typeof fetch = fetch,
): Promise<string> {
  const url = chatCompletionsUrl(cfg.baseUrl)
  const res = await fetchImpl(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${cfg.apiKey}`,
    },
    body: JSON.stringify({
      model: cfg.model,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: readme },
      ],
      temperature: 0.3,
      max_tokens: 1024,
    }),
  })
  if (!res.ok) {
    throw new Error(`xfyun HTTP ${res.status}`)
  }
  const data = (await res.json()) as {
    choices?: Array<{ message?: { content?: string } }>
  }
  const content = data?.choices?.[0]?.message?.content
  if (typeof content !== 'string' || !content.trim()) {
    throw new Error('xfyun empty content')
  }
  return content
}

export async function generateSummary(
  readme: string,
  cfg: XfyunConfig,
  fetchImpl: typeof fetch = fetch,
): Promise<Summary> {
  const content = await callXfyunChat(readme, cfg, fetchImpl)
  return parseSummaryContent(content)
}

/** Fetch README via raw.githubusercontent.com (same variants as Python client). */
export async function fetchReadmeFromGithub(
  repoName: string,
  truncateChars: number = README_TRUNCATE_CHARS,
  fetchImpl: typeof fetch = fetch,
): Promise<string | null> {
  for (const filename of ['README.md', 'readme.md', 'Readme.md'] as const) {
    const url = `https://raw.githubusercontent.com/${repoName}/HEAD/${filename}`
    const res = await fetchImpl(url)
    if (res.status === 200) {
      const text = await res.text()
      return text.slice(0, truncateChars)
    }
    if (res.status !== 404) {
      throw new Error(`readme fetch HTTP ${res.status}`)
    }
  }
  return null
}
