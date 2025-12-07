/**
 * NYC Pedestrian Demand Explorer
 * Main application component
 *
 * A React + TypeScript + Leaflet application for visualizing
 * NYC DOT Pedestrian Mobility Plan data to support Low Traffic
 * Neighborhood research in Lower Manhattan.
 */

import { useState, useCallback } from 'react';
import { MapView } from './components/MapView';
import { ControlsPanel } from './components/ControlsPanel';
import { usePedestrianDemandData } from './hooks/usePedestrianDemandData';
import { INITIAL_CATEGORY_VISIBILITY, FOCUS_AREAS } from './utils/demandStyles';
import type {
  CategoryVisibility,
  DemandCategory,
  FocusArea,
  PedestrianDemandFeature,
} from './types/pedestrianDemand';

/**
 * Main App component
 */
function App() {
  // Fetch pedestrian demand data from NYC Open Data
  const { data, loadingState, error, featureCount } = usePedestrianDemandData({
    limit: 50000, // Fetch all available data
  });

  // Category visibility state
  const [categoryVisibility, setCategoryVisibility] = useState<CategoryVisibility>(
    INITIAL_CATEGORY_VISIBILITY
  );

  // Current focus area for map navigation
  const [focusArea, setFocusArea] = useState<FocusArea | null>(
    FOCUS_AREAS.find((a) => a.name === 'Chinatown / SoHo') || null
  );

  // Selected feature for info panel (reserved for future use)
  const [, setSelectedFeature] = useState<PedestrianDemandFeature | null>(
    null
  );

  // Mobile sidebar toggle
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  /**
   * Toggle category visibility
   */
  const handleCategoryToggle = useCallback((category: DemandCategory) => {
    setCategoryVisibility((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  }, []);

  /**
   * Handle focus area selection
   */
  const handleFocusAreaSelect = useCallback((area: FocusArea) => {
    setFocusArea(area);
    // Close mobile sidebar after selection
    setIsSidebarOpen(false);
  }, []);

  /**
   * Handle feature click on map
   */
  const handleFeatureClick = useCallback((feature: PedestrianDemandFeature) => {
    setSelectedFeature(feature);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              NYC Pedestrian Demand Explorer
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Using NYC DOT Pedestrian Mobility Plan data for Low Traffic Neighborhood analysis
            </p>
          </div>

          {/* Mobile sidebar toggle */}
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
            aria-label="Toggle controls"
          >
            <svg
              className="w-6 h-6 text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={isSidebarOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'}
              />
            </svg>
          </button>
        </div>
      </header>

      {/* Main content area */}
      <main className="flex-1 flex overflow-hidden">
        {/* Map container */}
        <div className="flex-1 relative">
          {/* Loading overlay */}
          {loadingState === 'loading' && (
            <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-[1001] flex items-center justify-center">
              <div className="text-center">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-gray-600 font-medium">Loading pedestrian demand data...</p>
                <p className="text-gray-400 text-sm mt-1">Fetching from NYC Open Data</p>
              </div>
            </div>
          )}

          {/* Error overlay */}
          {loadingState === 'error' && error && (
            <div className="absolute inset-0 bg-white/90 z-[1001] flex items-center justify-center">
              <div className="text-center max-w-md px-4">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-red-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold text-gray-800 mb-2">
                  Failed to Load Data
                </h2>
                <p className="text-gray-600 mb-4">{error.message}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Map */}
          <MapView
            data={data}
            categoryVisibility={categoryVisibility}
            focusArea={focusArea}
            onFeatureClick={handleFeatureClick}
            className="w-full h-full"
          />
        </div>

        {/* Sidebar - Controls Panel */}
        <div
          className={`
            absolute lg:relative top-0 right-0 h-full
            w-80 max-w-[90vw]
            transform transition-transform duration-300 ease-in-out
            lg:transform-none z-[1002]
            ${isSidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          `}
        >
          {/* Mobile backdrop */}
          {isSidebarOpen && (
            <div
              className="fixed inset-0 bg-black/30 lg:hidden -z-10"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}

          <div className="h-full overflow-y-auto bg-gray-50 lg:bg-transparent p-4">
            <ControlsPanel
              categoryVisibility={categoryVisibility}
              onCategoryToggle={handleCategoryToggle}
              onFocusAreaSelect={handleFocusAreaSelect}
              featureCount={featureCount}
              isLoading={loadingState === 'loading'}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 px-4 py-2 flex-shrink-0">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <p>
            Data: NYC DOT Pedestrian Mobility Plan •{' '}
            <a
              href="https://data.cityofnewyork.us/Transportation/Pedestrian-Mobility-Plan-Pedestrian-Demand/fwpa-qxaf"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              NYC Open Data
            </a>
          </p>
          <p>
            Built for Low Traffic Neighborhood research • The New School
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
