import React, { useEffect, useState, useMemo } from 'react';
import { ThemeContext, type Theme } from './theme-context-def';

export type { Theme };

const STORAGE_KEY = 'uaqa_theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Initialize with light theme as default
  const [theme, setThemeState] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored === 'dark') return 'dark';
      if (stored === 'light') return 'light';
      // Default is light per specifications
      return 'light';
    } catch {
      return 'light';
    }
  });

  const isDark = theme === 'dark';

  useEffect(() => {
    const root = document.documentElement;
    const metaTheme = document.getElementById('theme-meta');

    if (theme === 'dark') {
      root.classList.add('dark');
      root.setAttribute('data-theme', 'dark');
      if (metaTheme) metaTheme.setAttribute('content', '#0B0F19');
    } else {
      root.classList.remove('dark');
      root.setAttribute('data-theme', 'light');
      if (metaTheme) metaTheme.setAttribute('content', '#F8FAFC');
    }

    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Storage unavailable fallback
    }
  }, [theme]);

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const value = useMemo(
    () => ({
      theme,
      isDark,
      toggleTheme,
      setTheme,
    }),
    [theme, isDark]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
