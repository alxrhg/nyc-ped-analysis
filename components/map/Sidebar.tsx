"use client";

import type { LayerVisibility, CrashFilters, MapStats } from "./ThesisMap";

interface SidebarProps {
  layers: LayerVisibility;
  onToggleLayer: (layer: keyof LayerVisibility) => void;
  crashFilters: CrashFilters;
  onToggleCrashFilter: (filter: keyof CrashFilters) => void;
  stats: MapStats;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  loading: {
    traffic: boolean;
    pedestrian: boolean;
    crashes: boolean;
  };
}

function LayerToggle({
  label,
  checked,
  onChange,
  color,
  loading,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
  color: string;
  loading?: boolean;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer py-1 group">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="sr-only"
      />
      <span
        className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
          checked ? "border-transparent" : "border-[#3a3a3a]"
        }`}
        style={{ backgroundColor: checked ? color : "transparent" }}
      >
        {checked && (
          <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 6l3 3 5-5"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </span>
      <span className="text-sm text-[#ededed] group-hover:text-white transition-colors flex-1">
        {label}
      </span>
      {loading && (
        <span className="w-3 h-3 border-2 border-[#3a3a3a] border-t-[#9ca3af] rounded-full animate-spin" />
      )}
    </label>
  );
}

function StatItem({
  label,
  value,
  loading,
}: {
  label: string;
  value: string | number;
  loading?: boolean;
}) {
  return (
    <div className="flex justify-between items-center py-1">
      <span className="text-xs text-[#9ca3af]">{label}</span>
      {loading ? (
        <span className="w-3 h-3 border-2 border-[#3a3a3a] border-t-[#9ca3af] rounded-full animate-spin" />
      ) : (
        <span className="text-sm font-medium text-[#ededed]">
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
      )}
    </div>
  );
}

export default function Sidebar({
  layers,
  onToggleLayer,
  crashFilters,
  onToggleCrashFilter,
  stats,
  darkMode,
  onToggleDarkMode,
  loading,
}: SidebarProps) {
  return (
    <aside className="w-80 bg-[#141414] border-r border-[#2a2a2a] flex flex-col overflow-y-auto shrink-0">
      {/* Basemap toggle */}
      <div className="p-4 border-b border-[#2a2a2a]">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#9ca3af] mb-2">
          Basemap
        </h2>
        <div className="flex gap-1">
          <button
            onClick={darkMode ? onToggleDarkMode : undefined}
            className={`flex-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              !darkMode
                ? "bg-[#3b82f6] text-white"
                : "bg-[#2a2a2a] text-[#9ca3af] hover:text-white"
            }`}
          >
            Light {!darkMode && "\u2713"}
          </button>
          <button
            onClick={!darkMode ? onToggleDarkMode : undefined}
            className={`flex-1 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
              darkMode
                ? "bg-[#3b82f6] text-white"
                : "bg-[#2a2a2a] text-[#9ca3af] hover:text-white"
            }`}
          >
            Dark {darkMode && "\u2713"}
          </button>
        </div>
      </div>

      {/* Layers */}
      <div className="p-4 border-b border-[#2a2a2a]">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#9ca3af] mb-3">
          Map Layers
        </h2>

        <LayerToggle
          label="Traffic Volume"
          checked={layers.traffic}
          onChange={() => onToggleLayer("traffic")}
          color="#eab308"
          loading={loading.traffic}
        />
        <LayerToggle
          label="Pedestrian Counts"
          checked={layers.pedestrian}
          onChange={() => onToggleLayer("pedestrian")}
          color="#a78bfa"
          loading={loading.pedestrian}
        />
        <LayerToggle
          label="Motor Vehicle Crashes"
          checked={layers.crashes}
          onChange={() => onToggleLayer("crashes")}
          color="#ef4444"
          loading={loading.crashes}
        />
        <LayerToggle
          label="Subway Stations"
          checked={layers.transit}
          onChange={() => onToggleLayer("transit")}
          color="#3b82f6"
        />
        <LayerToggle
          label="Proposed LTN Boundary"
          checked={layers.ltn}
          onChange={() => onToggleLayer("ltn")}
          color="#60a5fa"
        />
      </div>

      {/* Crash filters */}
      {layers.crashes && (
        <div className="p-4 border-b border-[#2a2a2a]">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[#9ca3af] mb-3">
            Crash Filters
          </h2>
          <label className="flex items-center gap-2 cursor-pointer py-1 text-sm">
            <input
              type="checkbox"
              checked={crashFilters.pedestrian}
              onChange={() => onToggleCrashFilter("pedestrian")}
              className="accent-[#ef4444]"
            />
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: "#ef4444" }}
            />
            Pedestrian involved
          </label>
          <label className="flex items-center gap-2 cursor-pointer py-1 text-sm">
            <input
              type="checkbox"
              checked={crashFilters.cyclist}
              onChange={() => onToggleCrashFilter("cyclist")}
              className="accent-[#f97316]"
            />
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: "#f97316" }}
            />
            Cyclist involved
          </label>
          <label className="flex items-center gap-2 cursor-pointer py-1 text-sm">
            <input
              type="checkbox"
              checked={crashFilters.motorist}
              onChange={() => onToggleCrashFilter("motorist")}
              className="accent-[#aaaaaa]"
            />
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: "#aaaaaa" }}
            />
            Vehicle only
          </label>
        </div>
      )}

      {/* Legend */}
      <div className="p-4 border-b border-[#2a2a2a]">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#9ca3af] mb-3">
          Legend
        </h2>

        {layers.traffic && (
          <div className="mb-3">
            <div className="text-xs text-[#9ca3af] mb-1.5">
              Traffic Volume (ADT)
            </div>
            <div className="flex items-center gap-1">
              <div
                className="h-2 flex-1 rounded-sm"
                style={{
                  background:
                    "linear-gradient(to right, #22c55e, #eab308, #ef4444, #991b1b)",
                }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-[#9ca3af] mt-0.5">
              <span>&lt;5K</span>
              <span>15K</span>
              <span>30K+</span>
            </div>
          </div>
        )}

        {layers.pedestrian && (
          <div className="mb-3">
            <div className="text-xs text-[#9ca3af] mb-1.5">
              Pedestrian Volume
            </div>
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: "#a78bfa" }}
              />
              <span className="text-[10px] text-[#9ca3af]">
                Circle size = count
              </span>
            </div>
          </div>
        )}

        {layers.crashes && (
          <div className="mb-3">
            <div className="text-xs text-[#9ca3af] mb-1.5">
              Crash Density (heatmap)
            </div>
            <div className="flex items-center gap-1">
              <div
                className="h-2 flex-1 rounded-sm"
                style={{
                  background:
                    "linear-gradient(to right, #fee5d9, #fcae91, #fb6a4a, #de2d26, #a50f15, #67000d)",
                }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-[#9ca3af] mt-0.5">
              <span>Low</span>
              <span>High</span>
            </div>
            <div className="text-[9px] text-[#6b7280] mt-1">
              Zoom in to see individual incidents
            </div>
          </div>
        )}

        {layers.transit && (
          <div className="mb-3">
            <div className="text-xs text-[#9ca3af] mb-1.5">
              Transit Coverage
            </div>
            <div className="flex items-center gap-2 mb-1">
              <div className="flex gap-px">
                <span
                  className="inline-flex items-center justify-center rounded-full border-2 border-[#333] text-white font-bold"
                  style={{
                    width: 16,
                    height: 16,
                    fontSize: 9,
                    backgroundColor: "#EE352E",
                  }}
                >
                  1
                </span>
                <span
                  className="inline-flex items-center justify-center rounded-full border-2 border-[#333] text-white font-bold"
                  style={{
                    width: 16,
                    height: 16,
                    fontSize: 9,
                    backgroundColor: "#0039A6",
                  }}
                >
                  A
                </span>
              </div>
              <span className="text-[10px] text-[#9ca3af]">
                Subway station (MTA bullets)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-0.5 rounded" style={{ backgroundColor: "#FF6319" }} />
              <span className="text-[10px] text-[#9ca3af]">
                Subway route line
              </span>
            </div>
          </div>
        )}

        {layers.ltn && (
          <div className="mb-3">
            <div className="text-xs text-[#9ca3af] mb-1.5">
              Proposed LTN <span className="text-[#f59e0b]">(thesis proposal)</span>
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="w-4 h-0.5 border-t-2 border-dashed border-[#3b82f6]" />
                <span className="text-[10px] text-[#9ca3af]">
                  Boundary road
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rotate-45"
                  style={{ backgroundColor: "#f59e0b" }}
                />
                <span className="text-[10px] text-[#9ca3af]">
                  Modal filter
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Statistics */}
      <div className="p-4 flex-1">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#9ca3af] mb-3">
          Corridor Summary
        </h2>

        {/* Crash breakdown */}
        <div className="mb-2">
          <StatItem
            label="Total crash incidents (3 yr)"
            value={stats.crashCount}
            loading={loading.crashes}
          />
          {!loading.crashes && stats.crashCount > 0 && (
            <div className="ml-2 border-l-2 border-[#2a2a2a] pl-2 mt-0.5">
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[10px] text-[#9ca3af]">
                  Pedestrian involved
                </span>
                <span className="text-xs font-medium text-[#e85d75]">
                  {stats.crashPedestrian.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[10px] text-[#9ca3af]">
                  Cyclist involved
                </span>
                <span className="text-xs font-medium text-[#f0a030]">
                  {stats.crashCyclist.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center py-0.5">
                <span className="text-[10px] text-[#9ca3af]">
                  Vehicle only
                </span>
                <span className="text-xs font-medium text-[#aaaaaa]">
                  {stats.crashVehicle.toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Top hotspots */}
        {!loading.crashes &&
          stats.topHotspots &&
          stats.topHotspots.length > 0 && (
            <div className="mb-3">
              <div className="text-[10px] text-[#9ca3af] mb-1">
                Top hotspot intersections:
              </div>
              {stats.topHotspots.map((h, i) => (
                <div
                  key={i}
                  className="flex justify-between items-center py-0.5"
                >
                  <span className="text-[10px] text-[#ededed] truncate mr-2">
                    {i + 1}. {h.name}
                  </span>
                  <span className="text-[10px] font-medium text-[#ef4444] shrink-0">
                    {h.count}
                  </span>
                </div>
              ))}
            </div>
          )}

        <StatItem
          label="Pedestrian count locations"
          value={stats.pedestrianLocations}
          loading={loading.pedestrian}
        />
        <StatItem
          label="Traffic segments"
          value={stats.trafficSegments}
          loading={loading.traffic}
        />
        <StatItem
          label="Subway stations"
          value={stats.subwayStations}
        />

        <div className="mt-4 pt-4 border-t border-[#2a2a2a]">
          <p className="text-[10px] text-[#6b7280] leading-relaxed">
            All data sourced live from NYC Open Data SODA API. Crash data
            covers the last 3 years. Traffic and pedestrian counts reflect the
            most recent available survey periods. The Proposed LTN Boundary
            layer represents a thesis proposal, not existing or planned
            infrastructure.
          </p>
        </div>
      </div>
    </aside>
  );
}
