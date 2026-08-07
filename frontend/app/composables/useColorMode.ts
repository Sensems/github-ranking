import { ref } from 'vue'

export type ColorMode = 'dark' | 'light'

const STORAGE_KEY = 'color-mode'

const mode = ref<ColorMode>('dark')

function apply(next: ColorMode) {
  mode.value = next
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', next === 'dark')
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    /* ignore quota / private mode */
  }
}

export function useAppColorMode() {
  function applyStored() {
    let stored: string | null = null
    try {
      stored = localStorage.getItem(STORAGE_KEY)
    } catch {
      stored = null
    }
    apply(stored === 'light' ? 'light' : 'dark')
  }

  function toggle() {
    apply(mode.value === 'dark' ? 'light' : 'dark')
  }

  return { mode, toggle, applyStored, apply }
}
