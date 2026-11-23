import type { CityDashboardData } from '../../types/dashboard';
import { DEMO_LOCATIONS } from './locations';
import { coimbatoreData } from './coimbatore';
import { chennaiData } from './chennai';
import { bengaluruData } from './bengaluru';
import { hyderabadData } from './hyderabad';
import { mumbaiData } from './mumbai';
import { delhiData } from './delhi';
import { kochiData } from './kochi';
import { puneData } from './pune';
import { kolkataData } from './kolkata';
import { thoothukudiData } from './thoothukudi';

export const DASHBOARD_DATA: Record<string, CityDashboardData> = {
  coimbatore: coimbatoreData,
  chennai: chennaiData,
  bengaluru: bengaluruData,
  hyderabad: hyderabadData,
  mumbai: mumbaiData,
  delhi: delhiData,
  kochi: kochiData,
  pune: puneData,
  kolkata: kolkataData,
  thoothukudi: thoothukudiData,
};

export { DEMO_LOCATIONS };
