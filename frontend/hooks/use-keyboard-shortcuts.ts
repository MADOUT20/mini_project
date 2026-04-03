// Reusable frontend hook for use keyboard shortcuts behavior.
import { useEffect } from 'react'

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+R or Cmd+R to refresh the page
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault()
        window.location.reload()
      }

      // Ctrl+Shift+A to toggle admin panel (if admin is logged in)
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'a') {
        e.preventDefault()
        const adminPanel = document.getElementById('admin-panel')
        if (adminPanel) {
          adminPanel.style.display = adminPanel.style.display === 'none' ? 'block' : 'none'
        }
      }

      // Ctrl+K for search/command palette (future feature)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        console.log('[v0] Command palette shortcut triggered')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])
}
