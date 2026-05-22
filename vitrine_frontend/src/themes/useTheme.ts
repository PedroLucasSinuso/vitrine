import { useContext } from 'react'
import { ThemeContext, type Theme } from './ThemeProvider'

export function useTheme() {
  const ctx = useContext(ThemeContext)

  if (!ctx) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }

  const toggleTheme = () => {
    const next: Theme = ctx.theme === 'vitrine' ? 'flagship' : 'vitrine'
    ctx.setTheme(next)
  }

  return {
    theme: ctx.theme,
    setTheme: ctx.setTheme,
    isDark: ctx.isDark,
    toggleTheme,
  }
}
