import { useEffect } from 'react';
import { APP_CONFIG } from '../constants/app';

export function useDocumentTitle(title?: string): void {
  useEffect(() => {
    document.title = title
      ? `${title} — ${APP_CONFIG.NAME}`
      : APP_CONFIG.DEFAULT_TITLE;
  }, [title]);
}

