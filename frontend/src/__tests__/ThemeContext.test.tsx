import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../context/ThemeContext';
import { useTheme } from '../hooks/useTheme';

function ThemeConsumer() {
  const { theme, toggleTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
}

describe('ThemeContext', () => {
  it('provides a default theme of light or dark', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    const themeValue = screen.getByTestId('theme-value').textContent;
    expect(['light', 'dark']).toContain(themeValue);
  });

  it('toggles theme on button click', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    const initial = screen.getByTestId('theme-value').textContent;
    fireEvent.click(screen.getByText('Toggle'));
    const after = screen.getByTestId('theme-value').textContent;
    expect(after).not.toBe(initial);
    expect(['light', 'dark']).toContain(after);
  });

  it('toggles back to initial theme on second click', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>
    );
    const initial = screen.getByTestId('theme-value').textContent;
    fireEvent.click(screen.getByText('Toggle'));
    fireEvent.click(screen.getByText('Toggle'));
    const final = screen.getByTestId('theme-value').textContent;
    expect(final).toBe(initial);
  });
});

