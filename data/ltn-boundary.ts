const ltnBoundary: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
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
            [-74.0052, 40.7255],
            [-74.004, 40.721],
            [-74.0028, 40.719],
            [-74.001, 40.717],
            [-73.999, 40.7155],
            [-73.9975, 40.7145],
            [-73.996, 40.714],
            [-73.9945, 40.7138],
            [-73.9935, 40.714],
            [-73.9925, 40.7145],
            [-73.9918, 40.7155],
            [-73.992, 40.717],
            [-73.9925, 40.719],
            [-73.993, 40.721],
            [-73.9935, 40.723],
            [-73.994, 40.7248],
            [-73.995, 40.7258],
            [-73.997, 40.7262],
            [-73.999, 40.7264],
            [-74.001, 40.7264],
            [-74.003, 40.7262],
            [-74.0052, 40.7255],
          ],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Houston Street (Boundary Road)",
        type: "boundary_road",
        role: "Through traffic corridor \u2014 northern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-74.0052, 40.7255],
          [-74.003, 40.7262],
          [-74.001, 40.7264],
          [-73.999, 40.7264],
          [-73.997, 40.7262],
          [-73.995, 40.7258],
          [-73.994, 40.7248],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Canal Street (Boundary Road)",
        type: "boundary_road",
        role: "Through traffic corridor \u2014 southern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-74.0028, 40.719],
          [-74.001, 40.717],
          [-73.999, 40.7155],
          [-73.9975, 40.7145],
          [-73.996, 40.714],
          [-73.9945, 40.7138],
          [-73.9935, 40.714],
          [-73.9925, 40.7145],
          [-73.9918, 40.7155],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Varick Street / Avenue of the Americas (Boundary Road)",
        type: "boundary_road",
        role: "Through traffic corridor \u2014 western boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-74.0052, 40.7255],
          [-74.004, 40.721],
          [-74.0028, 40.719],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Bowery / Christie Street (Boundary Road)",
        type: "boundary_road",
        role: "Through traffic corridor \u2014 eastern boundary",
      },
      geometry: {
        type: "LineString",
        coordinates: [
          [-73.994, 40.7248],
          [-73.9935, 40.723],
          [-73.993, 40.721],
          [-73.9925, 40.719],
          [-73.992, 40.717],
          [-73.9918, 40.7155],
        ],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Broome & Centre",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.998, 40.7185],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Spring & Broadway",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.9978, 40.7223],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Prince & Mott",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.9948, 40.7236],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Grand & Mulberry",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.9967, 40.7186],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Kenmare & Lafayette",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.9962, 40.7225],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Broome & West Broadway",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-74.0013, 40.7215],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Grand & Wooster",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-74.0005, 40.7199],
      },
    },
    {
      type: "Feature",
      properties: {
        name: "Spring & Crosby",
        type: "modal_filter",
        description: "Proposed modal filter \u2014 blocks through motor traffic",
      },
      geometry: {
        type: "Point",
        coordinates: [-73.9963, 40.7218],
      },
    },
  ],
};

export default ltnBoundary;
