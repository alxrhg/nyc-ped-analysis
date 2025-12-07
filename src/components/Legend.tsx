/**
 * Legend component for the pedestrian demand map
 * Displays color/weight scale for demand categories
 */

import { DEMAND_STYLES } from '../utils/demandStyles';
import type { DemandCategory } from '../types/pedestrianDemand';

/**
 * Order of categories for display (highest to lowest)
 */
const CATEGORY_ORDER: DemandCategory[] = ['Very High', 'High', 'Medium', 'Low'];

interface LegendProps {
  className?: string;
}

/**
 * Floating legend component showing demand category colors
 * Positioned in bottom-right of map viewport
 */
export function Legend({ className = '' }: LegendProps) {
  return (
    <div
      className={`
        bg-white/95 backdrop-blur-sm
        rounded-lg shadow-lg
        p-3 min-w-[180px]
        font-sans text-sm
        ${className}
      `}
    >
      {/* Legend title */}
      <h4 className="font-semibold text-gray-800 mb-2 text-xs uppercase tracking-wide">
        Pedestrian Demand
      </h4>
      <p className="text-[10px] text-gray-500 mb-3 -mt-1">NYC DOT</p>

      {/* Category swatches */}
      <div className="space-y-1.5">
        {CATEGORY_ORDER.map((category) => {
          const style = DEMAND_STYLES[category];
          return (
            <div key={category} className="flex items-center gap-2">
              {/* Line swatch with appropriate width */}
              <div
                className="rounded-sm"
                style={{
                  backgroundColor: style.color,
                  width: '24px',
                  height: `${Math.max(style.weight * 2, 4)}px`,
                  opacity: style.opacity,
                }}
              />
              {/* Category label */}
              <span className="text-gray-700 text-xs">{style.label}</span>
            </div>
          );
        })}
      </div>

      {/* Data source attribution */}
      <div className="mt-3 pt-2 border-t border-gray-200">
        <p className="text-[9px] text-gray-400 leading-tight">
          Source: NYC DOT
          <br />
          Pedestrian Mobility Plan
        </p>
      </div>
    </div>
  );
}

export default Legend;
