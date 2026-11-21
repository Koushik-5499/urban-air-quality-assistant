import {
  LayoutDashboard,
  MapPin,
  Wind,
  Map,
  Bot,
  Bell,
  BarChart3,
} from 'lucide-react';
import { ROUTES } from '../constants/routes';
import type { NavItem } from '../types/navigation';

export const NAVIGATION_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    path: ROUTES.DASHBOARD,
    icon: LayoutDashboard,
    description: 'Real-time air quality index and live urban sensors',
  },
  {
    label: 'Locations',
    path: ROUTES.LOCATIONS,
    icon: MapPin,
    description: 'City stations, regional monitoring hubs, and geographic filters',
  },
  {
    label: 'Pollutants',
    path: ROUTES.POLLUTANTS,
    icon: Wind,
    description: 'PM2.5, PM10, NO2, SO2, CO, and O3 concentration metrics',
  },
  {
    label: 'Pollution Map',
    path: ROUTES.MAP,
    icon: Map,
    description: 'Interactive heatmaps, spatial distribution, and hotspots',
  },
  {
    label: 'AI Assistant',
    path: ROUTES.ASSISTANT,
    icon: Bot,
    description: 'Intelligent air quality advisor, queries, and health recommendations',
  },
  {
    label: 'Alerts',
    path: ROUTES.ALERTS,
    icon: Bell,
    description: 'Threshold alerts, health warnings, and notification settings',
  },
  {
    label: 'Analytics',
    path: ROUTES.ANALYTICS,
    icon: BarChart3,
    description: 'Historical trends, comparative analysis, and forecasts',
  },
];

