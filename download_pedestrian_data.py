#!/usr/bin/env python3
"""
Quick script to download pedestrian demand data from NYC Open Data.

Usage:
    python download_pedestrian_data.py

The data will be saved to spatial_analysis/data/raw/pedestrian_demand.geojson
"""

import requests
from pathlib import Path

# Direct download endpoint for pedestrian demand data
URL = "https://data.cityofnewyork.us/api/views/fwpa-qxaf/rows.geojson?accessType=DOWNLOAD"

OUTPUT_DIR = Path(__file__).parent / "spatial_analysis" / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "pedestrian_demand.geojson"

def main():
    print("Downloading Pedestrian Demand data from NYC Open Data...")
    print(f"URL: {URL}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.get(URL, timeout=120)
    response.raise_for_status()

    with open(OUTPUT_FILE, "w") as f:
        f.write(response.text)

    print(f"[OK] Saved to: {OUTPUT_FILE}")

    # Quick stats
    import json
    data = json.loads(response.text)
    if "features" in data:
        print(f"[OK] Downloaded {len(data['features'])} features")

if __name__ == "__main__":
    main()
