export function useBoardGeneratedAt() {
  return useState<string | null>('board-generated-at', () => null)
}
