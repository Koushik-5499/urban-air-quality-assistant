import { useState } from 'react';
import { Check, Sparkles, Volume2, Moon, Sliders } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { saveNotificationPreferences } from '../../services/alertService';
import type { NotificationPreferences as PrefsType } from '../../types/alerts';

export interface NotificationPreferencesProps {
  preferences: PrefsType;
  onPreferencesChange: (newPrefs: PrefsType) => void;
}

export function NotificationPreferences({
  preferences,
  onPreferencesChange,
}: NotificationPreferencesProps) {
  const [prefs, setPrefs] = useState<PrefsType>(preferences);
  const [showSavedFeedback, setShowSavedFeedback] = useState(false);

  const handleToggle = (key: keyof PrefsType) => {
    setPrefs((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleFrequencyChange = (frequency: PrefsType['frequency']) => {
    setPrefs((prev) => ({
      ...prev,
      frequency,
    }));
  };

  const handleSave = () => {
    saveNotificationPreferences(prefs);
    onPreferencesChange(prefs);
    setShowSavedFeedback(true);
    setTimeout(() => setShowSavedFeedback(false), 2500);
  };

  return (
    <Card variant="standard" className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Sliders className="w-4 h-4" />
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Notification & Warning Preferences
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure simulated alert triggers, dispatch thresholds, and frequency settings.
          </p>
        </div>

        {/* Master Toggle */}
        <label className="flex items-center gap-2.5 cursor-pointer self-start sm:self-auto">
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            {prefs.notificationsEnabled ? 'Alerts Active' : 'Alerts Disabled'}
          </span>
          <input
            type="checkbox"
            checked={prefs.notificationsEnabled}
            onChange={() => handleToggle('notificationsEnabled')}
            className="sr-only peer"
          />
          <div className="w-10 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600 relative" />
        </label>
      </div>

      {/* Public Platform Notice */}
      <div className="p-3.5 rounded-xl bg-teal-50/80 dark:bg-teal-950/40 border border-teal-200/80 dark:border-teal-800/60 flex items-start gap-3">
        <div className="p-2 rounded-lg bg-teal-100 text-teal-800 dark:bg-teal-900/60 dark:text-teal-300 shrink-0">
          <Sliders className="w-4 h-4" />
        </div>
        <div className="space-y-0.5">
          <h4 className="text-xs font-bold text-teal-900 dark:text-teal-200">
            Public Environmental Monitoring Network
          </h4>
          <p className="text-xs text-teal-800/90 dark:text-teal-300/90 leading-relaxed">
            User accounts, personal logins, and server-side notification subscriptions have been retired. All ambient threshold alerts are broadcast publicly on the Alert Feed across monitored cities without requiring an account.
          </p>
        </div>
      </div>

      {/* Threshold Options */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Severity Trigger Thresholds
        </h4>

        <div className="space-y-2">
          {/* Critical AQI */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-white block">
                Critical AQI Warnings (AQI &gt; 150)
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Immediate dispatch when cities cross into Unhealthy, Very Unhealthy, or Hazardous.
              </span>
            </div>
            <input
              type="checkbox"
              checked={prefs.criticalAlerts}
              onChange={() => handleToggle('criticalAlerts')}
              disabled={!prefs.notificationsEnabled}
              className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-40"
            />
          </div>

          {/* Sensitive / Unhealthy */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-white block">
                Sensitive Group Advisories (AQI 101–150)
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Notify when ozone or fine particulates reach levels impacting children and asthmatics.
              </span>
            </div>
            <input
              type="checkbox"
              checked={prefs.unhealthyAlerts}
              onChange={() => handleToggle('unhealthyAlerts')}
              disabled={!prefs.notificationsEnabled}
              className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-40"
            />
          </div>

          {/* Moderate Air Quality */}
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-white block">
                Moderate Air Updates (AQI 51–100)
              </span>
              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Informational updates when acceptable air experiences localized particulate shifts.
              </span>
            </div>
            <input
              type="checkbox"
              checked={prefs.moderateAlerts}
              onChange={() => handleToggle('moderateAlerts')}
              disabled={!prefs.notificationsEnabled}
              className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-40"
            />
          </div>
        </div>
      </div>

      {/* Frequency & Audio Preferences */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Frequency */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-2">
          <span className="text-xs font-bold text-slate-900 dark:text-white block">
            Preferred Alert Cadence
          </span>
          <div className="space-y-1.5 text-xs">
            {(['immediate', 'daily', 'weekly'] as const).map((freq) => (
              <label
                key={freq}
                className="flex items-center gap-2 cursor-pointer text-slate-700 dark:text-slate-300"
              >
                <input
                  type="radio"
                  name="alert-frequency"
                  checked={prefs.frequency === freq}
                  onChange={() => handleFrequencyChange(freq)}
                  disabled={!prefs.notificationsEnabled}
                  className="text-emerald-600 focus:ring-emerald-500 disabled:opacity-40"
                />
                <span className="capitalize font-medium">
                  {freq === 'immediate'
                    ? 'Immediate (As Events Occur)'
                    : freq === 'daily'
                    ? 'Daily Summary Digest'
                    : 'Weekly Environmental Briefing'}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Quiet Hours & Sound */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-3">
          <span className="text-xs font-bold text-slate-900 dark:text-white block">
            Sound & Quiet Period
          </span>

          <label className="flex items-center justify-between text-xs cursor-pointer">
            <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
              <Volume2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Simulated Audio Chime</span>
            </span>
            <input
              type="checkbox"
              checked={prefs.soundEnabled}
              onChange={() => handleToggle('soundEnabled')}
              disabled={!prefs.notificationsEnabled}
              className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-40"
            />
          </label>

          <label className="flex items-center justify-between text-xs cursor-pointer">
            <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
              <Moon className="w-3.5 h-3.5 text-slate-400" />
              <span>Quiet Night Hours (22:00–07:00)</span>
            </span>
            <input
              type="checkbox"
              checked={prefs.quietHours}
              onChange={() => handleToggle('quietHours')}
              disabled={!prefs.notificationsEnabled}
              className="h-4 w-4 rounded text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-40"
            />
          </label>
        </div>
      </div>

      {/* Simulated Notice & Save Button */}
      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800">
        <p className="text-[11px] text-slate-400 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-teal-600 shrink-0" />
          <span>Public mode: No user accounts, personal logins, or remote tracking required.</span>
        </p>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          {showSavedFeedback && (
            <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1 animate-in fade-in">
              <Check className="w-3.5 h-3.5" /> Saved!
            </span>
          )}

          <Button variant="primary" size="sm" onClick={handleSave} className="text-xs">
            Save Preferences
          </Button>
        </div>
      </div>
    </Card>
  );
}
