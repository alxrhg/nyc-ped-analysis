"use client";

import useSWR from "swr";
import {
  fetchTrafficVolumes,
  fetchPedestrianCounts,
  fetchCrashData,
  type TrafficVolumeRecord,
  type PedestrianCountRecord,
  type CrashRecord,
} from "./nyc-open-data";

const SWR_OPTIONS = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  dedupingInterval: 600_000, // 10 minutes
  errorRetryCount: 2,
};

export function useTrafficVolumes() {
  return useSWR<TrafficVolumeRecord[]>(
    "nyc-traffic-volumes",
    fetchTrafficVolumes,
    SWR_OPTIONS
  );
}

export function usePedestrianCounts() {
  return useSWR<PedestrianCountRecord[]>(
    "nyc-pedestrian-counts",
    fetchPedestrianCounts,
    SWR_OPTIONS
  );
}

export function useCrashData() {
  return useSWR<CrashRecord[]>(
    "nyc-crash-data",
    fetchCrashData,
    SWR_OPTIONS
  );
}
