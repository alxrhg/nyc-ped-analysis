// Hardcoded subway route paths through the Canal St–Houston St corridor.
// Approximate centerline traces extending slightly beyond the study area.
// Coordinates are [lat, lng] for Leaflet.

export interface SubwayRoute {
  id: string;
  label: string;
  color: string;
  weight: number;
  opacity: number;
  path: [number, number][];
}

const subwayLines: SubwayRoute[] = [
  {
    id: "1-2",
    label: "1/2",
    color: "#EE352E",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -74.0040],
      [40.72832, -74.00530],
      [40.72500, -74.00500],
      [40.72056, -74.00521],
      [40.716, -74.0060],
      [40.712, -74.0075],
    ],
  },
  {
    id: "a-c-e",
    label: "A/C/E",
    color: "#0039A6",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -74.0025],
      [40.72900, -74.00340],
      [40.72622, -74.00369],
      [40.72300, -74.00310],
      [40.72028, -74.00244],
      [40.716, -74.0015],
      [40.712, -74.0010],
    ],
  },
  {
    id: "6",
    label: "6",
    color: "#00933C",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -73.9960],
      [40.72900, -73.9962],
      [40.72534, -73.99633],
      [40.72233, -73.99671],
      [40.71863, -73.99735],
      [40.716, -73.9978],
      [40.712, -73.9985],
    ],
  },
  {
    id: "n-q-r-w",
    label: "N/Q/R/W",
    color: "#FCCC0A",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -73.9973],
      [40.72900, -73.9975],
      [40.72434, -73.99771],
      [40.72200, -73.99800],
      [40.71946, -73.99854],
      [40.716, -73.9993],
      [40.712, -74.0005],
    ],
  },
  {
    id: "j-z",
    label: "J/Z",
    color: "#996633",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -73.9910],
      [40.72800, -73.9920],
      [40.72400, -73.9930],
      [40.72028, -73.99369],
      [40.71817, -73.99993],
      [40.716, -74.0010],
      [40.712, -74.0025],
    ],
  },
  {
    id: "b-d-f-m",
    label: "B/D/F/M",
    color: "#FF6319",
    weight: 3,
    opacity: 0.7,
    path: [
      [40.733, -73.9950],
      [40.72900, -73.9955],
      [40.72534, -73.99633],
      [40.72200, -73.9968],
      [40.71900, -73.9975],
      [40.716, -73.9985],
      [40.712, -73.9995],
    ],
  },
];

export default subwayLines;
