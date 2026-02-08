// LTN Boundary: Houston St (north) – Bowery (east) – Canal St (south) – Broadway (west)
// Polygon traces the four street centerlines forming a quadrilateral.
// Coordinates are [lng, lat] (GeoJSON order).

const ltnBoundary: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    // ── Boundary polygon ──────────────────────────────────────────────
    {
      type: "Feature",
      properties: {
        name: "Proposed LTN Boundary",
        description:
          "Proposed Low Traffic Neighborhood: Canal Street to Houston Street Corridor",
        type: "boundary",
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            // NW corner: Houston & Broadway → east along Houston
            [-73.9967, 40.7254],
            [-73.9960, 40.7255],
            [-73.9956, 40.7256],
            [-73.9949, 40.7256],
            [-73.9940, 40.7257],
            [-73.9933, 40.7258],
            // NE corner: Houston & Bowery → south along Bowery
            [-73.9927, 40.7258],
            [-73.9930, 40.7251],
            [-73.9934, 40.7244],
            [-73.9938, 40.7237],
            [-73.9943, 40.7229],
            [-73.9948, 40.7221],
            [-73.9952, 40.7213],
            [-73.9957, 40.7205],
            [-73.9962, 40.7197],
            [-73.9967, 40.7188],
            [-73.9972, 40.7179],
            [-73.9976, 40.7170],
            [-73.9980, 40.7163],
            // SE corner: Canal & Bowery → west along Canal
            [-73.9983, 40.7158],
            [-73.9984, 40.7162],
            [-73.9985, 40.7166],
            [-73.9986, 40.7170],
            [-73.9988, 40.7174],
            [-73.9990, 40.7178],
            [-73.9993, 40.7182],
            [-73.9997, 40.7186],
            [-74.0003, 40.7191],
            // SW corner: Canal & Broadway → north along Broadway
            [-74.0010, 40.7197],
            [-74.0004, 40.7199],
            [-73.9999, 40.7203],
            [-73.9994, 40.7208],
            [-73.9990, 40.7214],
            [-73.9986, 40.7221],
            [-73.9982, 40.7227],
            [-73.9978, 40.7234],
            [-73.9974, 40.7241],
            [-73.9970, 40.7248],
            // Close polygon back to NW
            [-73.9967, 40.7254],
          ],
        ],
      },
    },

    // ── Boundary roads ────────────────────────────────────────────────
    {
      type: "Feature",
      properties: {
        name: "Houston Street",
        label: "HOUSTON ST",
        type: "boundary_road",
        role: "Through traffic corridor — northern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-73.9967, 40.7254],
          [-73.9960, 40.7255],
          [-73.9956, 40.7256],
          [-73.9949, 40.7256],
          [-73.9940, 40.7257],
          [-73.9933, 40.7258],
          [-73.9927, 40.7258],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Bowery",
        label: "BOWERY",
        type: "boundary_road",
        role: "Through traffic corridor — eastern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-73.9927, 40.7258],
          [-73.9930, 40.7251],
          [-73.9934, 40.7244],
          [-73.9938, 40.7237],
          [-73.9943, 40.7229],
          [-73.9948, 40.7221],
          [-73.9952, 40.7213],
          [-73.9957, 40.7205],
          [-73.9962, 40.7197],
          [-73.9967, 40.7188],
          [-73.9972, 40.7179],
          [-73.9976, 40.7170],
          [-73.9980, 40.7163],
          [-73.9983, 40.7158],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Canal Street",
        label: "CANAL ST",
        type: "boundary_road",
        role: "Through traffic corridor — southern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-73.9983, 40.7158],
          [-73.9984, 40.7162],
          [-73.9985, 40.7166],
          [-73.9986, 40.7170],
          [-73.9988, 40.7174],
          [-73.9990, 40.7178],
          [-73.9993, 40.7182],
          [-73.9997, 40.7186],
          [-74.0003, 40.7191],
          [-74.0010, 40.7197],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Broadway",
        label: "BROADWAY",
        type: "boundary_road",
        role: "Through traffic corridor — western boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-74.0010, 40.7197],
          [-74.0004, 40.7199],
          [-73.9999, 40.7203],
          [-73.9994, 40.7208],
          [-73.9990, 40.7214],
          [-73.9986, 40.7221],
          [-73.9982, 40.7227],
          [-73.9978, 40.7234],
          [-73.9974, 40.7241],
          [-73.9970, 40.7248],
          [-73.9967, 40.7254],
        ],
      },
    },

    // ── Modal filters ─────────────────────────────────────────────────
    // Placed at intersections where interior streets meet boundary roads
    {
      type: "Feature",
      properties: {
        name: "Crosby St & Houston St",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the north via Crosby Street",
      },
      geometry: { type: "Point", coordinates: [-73.9956, 40.7256] },
    },
    {
      type: "Feature",
      properties: {
        name: "Lafayette St & Houston St",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the north via Lafayette Street",
      },
      geometry: { type: "Point", coordinates: [-73.9940, 40.7257] },
    },
    {
      type: "Feature",
      properties: {
        name: "Spring St & Broadway",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the west via Spring Street",
      },
      geometry: { type: "Point", coordinates: [-73.9982, 40.7227] },
    },
    {
      type: "Feature",
      properties: {
        name: "Broome St & Broadway",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the west via Broome Street",
      },
      geometry: { type: "Point", coordinates: [-73.9990, 40.7214] },
    },
    {
      type: "Feature",
      properties: {
        name: "Grand St & Broadway",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the west via Grand Street",
      },
      geometry: { type: "Point", coordinates: [-73.9999, 40.7203] },
    },
    {
      type: "Feature",
      properties: {
        name: "Spring St & Bowery",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the east via Spring Street",
      },
      geometry: { type: "Point", coordinates: [-73.9943, 40.7229] },
    },
    {
      type: "Feature",
      properties: {
        name: "Broome St & Bowery",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the east via Broome Street",
      },
      geometry: { type: "Point", coordinates: [-73.9952, 40.7213] },
    },
    {
      type: "Feature",
      properties: {
        name: "Mulberry St & Canal St",
        type: "modal_filter",
        description:
          "Proposed modal filter — blocks through traffic entering from the south via Mulberry Street",
      },
      geometry: { type: "Point", coordinates: [-73.9988, 40.7174] },
    },
  ],
};

export default ltnBoundary;
