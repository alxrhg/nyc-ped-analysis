/**
 * Leaflet map management (pattern from trip's map.ts).
 *
 * Handles map initialization, marker layers, clustering, and heatmaps.
 * Uses category-colored markers and cluster groups like trip does.
 */
const MapManager = {
  map: null,
  stationLayer: null,
  incidentLayer: null,
  heatLayer: null,

  /** Initialize the Leaflet map centered on NYC. */
  init() {
    this.map = L.map('map', {
      center: [40.7128, -74.006],
      zoom: 12,
      zoomControl: true,
    });

    // OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(this.map);

    // Marker cluster groups (pattern from trip: clustered markers with disableClusteringAtZoom)
    this.stationLayer = L.markerClusterGroup({
      disableClusteringAtZoom: 15,
      maxClusterRadius: 50,
      spiderfyOnMaxZoom: true,
    });

    this.incidentLayer = L.markerClusterGroup({
      disableClusteringAtZoom: 17,
      maxClusterRadius: 40,
    });

    this.map.addLayer(this.stationLayer);

    return this;
  },

  /** Create a colored circle marker (pattern from trip: category-colored markers). */
  _circleMarker(lat, lng, className, radius = 7) {
    return L.circleMarker([lat, lng], {
      radius,
      className,
      fillOpacity: 0.85,
      weight: 2,
      color: 'white',
      fillColor: className === 'marker-station' ? '#2d6a4f' : '#d62828',
    });
  },

  /** Render count stations on the map. */
  setStations(stations) {
    this.stationLayer.clearLayers();
    stations.forEach(s => {
      const marker = this._circleMarker(s.latitude, s.longitude, 'marker-station');
      marker.bindPopup(`
        <strong>${s.name}</strong><br/>
        ${s.borough}<br/>
        ${s.street_name || ''}${s.cross_street ? ' & ' + s.cross_street : ''}
      `);
      marker.on('click', () => {
        document.dispatchEvent(new CustomEvent('station-selected', { detail: s }));
      });
      this.stationLayer.addLayer(marker);
    });
  },

  /** Render safety incidents on the map. */
  setIncidents(incidents) {
    this.incidentLayer.clearLayers();
    incidents.forEach(inc => {
      const severity = inc.pedestrians_killed > 0 ? 9 : 6;
      const marker = this._circleMarker(inc.latitude, inc.longitude, 'marker-incident', severity);
      marker.bindPopup(`
        <strong>${inc.borough}</strong><br/>
        ${new Date(inc.incident_date).toLocaleDateString()}<br/>
        Injured: ${inc.pedestrians_injured} | Killed: ${inc.pedestrians_killed}<br/>
        ${inc.contributing_factor || ''}
      `);
      this.incidentLayer.addLayer(marker);
    });
  },

  /** Render a heatmap layer from incident data. */
  setHeatmap(points) {
    if (this.heatLayer) {
      this.map.removeLayer(this.heatLayer);
    }
    const data = points.map(p => [p.lat, p.lng, p.intensity]);
    this.heatLayer = L.heatLayer(data, {
      radius: 20,
      blur: 15,
      maxZoom: 16,
      gradient: { 0.2: '#ffffb2', 0.4: '#fecc5c', 0.6: '#fd8d3c', 0.8: '#f03b20', 1.0: '#bd0026' },
    });
  },

  /** Toggle layer visibility. */
  toggleLayer(layerName, visible) {
    const layers = {
      stations: this.stationLayer,
      safety: this.incidentLayer,
      heatmap: this.heatLayer,
    };
    const layer = layers[layerName];
    if (!layer) return;
    if (visible) {
      this.map.addLayer(layer);
    } else {
      this.map.removeLayer(layer);
    }
  },
};
