import { NavLink } from 'react-router-dom';
import { ChevronLeft, ChevronRight, X, ShieldCheck } from 'lucide-react';
import { NAVIGATION_ITEMS } from '../../data/navigation';
import { cn } from '../../utils/cn';

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  isMobileDrawer?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({
  collapsed,
  onToggleCollapse,
  isMobileDrawer = false,
  onCloseMobile,
}: SidebarProps) {
  return (
    <aside
      aria-label="Sidebar Navigation"
      className={cn(
        'flex flex-col justify-between border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/70 transition-all duration-300 ease-in-out',
        isMobileDrawer
          ? 'w-full h-full p-4'
          : cn(
              'hidden md:flex shrink-0 border-r min-h-[calc(100vh-4rem)]',
              collapsed ? 'w-20 p-3' : 'w-64 p-4'
            )
      )}
    >
      <div className="space-y-4">
        {/* Mobile Drawer Header */}
        {isMobileDrawer && (
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Navigation Menu
            </span>
            <button
              type="button"
              onClick={onCloseMobile}
              aria-label="Close navigation menu"
              className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2 rounded-lg text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Section Header for desktop expanded */}
        {!isMobileDrawer && !collapsed && (
          <div className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Platform Views
          </div>
        )}

        {/* Navigation Items List */}
        <nav className="space-y-1.5" aria-label="Main Navigation">
          {NAVIGATION_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                onClick={onCloseMobile}
                title={collapsed && !isMobileDrawer ? item.label : undefined}
                className={({ isActive }) =>
                  cn(
                    'group flex items-center rounded-xl font-medium transition-all duration-150 relative select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500',
                    collapsed && !isMobileDrawer
                      ? 'justify-center p-3 text-sm'
                      : 'gap-3 px-3.5 py-2.5 text-sm',
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-semibold border border-emerald-200/80 dark:border-emerald-800/60 shadow-xs'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {/* Active Accent Pill */}
                    {isActive && (
                      <span
                        className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-emerald-600 dark:bg-emerald-400"
                        aria-hidden="true"
                      />
                    )}

                    <Icon
                      className={cn(
                        'shrink-0 transition-colors',
                        collapsed && !isMobileDrawer ? 'h-5 w-5' : 'h-4 w-4',
                        isActive
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-slate-500 group-hover:text-slate-900 dark:text-slate-400 dark:group-hover:text-white'
                      )}
                      aria-hidden="true"
                    />

                    {/* Label (visible when expanded or on mobile drawer) */}
                    {(!collapsed || isMobileDrawer) && (
                      <span className="truncate">{item.label}</span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Area of Sidebar */}
      <div className="pt-4 border-t border-slate-200 dark:border-slate-800/80 space-y-3">
        {(!collapsed || isMobileDrawer) && (
          <div className="rounded-xl border border-emerald-200/60 dark:border-emerald-900/40 bg-emerald-50/60 dark:bg-emerald-950/30 p-3 text-xs">
            <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-300 font-semibold">
              <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
              <span>Design System v2</span>
            </div>
            <p className="mt-1 text-[11px] text-emerald-700/80 dark:text-emerald-400/80 leading-relaxed">
              Standardized tokens, accessible controls, and theme engine active.
            </p>
          </div>
        )}

        {/* Collapse / Expand Toggle Button on Desktop */}
        {!isMobileDrawer && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={cn(
              'w-full min-h-[44px] flex items-center rounded-lg py-2 text-xs font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer',
              collapsed ? 'justify-center px-0' : 'justify-between px-3'
            )}
          >
            {!collapsed && <span>Collapse Sidebar</span>}
            {collapsed ? (
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            ) : (
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
            )}
          </button>
        )}
      </div>
    </aside>
  );
}
