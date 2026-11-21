import { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { AQIMarker } from './AQIMarker';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';
import { MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM, getAQIColor } from '../../data/mapData';
import type { MapCityData } from '../../types/map';

export interface PollutionMapProps {
  cities: MapCityData[];
  selectedCity: MapCityData | null;
  activeDashboardCityId: string;
  onSelectCity: (city: MapCityData) => void;
  onSelectForDashboard: (cityId: string) => void;
  onViewDetails: (city: MapCityData) => void;
  showHeatmap: boolean;
  onToggleHeatmap: () => void;
  showMarkers: boolean;
  onToggleMarkers: () => void;
  resetTrigger: number;
  onResetView: () => void;
  focusTrigger: number;
}

// Controller component to manipulate the Leaflet map instance via React hook
function MapViewController({
  selectedCity,
  focusTrigger,
  resetTrigger,
}: {
  selectedCity: MapCityData | null;
  focusTrigger: number;
  resetTrigger: number;
}) {
  const map = useMap();

  // Invalidate size on mount to handle rendering inside flex containers
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);

  // Center on selected city when focusTrigger increments or selected city changes
  useEffect(() => {
    if (selectedCity && focusTrigger > 0) {
      map.flyTo([selectedCity.lat, selectedCity.lng], 8, {
        duration: 1.2,
      });
    }
  }, [map, selectedCity, focusTrigger]);

  // Reset to whole India view when resetTrigger increments
  useEffect(() => {
    if (resetTrigger > 0) {
      map.flyTo(MAP_DEFAULT_CENTER, MAP_DEFAULT_ZOOM, {
        duration: 1.0,
      });
    }
  }, [map, resetTrigger]);

  return null;
}

// Map Zoom buttons handler
function MapZoomButtons() {
  const map = useMap();

  useEffect(() => {
    (window as unknown as { __leafletZoomIn?: () => void }).__leafletZoomIn = () => map.zoomIn();
    (window as unknown as { __leafletZoomOut?: () => void }).__leafletZoomOut = () => map.zoomOut();
  }, [map]);

  return null;
}

export function PollutionMap({
  cities,
  selectedCity,
  activeDashboardCityId,
  onSelectCity,
  onSelectForDashboard,
  onViewDetails,
  showHeatmap,
  onToggleHeatmap,
  showMarkers,
  onToggleMarkers,
  resetTrigger,
  onResetView,
  focusTrigger,
}: PollutionMapProps) {
  const handleZoomIn = () => {
    const win = window as unknown as { __leafletZoomIn?: () => void };
    if (win.__leafletZoomIn) win.__leafletZoomIn();
  };

  const handleZoomOut = () => {
    const win = window as unknown as { __leafletZoomOut?: () => void };
    if (win.__leafletZoomOut) win.__leafletZoomOut();
  };

  return (
    <div className="relative w-full h-[540px] sm:h-[620px] rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-md">
      <MapContainer
        center={MAP_DEFAULT_CENTER}
        zoom={MAP_DEFAULT_ZOOM}
        zoomControl={false}
        scrollWheelZoom={true}
        className="w-full h-full z-0 bg-slate-100 dark:bg-slate-950"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        <MapViewController
          selectedCity={selectedCity}
          focusTrigger={focusTrigger}
          resetTrigger={resetTrigger}
        />

        <MapZoomButtons />

        {/* Optional Heatmap Dispersion Circles */}
        {showHeatmap &&
          cities.map((city) => {
            const color = getAQIColor(city.category);
            const radiusMeters = 40000 + city.aqi * 500; // 50km to 140km radius

            return (
              <Circle
                key={`heatmap-${city.id}`}
                center={[city.lat, city.lng]}
                radius={radiusMeters}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: 0.28,
                  color: color,
                  weight: 1.5,
                  opacity: 0.45,
                }}
              />
            );
          })}

        {/* AQI City Markers */}
        {showMarkers &&
          cities.map((city) => (
            <AQIMarker
              key={city.id}
              city={city}
              isSelected={selectedCity?.id === city.id}
              isActiveDashboardCity={city.id === activeDashboardCityId}
              onSelectCity={onSelectCity}
              onSelectForDashboard={onSelectForDashboard}
              onViewDetails={onViewDetails}
            />
          ))}
      </MapContainer>

      {/* Floating Controls Overlay (Top Right) */}
      <div className="absolute top-4 right-4 z-[400]">
        <MapControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onResetView={onResetView}
          onLocateSelected={() => onSelectCity(selectedCity || cities[0])}
          showHeatmap={showHeatmap}
          onToggleHeatmap={onToggleHeatmap}
          showMarkers={showMarkers}
          onToggleMarkers={onToggleMarkers}
          hasSelectedCity={Boolean(selectedCity)}
        />
      </div>

      {/* Floating Legend Overlay (Bottom Left) */}
      <div className="absolute bottom-4 left-4 z-[400] max-w-sm sm:max-w-md">
        <MapLegend />
      </div>
    </div>
  );
}
