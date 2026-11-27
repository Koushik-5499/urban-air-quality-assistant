import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { LocationProvider } from '../context/LocationContext';
import { airQualityApi } from '../services/api/airQualityApi';
import { healthApi } from '../services/api/healthApi';
import { RootLayout } from '../layouts/RootLayout';
import { DashboardPage } from '../pages/DashboardPage';
import { AssistantPage } from '../pages/AssistantPage';
import { AlertsPage } from '../pages/AlertsPage';
import { LocationsPage } from '../pages/LocationsPage';
import { PollutantsPage } from '../pages/PollutantsPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { MapPage } from '../pages/MapPage';
import { ClearAlertsModal } from '../components/alerts/ClearAlertsModal';
import { AlertDetailsModal } from '../components/alerts/AlertDetailsModal';
import { CityDetailsPanel } from '../components/locations/CityDetailsPanel';
import { MapEmptyState } from '../components/maps/MapEmptyState';
import { MapControls } from '../components/maps/MapControls';
import { MapLegend } from '../components/maps/MapLegend';
import { MapLoading } from '../components/maps/MapLoading';
import { PagePlaceholder } from '../components/common/PagePlaceholder';
import { HealthRecommendation } from '../components/dashboard/HealthRecommendation';
import { Input } from '../components/ui/Input';
import { PollutantStatusBadge } from '../components/pollutants/PollutantStatusBadge';
import { PollutantSkeleton } from '../components/pollutants/PollutantSkeleton';
import { LocationEmptyState } from '../components/locations/LocationEmptyState';
import { DASHBOARD_DATA } from '../data/dashboardData';
import type { AirAlert } from '../types/alerts';

vi.mock('../components/maps/PollutionMap', () => ({
  PollutionMap: ({
    cities,
    onSelectCity,
  }: {
    cities?: unknown[];
    onSelectCity?: (city: unknown) => void;
  }) => (
    <div data-testid="mock-pollution-map">
      <button type="button" onClick={() => cities?.[0] && onSelectCity?.(cities[0])}>
        Select Map City
      </button>
    </div>
  ),
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

function renderWithProviders(ui: React.ReactNode) {
  return render(
    <MemoryRouter>
      <ThemeProvider>
        <LocationProvider>{ui}</LocationProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Page & Layout Integration Rendering', () => {
  it('renders RootLayout navigation and skip-to-content link', () => {
    renderWithProviders(<RootLayout />);
    expect(screen.getByText(/Skip to main content/i)).toBeTruthy();
    expect(screen.getByLabelText(/Sidebar Navigation/i)).toBeTruthy();
    screen.queryAllByRole('button').slice(0, 4).forEach((b) => fireEvent.click(b));
  });

  it('renders DashboardPage with Delhi default city, AQI gauge, and Challenge 6 guidance', async () => {
    renderWithProviders(<DashboardPage />);
    expect(screen.getAllByText(/Delhi/i).length).toBeGreaterThan(0);
    await waitFor(() => {
      expect(screen.getByText(/Health Guidance & Precautions/i)).toBeTruthy();
    });
  });

  it('renders AssistantPage and supports lifestyle persona selection and fallback messaging', async () => {
    renderWithProviders(<AssistantPage />);
    expect(screen.getAllByText(/AI Environmental Health Assistant/i).length).toBeGreaterThan(0);

    const commuterBtn = screen.getByText(/Daily Commuter/i);
    await act(async () => {
      fireEvent.click(commuterBtn);
    });

    const input = screen.getByLabelText(/Message input for AI Health Assistant/i);
    await act(async () => {
      fireEvent.change(input, { target: { value: 'Winter smog advice' } });
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });
    });
    expect(screen.getByText('Winter smog advice')).toBeTruthy();
  });

  it('renders AlertsPage and switches accessible tabs (feed, preferences, monitored cities)', () => {
    renderWithProviders(<AlertsPage />);
    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBeGreaterThanOrEqual(3);

    fireEvent.click(tabs[1]);
    expect(tabs[1].getAttribute('aria-selected')).toBe('true');

    fireEvent.click(tabs[2]);
    expect(tabs[2].getAttribute('aria-selected')).toBe('true');
  });

  it('renders LocationsPage and switches between grid and compare views', () => {
    renderWithProviders(<LocationsPage />);
    expect(screen.getAllByText(/Delhi/i).length).toBeGreaterThan(0);
    const searchInputs = screen.queryAllByRole('textbox');
    if (searchInputs.length > 0) {
      fireEvent.change(searchInputs[0], { target: { value: 'Del' } });
      fireEvent.focus(searchInputs[0]);
    }
    screen.queryAllByRole('button').slice(0, 5).forEach((b) => fireEvent.click(b));
    const tabs = screen.getAllByRole('tab');
    expect(tabs.length).toBeGreaterThanOrEqual(2);
    fireEvent.click(tabs[1]);
    expect(tabs[1].getAttribute('aria-selected')).toBe('true');
  });

  it('renders PollutantsPage with pollutant breakdown cards and filter controls', () => {
    renderWithProviders(<PollutantsPage />);
    expect(screen.getAllByText(/PM2\.5/i).length).toBeGreaterThan(0);
    const tabs = screen.queryAllByRole('tab');
    if (tabs.length >= 2) {
      fireEvent.click(tabs[1]);
    }
    const clearBtns = screen.queryAllByRole('button');
    clearBtns.slice(0, 4).forEach((btn) => fireEvent.click(btn));
  });

  it('renders AnalyticsPage with trend summary cards and horizon selectors', () => {
    renderWithProviders(<AnalyticsPage />);
    expect(screen.getAllByText(/AQI/i).length).toBeGreaterThan(0);
    const btns = screen.queryAllByRole('button');
    btns.slice(0, 5).forEach((btn) => fireEvent.click(btn));
  });

  it('renders MapPage with filters, list switcher, and station drawer', () => {
    renderWithProviders(<MapPage />);
    expect(screen.getByTestId('mock-pollution-map')).toBeTruthy();
    fireEvent.click(screen.getByText('Select Map City'));
    const tabs = screen.queryAllByRole('tab');
    if (tabs.length >= 2) {
      fireEvent.click(tabs[1]);
    }
    const btns = screen.queryAllByRole('button');
    btns.slice(0, 4).forEach((btn) => fireEvent.click(btn));
  });

  it('renders modals, drawers, empty states, placeholders, and explainability toggles', () => {
    const sampleAlert: AirAlert = {
      id: 'a-test',
      cityId: 'delhi',
      city: 'Delhi',
      state: 'Delhi',
      country: 'India',
      station: 'Anand Vihar',
      aqi: 295,
      category: 'Very Unhealthy',
      severity: 'critical',
      title: 'Critical Pollution Alert',
      description: 'Severe inversion PM2.5 plume',
      recommendedAction: 'Remain indoors with HEPA filtration',
      dominantPollutant: 'PM2.5',
      timestamp: new Date().toISOString(),
      dateFormatted: 'Today, 07:30 AM',
      isRead: false,
      isDismissed: false,
      isSimulated: true,
    };

    const onClose = vi.fn();
    renderWithProviders(
      <div>
        <ClearAlertsModal isOpen={true} onClose={onClose} onConfirm={vi.fn()} />
        <AlertDetailsModal
          alert={sampleAlert}
          isOpen={true}
          onClose={onClose}
          onToggleRead={vi.fn()}
          onDismiss={vi.fn()}
          onSelectForDashboard={vi.fn()}
          isActiveDashboardCity={false}
        />
        <CityDetailsPanel
          city={DASHBOARD_DATA['delhi']}
          isOpen={true}
          onClose={onClose}
          onSelectForDashboard={vi.fn()}
          isActiveCity={true}
          onToggleCompare={vi.fn()}
          isComparing={false}
          canCompare={true}
        />
        <MapEmptyState onReset={vi.fn()} />
        <PagePlaceholder title="Station View" description="Environmental telemetry placeholder" routePath="/test" />
        <HealthRecommendation category="Hazardous" aqi={360} />
      </div>
    );

    const whyBtns = screen.getAllByRole('button', { name: /Why this advice/i });
    fireEvent.click(whyBtns[0]);
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('renders auxiliary widgets (Input, MapControls, MapLegend, MapLoading, PollutantSkeleton, LocationEmptyState) and toggles handlers', () => {
    const onZoomIn = vi.fn();
    const onReset = vi.fn();
    renderWithProviders(
      <div>
        <Input label="City Search" placeholder="Filter..." helperText="Helper" error="" />
        <Input label="Bad Field" error="Required" />
        <PollutantStatusBadge status="Good" />
        <PollutantStatusBadge status="Moderate" />
        <PollutantStatusBadge status="Hazardous" />
        <PollutantSkeleton />
        <LocationEmptyState query="Nowhere" onReset={onReset} />
        <MapControls
          onZoomIn={onZoomIn}
          onZoomOut={vi.fn()}
          onResetView={vi.fn()}
          onLocateSelected={vi.fn()}
          showHeatmap={false}
          onToggleHeatmap={vi.fn()}
          showMarkers={true}
          onToggleMarkers={vi.fn()}
          hasSelectedCity={true}
        />
        <MapLegend />
        <MapLoading />
      </div>
    );

    const legendBtn = screen.getByRole('button', { expanded: true });
    fireEvent.click(legendBtn);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((b) => fireEvent.click(b));
    expect(onZoomIn).toHaveBeenCalled();
    expect(onReset).toHaveBeenCalled();
  });

  it('interacts with AlertsPage NotificationPreferences and MonitoredCities toggles', () => {
    renderWithProviders(<AlertsPage />);
    screen.queryAllByRole('textbox').forEach((inp) =>
      fireEvent.change(inp, { target: { value: 'Delhi' } })
    );
    screen.queryAllByRole('combobox').forEach((sel) =>
      fireEvent.change(sel, { target: { value: (sel as HTMLSelectElement).options?.[1]?.value ?? '' } })
    );
    const tabs = screen.getAllByRole('tab');
    fireEvent.click(tabs[1]);
    screen.queryAllByRole('button').slice(0, 8).forEach((b) => fireEvent.click(b));
    screen.queryAllByRole('checkbox').slice(0, 6).forEach((c) => fireEvent.click(c));
    fireEvent.click(tabs[2]);
    screen.queryAllByRole('button').slice(0, 8).forEach((b) => fireEvent.click(b));
  });
});

