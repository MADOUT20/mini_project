'use client'
// Client-side keyboard shortcut listener used across the app experience.

import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'

export function KeyboardShortcutsHandler() {
  useKeyboardShortcuts()
  return null
}
