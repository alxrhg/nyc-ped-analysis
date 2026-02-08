// Subway route paths through the Canal St–Houston St study corridor.
// Each route is traced along the street it runs under, using ~12-20
// coordinate points so the line hugs the street grid rather than
// cutting diagonally through blocks.
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
  // ── 1/2 — 7th Avenue South / Varick Street ──────────────────────
  // OUTSIDE the LTN boundary (west of Broadway)
  {
    id: "1-2",
    label: "1/2",
    color: "#EE352E",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7310, -74.0000], // north of Houston on 7th Ave S
      [40.7295, -74.0020],
      [40.7283, -74.0053], // Houston St station
      [40.7275, -74.0050],
      [40.7265, -74.0049],
      [40.7254, -74.0047],
      [40.7240, -74.0045],
      [40.7225, -74.0044],
      [40.7210, -74.0052], // approaching Canal
      [40.7206, -74.0052], // Canal St (1/2) station
      [40.7190, -74.0055],
      [40.7170, -74.0060], // south of Canal
    ],
  },

  // ── A/C/E — 8th Avenue → 6th Avenue / Varick ────────────────────
  // OUTSIDE the LTN boundary (west of Broadway)
  {
    id: "a-c-e",
    label: "A/C/E",
    color: "#0039A6",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7310, -74.0010], // north of Houston
      [40.7295, -74.0025],
      [40.7280, -74.0035],
      [40.7262, -74.0037], // Spring St (A/C/E) station
      [40.7248, -74.0035],
      [40.7235, -74.0032],
      [40.7220, -74.0029],
      [40.7203, -74.0024], // Canal St (A/C/E) station
      [40.7190, -74.0020],
      [40.7175, -74.0015],
      [40.7160, -74.0010], // south of Canal
    ],
  },

  // ── 6 — Lafayette Street ─────────────────────────────────────────
  // INSIDE the LTN boundary
  {
    id: "6",
    label: "6",
    color: "#00933C",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7280, -73.9925], // north of Houston on Lafayette
      [40.7259, -73.9931], // at Houston
      [40.7253, -73.9935],
      [40.7243, -73.9943], // at Prince
      [40.7240, -73.9945],
      [40.7230, -73.9953], // at Kenmare
      [40.7223, -73.9958], // Spring St (6) station
      [40.7218, -73.9960],
      [40.7210, -73.9964],
      [40.7200, -73.9968], // at Broome
      [40.7195, -73.9970],
      [40.7186, -73.9974], // Canal St (6) station
      [40.7180, -73.9976],
      [40.7170, -73.9980],
      [40.7155, -73.9985], // south of Canal
    ],
  },

  // ── N/Q/R/W — Broadway ───────────────────────────────────────────
  // Runs along the WESTERN boundary of the LTN
  {
    id: "n-q-r-w",
    label: "N/Q/R/W",
    color: "#FCCC0A",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7280, -73.9950], // north of Houston on Broadway
      [40.7260, -73.9960],
      [40.7254, -73.9967], // at Houston
      [40.7248, -73.9970],
      [40.7243, -73.9974], // Prince St (N/Q/R/W) station
      [40.7234, -73.9978],
      [40.7227, -73.9982], // at Spring
      [40.7221, -73.9986],
      [40.7214, -73.9990], // at Broome
      [40.7208, -73.9994],
      [40.7203, -73.9999], // at Grand
      [40.7199, -74.0004],
      [40.7195, -74.0010], // Canal St (N/Q/R/W) station
      [40.7185, -74.0015],
      [40.7170, -74.0025], // south of Canal
    ],
  },

  // ── J/Z — Centre Street → Bowery ─────────────────────────────────
  // Runs along the EASTERN boundary (Bowery) and south via Centre St
  {
    id: "j-z",
    label: "J/Z",
    color: "#996633",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7260, -73.9920], // north of Houston on Bowery
      [40.7250, -73.9925],
      [40.7240, -73.9930],
      [40.7230, -73.9935],
      [40.7220, -73.9940],
      [40.7203, -73.9937], // Bowery station
      [40.7195, -73.9950],
      [40.7188, -73.9960],
      [40.7182, -73.9980], // curving from Bowery to Centre St
      [40.7175, -73.9990],
      [40.7168, -73.9997], // Canal St (J/Z) station
      [40.7160, -74.0000],
      [40.7150, -74.0005], // south on Centre St
      [40.7140, -74.0010],
    ],
  },

  // ── B/D/F/M — 6th Avenue → Lafayette Street ─────────────────────
  // Shares Lafayette with 6 train, offset slightly east
  {
    id: "b-d-f-m",
    label: "B/D/F/M",
    color: "#FF6319",
    weight: 3,
    opacity: 0.6,
    path: [
      [40.7280, -73.9920], // north of Houston
      [40.7265, -73.9925],
      [40.7253, -73.9930], // Broadway-Lafayette station
      [40.7245, -73.9935],
      [40.7237, -73.9940],
      [40.7228, -73.9948],
      [40.7218, -73.9955],
      [40.7208, -73.9960],
      [40.7198, -73.9965],
      [40.7190, -73.9968],
      [40.7182, -73.9972], // approaching Canal
      [40.7170, -73.9977],
      [40.7155, -73.9982], // south of Canal
    ],
  },
];

export default subwayLines;
