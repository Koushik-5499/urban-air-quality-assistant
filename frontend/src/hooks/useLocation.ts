import { useContext } from 'react';
import { LocationContext, type LocationContextType } from '../context/location-context-def';

export function useLocation(): LocationContextType {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocation must be used within a LocationProvider');
  }
  return context;
}

