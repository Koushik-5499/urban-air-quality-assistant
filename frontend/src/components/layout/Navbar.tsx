import {
  Wind,
  Moon,
  Sun,
  Menu,
  PanelLeftClose,
  PanelLeft,
  Activity,
} from 'lucide-react';
import { APP_CONFIG } from '../../constants/app';
import { useTheme } from '../../hooks/useTheme';
import { Badge } from '../ui/Badge';

export interface NavbarProps {
  isSidebarCollapsed: boolean;
  onToggleSidebarCollapse: () => void;
  onOpenMobileSidebar: () => void;
}

export function Navbar({
  isSidebarCollapsed,
  onToggleSidebarCollapse,
  onOpenMobileSidebar,
}: NavbarProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md transition-colors duration-200">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left Section: Controls & Brand */}
        <div className="flex items-center gap-3">
          {/* Mobile Menu Trigger */}
          <button
            type="button"
            onClick={onOpenMobileSidebar}
            aria-label="Open mobile navigation menu"
            className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 cursor-pointer"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>

          {/* Desktop Sidebar Collapse Toggle */}
          <button
            type="button"
            onClick={onToggleSidebarCollapse}
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="hidden md:flex items-center justify-center min-h-[44px] min-w-[44px] p-2 rounded-lg text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-colors cursor-pointer"
          >
            {isSidebarCollapsed ? (
              <PanelLeft className="h-5 w-5" aria-hidden="true" />
            ) : (
              <PanelLeftClose className="h-5 w-5" aria-hidden="true" />
            )}
          </button>

          {/* Logo and Brand Mark */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-md shadow-emerald-600/20">
              <Wind className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
                  {APP_CONFIG.NAME}
                </span>
                <span className="hidden sm:inline-flex rounded-full bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
                  v{APP_CONFIG.VERSION}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden lg:block leading-none mt-0.5">
                Environmental Telemetry & Atmospheric AI
              </p>
            </div>
          </div>
        </div>

        {/* Right Section: Network Status & Theme Toggle */}
        <div className="flex items-center gap-3">
          {/* Live Sensor Status Pill */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs text-slate-600 dark:text-slate-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping motion-reduce:hidden absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium">Sensors Live</span>
            <Activity className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" aria-hidden="true" />
          </div>

          <Badge variant="success" size="sm" showDot className="hidden md:inline-flex">
            Online
          </Badge>

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={
              theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'
            }
            title={
              theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'
            }
            className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 transition-colors cursor-pointer"
          >
            {theme === 'light' ? (
              <Moon className="h-4 w-4 text-slate-700 hover:text-slate-900 transition-transform duration-200 hover:-rotate-12" aria-hidden="true" />
            ) : (
              <Sun className="h-4 w-4 text-amber-400 hover:text-amber-300 transition-transform duration-200 hover:rotate-45" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
