import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { axe } from 'vitest-axe';
import { ThemeProvider } from '../context/ThemeContext';
import { LocationProvider } from '../context/LocationContext';
import { airQualityApi } from '../services/api/airQualityApi';
import { healthApi } from '../services/api/healthApi';
import { RootLayout } from '../layouts/RootLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { LocationsPage } from '../pages/LocationsPage';
import { PollutantsPage } from '../pages/PollutantsPage';
import { MapPage } from '../pages/MapPage';
import { AssistantPage } from '../pages/AssistantPage';
import { AlertsPage } from '../pages/AlertsPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { NotFoundPage } from '../pages/NotFoundPage';

vi.mock('../components/maps/PollutionMap', () => ({
  PollutionMap: () => <div role="region" data-testid="mock-pollution-map" aria-label="Interactive air quality map" />,
}));

beforeAll(() => {
  if (typeof globalThis.ResizeObserver === 'undefined') {
    globalThis.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = vi.fn();
  }
});

beforeEach(() => {
  vi.spyOn(airQualityApi, 'getCityAirQuality').mockRejectedValue(new Error('offline test'));
  vi.spyOn(airQualityApi, 'calculateAqi').mockRejectedValue(new Error('offline test'));
  vi.spyOn(airQualityApi, 'getCities').mockResolvedValue([]);
  vi.spyOn(healthApi, 'askAssistant').mockRejectedValue(new Error('offline test'));
});

function renderPage(ui: React.ReactNode, wrapInMain = true) {
  const content = wrapInMain ? <main>{ui}</main> : ui;
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <LocationProvider>{content}</LocationProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Page-Level WCAG Accessibility Audits (vitest-axe)', () => {
  it('RootLayout navigation, landmarks, and skip link pass axe', async () => {
    const { container } = renderPage(<RootLayout />, false);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('DashboardPage passes axe audit and exposes chart table alternative', async () => {
    const { container } = renderPage(<DashboardPage />);
    await waitFor(() => {
      expect(container.querySelector('table caption')?.textContent).toContain('Hourly AQI');
    });
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('LocationsPage passes axe audit', async () => {
    const { container } = renderPage(<LocationsPage />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('PollutantsPage passes axe audit', async () => {
    const { container } = renderPage(<PollutantsPage />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('MapPage passes axe audit', async () => {
    const { container } = renderPage(<MapPage />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('AssistantPage passes axe audit', async () => {
    const { container } = renderPage(<AssistantPage />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('AlertsPage passes axe audit', async () => {
    const { container } = renderPage(<AlertsPage />);
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('AnalyticsPage passes axe audit and exposes chart table alternatives', async () => {
    const { container } = renderPage(<AnalyticsPage />);
    await waitFor(() => {
      expect(container.querySelectorAll('table caption').length).toBeGreaterThanOrEqual(2);
    });
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('NotFoundPage passes axe audit with level-one heading', async () => {
    const { container } = renderPage(<NotFoundPage />);
    expect(container.querySelector('h1')?.textContent).toContain('Page Not Found');
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });
});
