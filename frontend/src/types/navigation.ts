import type { LucideIcon } from 'lucide-react';
import type { AppRoute } from '../constants/routes';

export interface NavItem {
  label: string;
  path: AppRoute;
  icon: LucideIcon;
  description: string;
}

