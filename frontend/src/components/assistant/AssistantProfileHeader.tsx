import { Bot, Trash2, MapPin } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { CityDashboardData } from '../../types/dashboard';

export interface AssistantProfileHeaderProps {
  cityData: CityDashboardData;
  messageCount: number;
  onClearChat: () => void;
}

export function AssistantProfileHeader({
  cityData,
  messageCount,
  onClearChat,
}: AssistantProfileHeaderProps) {
  const { location, aqi, category } = cityData;

  const getAQIBadgeVariant = (cat: string) => {
    switch (cat) {
      case 'Good':
        return 'success';
      case 'Moderate':
        return 'warning';
      case 'Unhealthy for Sensitive Groups':
      case 'Unhealthy':
        return 'danger';
      default:
        return 'default';
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Medical Disclaimer */}
      <div
        role="note"
        aria-label="Medical disclaimer"
        className="px-3 py-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs text-amber-700 dark:text-amber-300 flex items-start gap-2"
      >
        <span className="shrink-0 font-bold" aria-hidden="true">⚠️</span>
        <span>
          <strong>Medical Disclaimer:</strong> AI health guidance is for environmental awareness
          only and is not a substitute for professional medical advice. Consult a qualified
          healthcare provider for medical decisions.
        </span>
      </div>
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      {/* Left: Assistant Identity */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center shadow-xs">
            <Bot className="w-5 h-5" />
          </div>
          {/* Online green indicator */}
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white dark:border-slate-900" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white leading-tight">
              AI Environmental Health Assistant
            </h2>
            <Badge variant="neutral" size="sm">
              Local Engine
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Ready • Telemetry-linked to active location</span>
          </p>
        </div>
      </div>

      {/* Right: Active City Pill & Clear Conversation */}
      <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="font-semibold text-slate-900 dark:text-white">{location.city}</span>
          <Badge variant={getAQIBadgeVariant(category)} size="sm">
            {aqi} AQI
          </Badge>
        </div>

        {messageCount > 1 && (
          <button
            type="button"
            onClick={onClearChat}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-transparent hover:border-rose-200 dark:hover:border-rose-900/40 transition-colors cursor-pointer"
            title="Clear chat history"
            aria-label="Clear chat history"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear Chat</span>
          </button>
        )}
      </div>
    </div>
    </div>
  );
}
