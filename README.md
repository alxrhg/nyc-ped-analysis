# NYC Pedestrian Spatial Analysis

This repository contains lightweight utilities for exploring the NYC Open Data
**Motor Vehicle Collisions - Crashes** dataset with a focus on pedestrian
impacts. The code builds tabular summaries that can be consumed by downstream
notebooks or mapping tools without requiring heavy geo dependencies.

## Quick start

1. Download a CSV export from the [NYC Open Data collisions dataset](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95). Include at least the following columns:
   - `CRASH DATE`
   - `BOROUGH`
   - `LATITUDE`
   - `LONGITUDE`
   - `ON STREET NAME` (optional but recommended)
   - `NUMBER OF PEDESTRIANS INJURED`
   - `NUMBER OF PEDESTRIANS KILLED`
2. Install dependencies (Python 3.10+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

3. Run the CLI to produce a JSON summary:

   ```bash
   python -m nyc_ped_analysis.cli \
     --input path/to/collisions.csv \
     --output summary.json \
     --top-locations 15
   ```

   Omit `--output` to print the summary to stdout.

## What the summary includes

- Borough totals: collisions, pedestrian injuries, and fatalities.
- Top street locations by pedestrian injuries (configurable count).
- Monthly collision trends for quick charting.

Each summary entry is ready for GeoJSON or visualization tools. For spatial
analysis that requires precise geometry operations, pair these summaries with a
borough boundary dataset in a downstream notebook.

The input cleaning step standardizes numeric columns and normalizes borough and
street values, so results stay consistent even when exports contain mixed types
or missing strings. The ``--top-locations`` flag must be positive to generate a
ranking.

## Development notes

The code intentionally avoids dependencies heavier than pandas so it can run in
resource-constrained environments. Extend the helpers in `src/nyc_ped_analysis`
if you need borough shapefiles or geocoding hooks.
