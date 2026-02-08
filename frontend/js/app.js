/**
 * Main application controller.
 *
 * Wires together the map, API client, and filters.
 * Pattern from trip: centralized app initialization with event-driven updates.
 */
(function () {
  'use strict';

  const mapMgr = MapManager.init();
  const filters = Filters.init();

  // --- Panel toggle ---
  document.getElementById('panel-toggle').addEventListener('click', () => {
    document.getElementById('panel').classList.toggle('collapsed');
  });

  // --- Data loading ---
  async function loadStations() {
    try {
      const stations = await API.getStations({ ...filters.getParams(), limit: 5000 });
      mapMgr.setStations(stations);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  }

  async function loadIncidents() {
    try {
      const params = { ...filters.getParams(), limit: 5000 };
      const incidents = await API.getIncidents(params);
      mapMgr.setIncidents(incidents);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    }
  }

  async function loadHeatmap() {
    try {
      const points = await API.getHeatmapData(filters.getParams());
      mapMgr.setHeatmap(points);
    } catch (err) {
      console.error('Failed to load heatmap:', err);
    }
  }

  async function loadSummary() {
    try {
      const stats = await API.getCountSummary(filters.getParams());
      const el = document.getElementById('summary-stats');
      if (!stats.total_readings) {
        el.innerHTML = '<p>No data loaded yet. Import data via the API to see statistics.</p>';
        return;
      }
      el.innerHTML = `
        <div class="stat-card">
          <div class="stat-value">${(stats.total_volume || 0).toLocaleString()}</div>
          <div class="stat-label">Total Pedestrian Volume</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.total_readings.toLocaleString()}</div>
          <div class="stat-label">Count Readings</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${stats.avg_volume || '—'}</div>
          <div class="stat-label">Avg Volume per Reading</div>
        </div>
      `;
    } catch (err) {
      document.getElementById('summary-stats').textContent = 'Could not load summary.';
    }
  }

  // --- Station detail panel ---
  document.addEventListener('station-selected', async (e) => {
    const station = e.detail;
    const section = document.getElementById('station-detail');
    document.getElementById('detail-name').textContent = station.name;

    try {
      const summary = await API.getCountSummary({ station_id: station.id });
      document.getElementById('detail-body').innerHTML = `
        <div class="stat-row"><span>Borough</span><span>${station.borough}</span></div>
        <div class="stat-row"><span>Source</span><span>${station.source}</span></div>
        <div class="stat-row"><span>Readings</span><span>${(summary.total_readings || 0).toLocaleString()}</span></div>
        <div class="stat-row"><span>Total Volume</span><span>${(summary.total_volume || 0).toLocaleString()}</span></div>
        <div class="stat-row"><span>Avg Volume</span><span>${summary.avg_volume || '—'}</span></div>
        <div class="stat-row"><span>Peak Volume</span><span>${(summary.max_volume || 0).toLocaleString()}</span></div>
      `;
    } catch {
      document.getElementById('detail-body').innerHTML = '<p>Could not load station details.</p>';
    }

    section.style.display = 'block';
  });

  // --- Event-driven refresh (pattern from trip: reactive updates) ---
  document.addEventListener('filters-changed', () => {
    loadStations();
    if (document.getElementById('layer-safety').checked) loadIncidents();
    if (document.getElementById('layer-heatmap').checked) loadHeatmap();
    loadSummary();
  });

  document.addEventListener('layer-toggled', (e) => {
    const { layer, visible } = e.detail;
    mapMgr.toggleLayer(layer, visible);
    // Load data on first enable
    if (visible) {
      if (layer === 'safety') loadIncidents();
      if (layer === 'heatmap') loadHeatmap();
    }
  });

  // --- Initial load ---
  loadStations();
  loadSummary();
})();
