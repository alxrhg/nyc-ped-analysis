"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import Sidebar from "@/components/map/Sidebar";
import type {
  LayerVisibility,
  CrashFilters,
  MapStats,
} from "@/components/map/ThesisMap";
import {
  useTrafficVolumes,
  usePedestrianCounts,
  useCrashData,
} from "@/lib/use-nyc-data";

// Dynamically import map to avoid SSR issues with mapbox-gl
const ThesisMap = dynamic(() => import("@/components/map/ThesisMap"), {
  ssr: false,
  loading: () => (
    <div className="flex-1 flex items-center justify-center bg-[#0a0a0a]">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-[#3a3a3a] border-t-[#3b82f6] rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm text-[#9ca3af]">Loading map...</p>
      </div>
    </div>
  ),
});

export default function ThesisMapPage() {
  const [layers, setLayers] = useState<LayerVisibility>({
    traffic: true,
    pedestrian: true,
    crashes: true,
    transit: true,
    ltn: true,
  });

  const [crashFilters, setCrashFilters] = useState<CrashFilters>({
    pedestrian: true,
    cyclist: true,
    motorist: true,
  });

  const [stats, setStats] = useState<MapStats>({
    crashCount: 0,
    pedestrianLocations: 0,
    totalPedVolume: 0,
    trafficSegments: 0,
    subwayStations: 0,
  });

  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Fetch data using SWR hooks
  const { data: trafficData, isLoading: trafficLoading } =
    useTrafficVolumes();
  const { data: pedestrianData, isLoading: pedestrianLoading } =
    usePedestrianCounts();
  const { data: crashData, isLoading: crashLoading } = useCrashData();

  const handleToggleLayer = useCallback((layer: keyof LayerVisibility) => {
    setLayers((prev) => ({ ...prev, [layer]: !prev[layer] }));
  }, []);

  const handleToggleCrashFilter = useCallback(
    (filter: keyof CrashFilters) => {
      setCrashFilters((prev) => ({ ...prev, [filter]: !prev[filter] }));
    },
    []
  );

  const handleStatsUpdate = useCallback(
    (updater: MapStats | ((prev: MapStats) => MapStats)) => {
      if (typeof updater === "function") {
        setStats(updater);
      } else {
        setStats(updater);
      }
    },
    []
  );

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-[#141414] border-b border-[#2a2a2a] px-4 py-3 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Mobile sidebar toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-1.5 rounded hover:bg-[#2a2a2a] text-[#9ca3af] hover:text-white transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={
                    sidebarOpen
                      ? "M6 18L18 6M6 6l12 12"
                      : "M4 6h16M4 12h16M4 18h16"
                  }
                />
              </svg>
            </button>
            <div>
              <h1 className="text-sm sm:text-base font-semibold text-[#ededed] leading-tight">
                Low Traffic Neighborhood Analysis: Canal Street to Houston
                Street Corridor
              </h1>
              <p className="text-[10px] sm:text-xs text-[#9ca3af]">
                Senior Thesis Research — Alexander Huang, The New School
              </p>
            </div>
          </div>

          {/* Loading indicators */}
          <div className="hidden sm:flex items-center gap-2">
            {(trafficLoading || pedestrianLoading || crashLoading) && (
              <div className="flex items-center gap-1.5 text-xs text-[#9ca3af]">
                <span className="w-2.5 h-2.5 border-2 border-[#3a3a3a] border-t-[#3b82f6] rounded-full animate-spin" />
                Loading data...
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Sidebar */}
        <div
          className={`${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          } lg:translate-x-0 absolute lg:relative z-10 h-full transition-transform duration-200`}
        >
          <Sidebar
            layers={layers}
            onToggleLayer={handleToggleLayer}
            crashFilters={crashFilters}
            onToggleCrashFilter={handleToggleCrashFilter}
            stats={stats}
            loading={{
              traffic: trafficLoading,
              pedestrian: pedestrianLoading,
              crashes: crashLoading,
            }}
          />
        </div>

        {/* Map */}
        <div className="flex-1 relative">
          <ThesisMap
            layers={layers}
            crashFilters={crashFilters}
            trafficData={trafficData}
            pedestrianData={pedestrianData}
            crashData={crashData}
            onStatsUpdate={handleStatsUpdate}
          />

          {/* Credit line */}
          <div className="absolute bottom-1 left-1 z-10 bg-[#0a0a0a]/80 backdrop-blur-sm px-2 py-0.5 rounded text-[9px] text-[#6b7280]">
            Data: NYC Open Data, NYC DOT, MTA | Visualization: Alexander Huang
          </div>
        </div>
      </div>
    </div>
  );
}
