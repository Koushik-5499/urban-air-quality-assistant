import { useMemo } from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { AQIPopup } from './AQIPopup';
import { getAQIColor } from '../../data/mapData';
import type { MapCityData } from '../../types/map';

export interface AQIMarkerProps {
  city: MapCityData;
  isSelected: boolean;
  isActiveDashboardCity: boolean;
  onSelectCity: (city: MapCityData) => void;
  onSelectForDashboard: (cityId: string) => void;
  onViewDetails: (city: MapCityData) => void;
}

export function AQIMarker({
  city,
  isSelected,
  isActiveDashboardCity,
  onSelectCity,
  onSelectForDashboard,
  onViewDetails,
}: AQIMarkerProps) {
  const icon = useMemo(() => {
    const color = getAQIColor(city.category);
    const ringHtml = isSelected
      ? `<span style="position:absolute; top:-6px; left:-6px; right:-6px; bottom:-6px; border-radius:9999px; border:2px solid #10b981; animation:ping 1.5s cubic-bezier(0,0,0.2,1) infinite; opacity:0.75;"></span>
         <span style="position:absolute; top:-3px; left:-3px; right:-3px; bottom:-3px; border-radius:9999px; border:2px solid #ffffff; box-shadow:0 0 8px rgba(0,0,0,0.3);"></span>`
      : '';

    const html = `
      <div style="position:relative; display:flex; flex-direction:column; align-items:center; cursor:pointer;" title="${city.city}: AQI ${city.aqi} (${city.category})">
        ${ringHtml}
        <div style="display:flex; align-items:center; gap:4px; padding:3px 8px; border-radius:9999px; background-color:${color}; color:#ffffff; font-weight:800; font-size:11px; font-family:ui-monospace, monospace; box-shadow:0 4px 6px -1px rgba(0,0,0,0.3); border:1.5px solid rgba(255,255,255,0.85); white-space:nowrap;">
          <span style="width:5px; height:5px; border-radius:9999px; background-color:#ffffff;"></span>
          <span>${city.aqi}</span>
        </div>
        <div style="width:6px; height:6px; transform:rotate(45deg); margin-top:-3px; background-color:${color}; box-shadow:0 1px 2px rgba(0,0,0,0.2);"></div>
        <span style="margin-top:2px; font-size:10px; font-weight:700; color:#1e293b; text-shadow:0 1px 3px #ffffff, 0 -1px 3px #ffffff, 1px 0 3px #ffffff, -1px 0 3px #ffffff; white-space:nowrap;">
          ${city.city}
        </span>
      </div>
    `;

    return L.divIcon({
      className: 'aqi-custom-marker-icon',
      html,
      iconSize: [44, 44],
      iconAnchor: [22, 22],
      popupAnchor: [0, -20],
    });
  }, [city.aqi, city.category, city.city, isSelected]);

  return (
    <Marker
      position={[city.lat, city.lng]}
      icon={icon}
      eventHandlers={{
        click: () => onSelectCity(city),
      }}
    >
      <Popup className="aqi-custom-popup">
        <AQIPopup
          city={city}
          isActiveDashboardCity={isActiveDashboardCity}
          onSelectForDashboard={onSelectForDashboard}
          onViewDetails={onViewDetails}
        />
      </Popup>
    </Marker>
  );
}

