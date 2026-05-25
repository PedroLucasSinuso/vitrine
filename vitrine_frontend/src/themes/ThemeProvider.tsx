/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useEffect, useCallback, type ReactNode } from 'react'

export type Theme = 'vitrine' | 'flagship'

interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
  isDark: boolean
}

export const ThemeContext = createContext<ThemeContextValue>({
  theme: 'vitrine',
  setTheme: () => {},
  isDark: false,
})

const STORAGE_KEY = 'vitrine_theme'
const LEGACY_DARK_KEY = 'app_darkMode'
const DEFAULT_THEME: Theme = 'vitrine'

/** Migrate legacy app_darkMode → vitrine_theme */
function migrateLegacyTheme(): Theme {
  const legacyDark = localStorage.getItem(LEGACY_DARK_KEY)
  if (legacyDark === 'true') {
    localStorage.removeItem(LEGACY_DARK_KEY)
    return 'flagship'
  }
  return DEFAULT_THEME
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return DEFAULT_THEME
    return (localStorage.getItem(STORAGE_KEY) as Theme) || migrateLegacyTheme()
  })

  const [isDark, setIsDark] = useState(() => theme === 'flagship')

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next)
    localStorage.setItem(STORAGE_KEY, next)
    setIsDark(next === 'flagship')
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.classList.toggle('dark', theme === 'flagship')
  }, [theme])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, isDark }}>
      {children}
    </ThemeContext.Provider>
  )
}
