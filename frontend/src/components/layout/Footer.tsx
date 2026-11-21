import { APP_CONFIG } from '../../constants/app';

export function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 py-4 px-6 text-center text-xs text-slate-500 dark:text-slate-400 transition-colors">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
        <span className="font-medium text-slate-600 dark:text-slate-400">
          © {new Date().getFullYear()} {APP_CONFIG.NAME}. Environmental Monitoring System.
        </span>
        <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400">
          <span>Design System Architecture</span>
          <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700" aria-hidden="true" />
          <span>Accessible • Responsive • Semantic</span>
        </div>
      </div>
    </footer>
  );
}
