import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('useAppColorMode', () => {
  beforeEach(() => {
    vi.resetModules()
    document.documentElement.classList.remove('dark')
    localStorage.clear()
  })

  it('defaults to dark and toggles to light with persistence', async () => {
    const { useAppColorMode } = await import('./useColorMode')
    const { mode, toggle, applyStored } = useAppColorMode()

    applyStored()
    expect(mode.value).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    toggle()
    expect(mode.value).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(localStorage.getItem('color-mode')).toBe('light')

    toggle()
    expect(mode.value).toBe('dark')
    expect(localStorage.getItem('color-mode')).toBe('dark')
  })

  it('restores light from localStorage', async () => {
    localStorage.setItem('color-mode', 'light')
    const { useAppColorMode } = await import('./useColorMode')
    const { mode, applyStored } = useAppColorMode()
    applyStored()
    expect(mode.value).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
