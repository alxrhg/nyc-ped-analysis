/**
 * Legend component for the pedestrian demand map
 * Displays NYC DOT street categories with color coding
 */

import { DEMAND_STYLES } from '../utils/demandStyles';
import type { DemandCategory } from '../types/pedestrianDemand';

/**
 * NYC DOT category mapping for legend display
 */
const LEGEND_ITEMS: Array<{
  demandLevel: DemandCategory;
  label: string;
}> = [
  { demandLevel: 'Global', label: 'Global' },
  { demandLevel: 'Regional', label: 'Regional' },
  { demandLevel: 'Neighborhood', label: 'Neighborhood' },
  { demandLevel: 'Community', label: 'Community' },
  { demandLevel: 'Baseline', label: 'Baseline' },
];

interface LegendProps {
  className?: string;
}

/**
 * Floating legend component showing NYC DOT street categories
 */
export function Legend({ className = '' }: LegendProps) {
  return (
    <div
      className={`
        bg-white/95 backdrop-blur-sm
        rounded-lg shadow-lg
        p-3 min-w-[160px]
        font-sans text-sm
        ${className}
      `}
    >
      {/* Legend title */}
      <h4 className="font-semibold text-gray-800 mb-1 text-xs uppercase tracking-wide">
        Street Category
      </h4>
      <p className="text-[10px] text-gray-500 mb-3">NYC DOT Ped Mobility Plan</p>

      {/* Category swatches */}
      <div className="space-y-1.5">
        {LEGEND_ITEMS.map(({ demandLevel, label }) => {
          const style = DEMAND_STYLES[demandLevel];
          return (
            <div key={demandLevel} className="flex items-center gap-2">
              {/* Line swatch */}
              <div
                className="rounded-sm"
                style={{
                  backgroundColor: style.color,
                  width: '20px',
                  height: `${Math.max(style.weight * 2, 3)}px`,
                  opacity: style.opacity,
                }}
              />
              {/* Category label */}
              <span className="text-gray-700 text-xs">{label}</span>
            </div>
          );
        })}
      </div>

      {/* Source */}
      <div className="mt-3 pt-2 border-t border-gray-200">
        <p className="text-[9px] text-gray-400">
          Data: NYC Open Data
        </p>
      </div>
    </div>
  );
}

export default Legend;
