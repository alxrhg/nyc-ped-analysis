/**
 * Controls panel component with category toggles, focus area buttons, and info
 */

import { DEMAND_STYLES, FOCUS_AREAS } from '../utils/demandStyles';
import type {
  CategoryVisibility,
  DemandCategory,
  FocusArea,
} from '../types/pedestrianDemand';

/**
 * Quantile-based category mapping for display
 */
const CATEGORY_DISPLAY: Array<{
  demandLevel: DemandCategory;
  label: string;
  description: string;
}> = [
  { demandLevel: 'Very High', label: 'Very High', description: 'Top 25% demand' },
  { demandLevel: 'High', label: 'High', description: '50-75th percentile' },
  { demandLevel: 'Medium', label: 'Medium', description: '25-50th percentile' },
  { demandLevel: 'Low', label: 'Low', description: 'Bottom 25%' },
];

interface ControlsPanelProps {
  categoryVisibility: CategoryVisibility;
  onCategoryToggle: (category: DemandCategory) => void;
  onFocusAreaSelect: (area: FocusArea) => void;
  featureCount: number;
  isLoading: boolean;
  className?: string;
}

/**
 * Sidebar control panel with:
 * - Category visibility toggles (checkboxes)
 * - Focus area quick-navigation buttons
 * - Contextual information about the map
 */
export function ControlsPanel({
  categoryVisibility,
  onCategoryToggle,
  onFocusAreaSelect,
  featureCount,
  isLoading,
  className = '',
}: ControlsPanelProps) {
  return (
    <aside
      className={`
        bg-white shadow-lg rounded-lg
        p-4 space-y-5
        font-sans
        ${className}
      `}
    >
      {/* Category Toggles Section */}
      <section>
        <h3 className="font-semibold text-gray-800 text-sm mb-3 uppercase tracking-wide">
          Demand Level
        </h3>
        <div className="space-y-2">
          {CATEGORY_DISPLAY.map(({ demandLevel, label, description }) => {
            const style = DEMAND_STYLES[demandLevel];
            const isChecked = categoryVisibility[demandLevel];

            return (
              <label
                key={demandLevel}
                className="flex items-center gap-3 cursor-pointer group"
              >
                {/* Custom styled checkbox */}
                <div className="relative flex-shrink-0">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => onCategoryToggle(demandLevel)}
                    className="sr-only peer"
                  />
                  <div
                    className={`
                      w-5 h-5 rounded border-2 transition-all
                      peer-focus:ring-2 peer-focus:ring-blue-300
                      ${isChecked
                        ? 'border-transparent'
                        : 'border-gray-300 bg-white'
                      }
                    `}
                    style={{
                      backgroundColor: isChecked ? style.color : undefined,
                    }}
                  >
                    {isChecked && (
                      <svg
                        className="w-full h-full text-white p-0.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={3}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    )}
                  </div>
                </div>

                {/* Label with demand level */}
                <div className="flex-1 min-w-0">
                  <span
                    className={`
                      text-sm font-medium transition-colors block
                      ${isChecked ? 'text-gray-800' : 'text-gray-400'}
                      group-hover:text-gray-900
                    `}
                  >
                    {label}
                  </span>
                  <span className="text-[10px] text-gray-400 block">
                    {description}
                  </span>
                </div>
              </label>
            );
          })}
        </div>

        {/* Feature count */}
        <p className="text-xs text-gray-400 mt-3">
          {isLoading ? (
            'Loading...'
          ) : (
            <>
              Showing <span className="font-medium text-gray-600">{featureCount.toLocaleString()}</span> street segments
            </>
          )}
        </p>
      </section>

      {/* Divider */}
      <hr className="border-gray-200" />

      {/* Focus Area Buttons Section */}
      <section>
        <h3 className="font-semibold text-gray-800 text-sm mb-3 uppercase tracking-wide">
          Focus Area
        </h3>
        <div className="space-y-2">
          {FOCUS_AREAS.map((area) => (
            <button
              key={area.name}
              onClick={() => onFocusAreaSelect(area)}
              className="
                w-full text-left px-3 py-2
                bg-gray-50 hover:bg-gray-100
                border border-gray-200 rounded-md
                text-sm text-gray-700 hover:text-gray-900
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-blue-300
              "
            >
              <span className="font-medium">{area.name}</span>
              {area.description && (
                <span className="block text-xs text-gray-500 mt-0.5">
                  {area.description}
                </span>
              )}
            </button>
          ))}
        </div>
      </section>

      {/* Divider */}
      <hr className="border-gray-200" />

      {/* About Section */}
      <section>
        <h3 className="font-semibold text-gray-800 text-sm mb-2 uppercase tracking-wide">
          About This Map
        </h3>
        <div className="text-xs text-gray-600 space-y-2 leading-relaxed">
          <p>
            This map visualizes <strong>pedestrian demand</strong> across NYC streets,
            based on the NYC DOT Pedestrian Mobility Plan dataset.
          </p>
          <p>
            Colors are distributed using <strong>quartile breaks</strong> for even distribution.
            <span style={{ color: '#d32f2f' }}> Red</span> shows the top 25% highest demand streets.
          </p>
          <p className="text-gray-500">
            Focus: Houston St to Canal St corridor in Chinatown/SoHo for pedestrianization research.
          </p>
        </div>
      </section>

      {/* Data Source */}
      <div className="pt-2 border-t border-gray-200">
        <p className="text-[10px] text-gray-400">
          Data:{' '}
          <a
            href="https://data.cityofnewyork.us/Transportation/Pedestrian-Mobility-Plan-Pedestrian-Demand/fwpa-qxaf"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-600 underline"
          >
            NYC Open Data
          </a>
        </p>
      </div>
    </aside>
  );
}

export default ControlsPanel;
