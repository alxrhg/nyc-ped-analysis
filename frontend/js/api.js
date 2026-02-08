/**
 * Centralized API client (pattern from trip's api.service.ts).
 * All backend communication goes through this module.
 */
const API = {
  _base: '/api',

  async _fetch(path, params = {}) {
    const url = new URL(this._base + path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') {
        url.searchParams.set(k, v);
      }
    });
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`API error ${resp.status}: ${path}`);
    return resp.json();
  },

  // Stations
  getStations(params = {}) {
    return this._fetch('/stations/', params);
  },

  getStation(id) {
    return this._fetch(`/stations/${id}`);
  },

  // Counts
  getCounts(params = {}) {
    return this._fetch('/counts/', params);
  },

  getCountSummary(params = {}) {
    return this._fetch('/counts/summary', params);
  },

  // Safety
  getIncidents(params = {}) {
    return this._fetch('/safety/', params);
  },

  getHeatmapData(params = {}) {
    return this._fetch('/safety/heatmap', params);
  },

  // Health
  health() {
    return this._fetch('/health');
  },
};
