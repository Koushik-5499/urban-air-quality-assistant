import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { LocationProvider } from './context/LocationContext';
import { RootLayout } from './layouts/RootLayout';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ROUTES } from './constants/routes';

// Code-split pages via React.lazy for optimized initial bundle delivery
const Dashboard = lazy(() => import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const LocationsPage = lazy(() =>
  import('./pages/LocationsPage').then((m) => ({ default: m.LocationsPage }))
);
const PollutantsPage = lazy(() =>
  import('./pages/PollutantsPage').then((m) => ({ default: m.PollutantsPage }))
);
const MapPage = lazy(() => import('./pages/MapPage').then((m) => ({ default: m.MapPage })));
const AssistantPage = lazy(() =>
  import('./pages/AssistantPage').then((m) => ({ default: m.AssistantPage }))
);
const AlertsPage = lazy(() =>
  import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage }))
);
const AnalyticsPage = lazy(() =>
  import('./pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage }))
);
const NotFoundPage = lazy(() =>
  import('./pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage }))
);

function RouteLoadingFallback() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center min-h-[50vh] p-8 space-y-3"
    >
      <LoadingSpinner size="lg" label="Loading application view..." />
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
        Loading view...
      </p>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LocationProvider>
        <BrowserRouter>
          <Suspense fallback={<RouteLoadingFallback />}>
            <Routes>
              <Route path="/" element={<RootLayout />}>
                <Route index element={<Dashboard />} />
                <Route path={ROUTES.LOCATIONS.slice(1)} element={<LocationsPage />} />
                <Route path={ROUTES.POLLUTANTS.slice(1)} element={<PollutantsPage />} />
                <Route path={ROUTES.MAP.slice(1)} element={<MapPage />} />
                <Route path={ROUTES.ASSISTANT.slice(1)} element={<AssistantPage />} />
                <Route path={ROUTES.ALERTS.slice(1)} element={<AlertsPage />} />
                <Route path={ROUTES.ANALYTICS.slice(1)} element={<AnalyticsPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </LocationProvider>
    </ThemeProvider>
  );
}
