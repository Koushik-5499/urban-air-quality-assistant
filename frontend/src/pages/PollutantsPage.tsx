import { useState, useMemo } from 'react';
import {
  Activity,
  Layers,
  Info,
} from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { PollutantOverview } from '../components/pollutants/PollutantOverview';
import { PollutantFilter } from '../components/pollutants/PollutantFilter';
import { PollutantMetricCard } from '../components/pollutants/PollutantMetricCard';
import { PollutantTrendChart } from '../components/pollutants/PollutantTrendChart';
import { PollutantComparisonChart } from '../components/pollutants/PollutantComparisonChart';
import { PollutantDetailCard } from '../components/pollutants/PollutantDetailCard';
import { AQIContributionSection } from '../components/pollutants/AQIContributionSection';
import { DEMO_LOCATIONS } from '../data/dashboardData';
import { generatePollutantTrends, POLLUTANT_DETAILS } from '../../src/data/pollutantDetails';
import type { PollutantId, ChartTimeRange } from '../types/dashboard';
import type { PollutantCategoryType } from '../types/pollutants';

function Pollutants() {
  useDocumentTitle('Pollutant Analysis — Urban Air Quality Assistant');

  const { selectedCityData, setSelectedCityId } = useLocation();

  // State
  const [selectedPollutantId, setSelectedPollutantId] = useState<PollutantId>('pm25');
  const [comparisonPollutants, setComparisonPollutants] = useState<PollutantId[]>([
    'pm25',
    'pm10',
    'no2',
  ]);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<PollutantCategoryType>('all');
  const [activeView, setActiveView] = useState<'grid' | 'comparison'>('grid');
  const [timeRange, setTimeRange] = useState<ChartTimeRange>('24h');
  const [comparisonMode, setComparisonMode] = useState<'normalized' | 'individual'>('normalized');

  // Filtered pollutants list for the 6 cards
  const filteredPollutants = useMemo(() => {
    return selectedCityData.pollutants.filter((p) => {
      // Search matching name, formula, or full name
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.formula.toLowerCase().includes(q) ||
        p.fullName.toLowerCase().includes(q);

      if (!matchesSearch) return false;

      // Category filter
      if (categoryFilter === 'particulate') {
        return p.id === 'pm25' || p.id === 'pm10';
      }
      if (categoryFilter === 'gaseous') {
        return p.id === 'co' || p.id === 'no2' || p.id === 'so2' || p.id === 'o3';
      }

      return true;
    });
  }, [selectedCityData.pollutants, searchQuery, categoryFilter]);

  // Generate trend points for current city and time range
  const trendData = useMemo(() => {
    return generatePollutantTrends(selectedCityData, timeRange);
  }, [selectedCityData, timeRange]);

  // Selected pollutant metric object
  const activePollutant = useMemo(() => {
    return (
      selectedCityData.pollutants.find((p) => p.id === selectedPollutantId) ||
      selectedCityData.pollutants[0]
    );
  }, [selectedCityData.pollutants, selectedPollutantId]);

  // Handlers
  const handleToggleCompare = (id: PollutantId) => {
    setComparisonPollutants((prev) => {
      if (prev.includes(id)) {
        return prev.filter((p) => p !== id);
      }
      return [...prev, id];
    });
  };

  const handleClearComparison = () => {
    setComparisonPollutants([]);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setCategoryFilter('all');
  };

  const isFiltered = searchQuery.trim().length > 0 || categoryFilter !== 'all';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Activity className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Detailed Pollutant Analysis
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            In-depth chemical breakdown of atmospheric criteria pollutants. Explore concentrations, historical diurnal dispersion curves, epidemiological health thresholds, and cross-pollutant dynamics.
          </p>
        </div>
      </div>

      {/* 2. Pollutant Overview Card */}
      <PollutantOverview
        cityData={selectedCityData}
        allLocations={DEMO_LOCATIONS}
        onSelectCity={setSelectedCityId}
      />

      {/* 3. Filter & View Switcher Bar */}
      <PollutantFilter
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        category={categoryFilter}
        onCategoryChange={setCategoryFilter}
        activeView={activeView}
        onActiveViewChange={setActiveView}
        onClearFilters={handleClearFilters}
        isFiltered={isFiltered}
      />

      {/* 4. Main Body Content Based on Active View */}
      {activeView === 'grid' ? (
        <div className="space-y-6">
          {/* 6 Pollutant Metric Cards Grid */}
          <div>
            <div className="flex items-center justify-between mb-3 text-xs font-semibold text-slate-600 dark:text-slate-400">
              <span>Criteria Air Pollutants ({filteredPollutants.length} of 6 active)</span>
              <span>Click any card to inspect comprehensive trend & health dossier</span>
            </div>

            {filteredPollutants.length === 0 ? (
              <div className="p-8 text-center rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                  No criteria pollutants match "{searchQuery}"
                </p>
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="mt-2 text-xs text-emerald-600 hover:underline cursor-pointer"
                >
                  Clear search filter
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredPollutants.map((pollutant) => (
                  <PollutantMetricCard
                    key={pollutant.id}
                    pollutant={pollutant}
                    isSelected={pollutant.id === selectedPollutantId}
                    isCompared={comparisonPollutants.includes(pollutant.id)}
                    canCompare={true}
                    onSelect={(id) => setSelectedPollutantId(id)}
                    onToggleCompare={handleToggleCompare}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Detailed Section for Selected Pollutant */}
          <div className="space-y-6 pt-2">
            {/* Interactive Trend Chart for Active Pollutant */}
            <PollutantTrendChart
              pollutantId={selectedPollutantId}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
              trendData={trendData}
              locationCity={selectedCityData.location.city}
            />

            {/* Scientific Dossier & Health Impact Card */}
            <PollutantDetailCard pollutant={activePollutant} />
          </div>

          {/* AQI Sub-index Contribution Section */}
          <AQIContributionSection
            pollutants={selectedCityData.pollutants}
            overallAQI={selectedCityData.aqi}
            dominantPollutant={selectedCityData.dominantPollutant}
          />
        </div>
      ) : (
        /* Multi-Pollutant Comparison View */
        <div className="space-y-6">
          <PollutantComparisonChart
            selectedPollutants={comparisonPollutants}
            onTogglePollutant={handleToggleCompare}
            onClearComparison={handleClearComparison}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
            trendData={trendData}
            comparisonMode={comparisonMode}
            onComparisonModeChange={setComparisonMode}
          />

          {/* Comparison Matrix Summary Table */}
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-600" />
                <span>Selected Pollutant Regulatory & Telemetry Matrix</span>
              </h3>
              <span className="text-xs text-slate-400">
                {comparisonPollutants.length} pollutants compared
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 dark:bg-slate-850 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Pollutant</th>
                    <th className="py-2.5 px-3">Reading</th>
                    <th className="py-2.5 px-3">Unit</th>
                    <th className="py-2.5 px-3">WHO Guideline</th>
                    <th className="py-2.5 px-3">NAAQS Standard</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">% of Limit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {comparisonPollutants.map((id) => {
                    const metric = selectedCityData.pollutants.find((p) => p.id === id);
                    const details = POLLUTANT_DETAILS[id];
                    if (!metric || !details) return null;
                    const percentOfLimit = Math.round((metric.value / details.naaqsLimit) * 100);

                    return (
                      <tr key={id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/50">
                        <td className="py-3 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                          <span
                            className="w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: details.color }}
                          />
                          <span>{details.formula} ({details.name})</span>
                        </td>
                        <td className="py-3 px-3 font-bold font-mono">
                          {id === 'co' ? metric.value.toFixed(2) : metric.value.toFixed(1)}
                        </td>
                        <td className="py-3 px-3 text-slate-500 font-mono">{metric.unit}</td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-400">
                          {details.whoLimitText}
                        </td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-400">
                          {details.naaqsLimitText}
                        </td>
                        <td className="py-3 px-3">
                          <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                            {metric.status}
                          </span>
                        </td>
                        <td className="py-3 px-3 font-mono font-bold text-slate-800 dark:text-slate-200">
                          {percentOfLimit}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sub-index explanation in compare view as well */}
          <AQIContributionSection
            pollutants={selectedCityData.pollutants}
            overallAQI={selectedCityData.aqi}
            dominantPollutant={selectedCityData.dominantPollutant}
          />
        </div>
      )}

      {/* 5. Educational and Demonstration Dataset Disclaimer */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-start gap-3 text-xs text-slate-500 dark:text-slate-400">
        <Info className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <p>
          <strong>Scientific Methodology Notice:</strong> All atmospheric concentrations and diurnal dispersion variations presented above are simulated demonstration datasets generated for educational visualization of criteria air pollutants under the National Ambient Air Quality Standards (NAAQS) framework. Values do not represent real-time regulatory enforcement monitoring.
        </p>
      </div>
    </div>
  );
}

export { Pollutants, Pollutants as PollutantsPage };
export default Pollutants;
