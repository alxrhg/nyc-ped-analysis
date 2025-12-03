#!/usr/bin/env python3
"""
NYC Pedestrian Analysis - Interactive Map Generator

Creates a base map of study areas first, then attempts to add data layers
from NYC Open Data APIs with graceful error handling.

Can also load data from local files if APIs are unavailable.

Usage:
    python create_map.py              # Try APIs first, fallback to local
    python create_map.py --local      # Use local files only
    python create_map.py --api        # Use APIs only

Author: Alexander Huang
"""

import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, List
import json

import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
import requests

# Paths
PROJECT_ROOT = Path(__file__).parent
RAW_DATA_DIR = PROJECT_ROOT / "spatial_analysis" / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "spatial_analysis" / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "spatial_analysis" / "outputs" / "maps"

# Study areas configuration
STUDY_AREAS = {
    "chinatown_soho": {
        "name": "Chinatown/SoHo",
        "center": (40.7205, -73.9975),
        "bounds": [[40.7130, -74.0050], [40.7280, -73.9900]],
        "color": "#e41a1c",
        "description": "Equity-critical case with high pedestrian volumes",
    },
    "financial_district": {
        "name": "Financial District",
        "center": (40.7065, -74.0100),
        "bounds": [[40.7000, -74.0200], [40.7130, -74.0000]],
        "color": "#377eb8",
        "description": "Extreme case - highest pedestrian volumes",
    },
    "lower_manhattan": {
        "name": "Lower Manhattan (Context)",
        "center": (40.7175, -73.9975),
        "bounds": [[40.6950, -74.0250], [40.7400, -73.9700]],
        "color": "#4daf4a",
        "description": "Broader context for boundary effects analysis",
    },
}

# NYC Open Data API endpoints
NYC_API_BASE = "https://data.cityofnewyork.us/resource"

DATA_SOURCES = {
    "subway_stations": {
        "endpoint": "arq3-7z49",
        "name": "Subway Stations",
        "format": "geojson",
        "color": "#0039A6",
        "icon": "subway",
    },
    "pedestrian_counts": {
        "endpoint": "2de2-6x2h",  # Bi-Annual Pedestrian Counts
        "name": "Bi-Annual Pedestrian Counts",
        "format": "json",
        "color": "#FF6B6B",
    },
    "pedestrian_demand_map": {
        "endpoint": "c4kr-96ik",
        "name": "Pedestrian Demand Map",
        "format": "geojson",
        "color": "#4ECDC4",
    },
    "crash_data": {
        "endpoint": "h9gi-nx95",
        "name": "Motor Vehicle Collisions",
        "format": "json",
        "color": "#FF0000",
        "filter": "number_of_pedestrians_injured>0 OR number_of_pedestrians_killed>0",
    },
    "nycha": {
        "endpoint": "evjd-dqpz",
        "name": "NYCHA Developments",
        "format": "geojson",
        "color": "#9B59B6",
    },
    "bike_lanes": {
        "endpoint": "7vsa-caz7",
        "name": "Bike Routes",
        "format": "geojson",
        "color": "#27AE60",
    },
}


@dataclass
class APIResult:
    """Result of an API fetch attempt."""
    success: bool
    endpoint: str
    name: str
    record_count: int = 0
    error_message: str = ""
    http_status: int = 0


def fetch_nyc_data(
    endpoint: str,
    name: str,
    data_format: str = "geojson",
    limit: int = 10000,
    bbox: Optional[List[List[float]]] = None,
    where_filter: Optional[str] = None,
) -> Tuple[Optional[dict], APIResult]:
    """
    Fetch data from NYC Open Data API.

    Args:
        endpoint: Dataset endpoint ID
        name: Human-readable name
        data_format: 'geojson' or 'json'
        limit: Max records to fetch
        bbox: Optional bounding box [[south, west], [north, east]]
        where_filter: Optional SoQL WHERE clause

    Returns:
        Tuple of (data dict or None, APIResult)
    """
    url = f"{NYC_API_BASE}/{endpoint}.{data_format}"

    params = {"$limit": limit}

    # Add bounding box filter if provided
    if bbox and data_format == "json":
        south, west = bbox[0]
        north, east = bbox[1]
        within_box = f"within_box(location, {north}, {west}, {south}, {east})"
        if where_filter:
            params["$where"] = f"({where_filter}) AND {within_box}"
        else:
            params["$where"] = within_box
    elif where_filter:
        params["$where"] = where_filter

    try:
        response = requests.get(url, params=params, timeout=30)

        result = APIResult(
            success=False,
            endpoint=endpoint,
            name=name,
            http_status=response.status_code,
        )

        if response.status_code == 200:
            data = response.json()

            # Count records
            if data_format == "geojson" and "features" in data:
                result.record_count = len(data["features"])
            elif isinstance(data, list):
                result.record_count = len(data)
            else:
                result.record_count = 1

            if result.record_count > 0:
                result.success = True
                return data, result
            else:
                result.error_message = "Empty response (0 records)"
                return None, result

        elif response.status_code == 404:
            result.error_message = f"Dataset not found (404) - endpoint may have changed"
        elif response.status_code == 403:
            result.error_message = f"Access forbidden (403) - may require API token"
        else:
            result.error_message = f"HTTP {response.status_code}: {response.text[:100]}"

        return None, result

    except requests.Timeout:
        return None, APIResult(
            success=False,
            endpoint=endpoint,
            name=name,
            error_message="Request timed out after 30 seconds",
        )
    except requests.RequestException as e:
        return None, APIResult(
            success=False,
            endpoint=endpoint,
            name=name,
            error_message=f"Network error: {str(e)[:100]}",
        )
    except json.JSONDecodeError as e:
        return None, APIResult(
            success=False,
            endpoint=endpoint,
            name=name,
            error_message=f"Invalid JSON response: {str(e)[:50]}",
        )


def create_base_map(
    center: Tuple[float, float] = (40.7128, -74.0060),
    zoom: int = 13,
) -> folium.Map:
    """Create the base map with study area boundaries."""

    print("\n" + "=" * 60)
    print("CREATING BASE MAP")
    print("=" * 60)

    # Create map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,  # We'll add tile layers manually
    )

    # Add multiple tile layer options
    folium.TileLayer(
        "cartodbpositron",
        name="Light (CartoDB)",
    ).add_to(m)

    folium.TileLayer(
        "cartodbdark_matter",
        name="Dark (CartoDB)",
    ).add_to(m)

    folium.TileLayer(
        "OpenStreetMap",
        name="OpenStreetMap",
    ).add_to(m)

    # Add study area boundaries
    study_areas_group = folium.FeatureGroup(name="Study Areas", show=True)

    for area_id, area in STUDY_AREAS.items():
        bounds = area["bounds"]

        # Create rectangle for study area
        folium.Rectangle(
            bounds=bounds,
            color=area["color"],
            weight=3,
            fill=True,
            fillColor=area["color"],
            fillOpacity=0.1,
            popup=folium.Popup(
                f"<b>{area['name']}</b><br>{area['description']}",
                max_width=300,
            ),
            tooltip=area["name"],
        ).add_to(study_areas_group)

        # Add label
        center = area["center"]
        folium.Marker(
            location=center,
            icon=folium.DivIcon(
                html=f'<div style="font-size: 10pt; color: {area["color"]}; font-weight: bold; text-shadow: 1px 1px white;">{area["name"]}</div>',
                icon_size=(150, 36),
                icon_anchor=(75, 18),
            ),
        ).add_to(study_areas_group)

    study_areas_group.add_to(m)

    # Add fullscreen button
    Fullscreen().add_to(m)

    print(f"[OK] Base map created with {len(STUDY_AREAS)} study areas")

    return m


def add_data_layers(m: folium.Map, bbox: Optional[List[List[float]]] = None) -> List[APIResult]:
    """
    Attempt to add data layers from NYC Open Data APIs.

    Returns list of API results for reporting.
    """
    print("\n" + "=" * 60)
    print("FETCHING DATA LAYERS FROM NYC OPEN DATA")
    print("=" * 60)

    results = []

    for source_id, source in DATA_SOURCES.items():
        print(f"\n[...] Fetching: {source['name']} ({source['endpoint']})...")

        data, result = fetch_nyc_data(
            endpoint=source["endpoint"],
            name=source["name"],
            data_format=source.get("format", "geojson"),
            limit=5000,
            bbox=bbox,
            where_filter=source.get("filter"),
        )

        results.append(result)

        if result.success:
            print(f"[OK] Retrieved {result.record_count} records")

            # Add layer to map
            try:
                layer_group = folium.FeatureGroup(name=source["name"], show=False)

                if source.get("format") == "geojson" and data:
                    # GeoJSON data
                    folium.GeoJson(
                        data,
                        style_function=lambda x, color=source["color"]: {
                            "color": color,
                            "weight": 2,
                            "fillOpacity": 0.3,
                        },
                        marker=folium.CircleMarker(
                            radius=6,
                            fill=True,
                            fillColor=source["color"],
                            color=source["color"],
                        ),
                    ).add_to(layer_group)

                elif data and isinstance(data, list):
                    # JSON with lat/lon
                    points_added = 0
                    for record in data[:1000]:  # Limit to 1000 points
                        lat = record.get("latitude") or record.get("lat")
                        lon = record.get("longitude") or record.get("lon") or record.get("lng")

                        if lat and lon:
                            try:
                                folium.CircleMarker(
                                    location=[float(lat), float(lon)],
                                    radius=4,
                                    color=source["color"],
                                    fill=True,
                                    fillOpacity=0.7,
                                ).add_to(layer_group)
                                points_added += 1
                            except (ValueError, TypeError):
                                continue

                    if points_added > 0:
                        print(f"     Added {points_added} points to map")
                    else:
                        print(f"     [!] No valid coordinates found in data")

                layer_group.add_to(m)

            except Exception as e:
                print(f"     [!] Error adding layer: {str(e)[:50]}")
        else:
            print(f"[FAIL] {result.error_message}")

    return results


def print_summary(results: List[APIResult]):
    """Print a summary of API fetch results."""

    print("\n" + "=" * 60)
    print("DATA LAYER SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    print(f"\nSuccessful: {success_count}/{len(results)}")
    print(f"Failed: {fail_count}/{len(results)}")

    if fail_count > 0:
        print("\n--- Failed Endpoints ---")
        for r in results:
            if not r.success:
                print(f"  {r.name}:")
                print(f"    Endpoint: {r.endpoint}")
                print(f"    Error: {r.error_message}")
                if r.http_status:
                    print(f"    HTTP Status: {r.http_status}")

    print("\n--- Successful Endpoints ---")
    for r in results:
        if r.success:
            print(f"  {r.name}: {r.record_count} records")


def load_local_files(m: folium.Map) -> List[APIResult]:
    """
    Try to load data from local GeoJSON/JSON files.

    Returns list of results for reporting.
    """
    print("\n" + "=" * 60)
    print("LOADING LOCAL DATA FILES")
    print("=" * 60)

    results = []

    # Map of local files to look for
    local_files = {
        "crash_data": {
            "paths": [
                PROCESSED_DATA_DIR / "crash_data_processed.geojson",
                RAW_DATA_DIR / "crash_data.geojson",
            ],
            "name": "Pedestrian Crashes",
            "color": "#FF0000",
        },
        "pedestrian_demand": {
            "paths": [
                PROCESSED_DATA_DIR / "pedestrian_demand_processed.geojson",
                RAW_DATA_DIR / "pedestrian_demand.geojson",
            ],
            "name": "Pedestrian Demand",
            "color": "#4ECDC4",
        },
        "subway_stations": {
            "paths": [
                PROCESSED_DATA_DIR / "subway_stations_processed.geojson",
                RAW_DATA_DIR / "subway_stations.geojson",
            ],
            "name": "Subway Stations",
            "color": "#0039A6",
        },
        "nycha": {
            "paths": [
                RAW_DATA_DIR / "nycha.geojson",
            ],
            "name": "NYCHA Developments",
            "color": "#9B59B6",
        },
    }

    for file_id, config in local_files.items():
        print(f"\n[...] Looking for: {config['name']}...")

        found_path = None
        for path in config["paths"]:
            if path.exists():
                found_path = path
                break

        if found_path:
            try:
                with open(found_path) as f:
                    data = json.load(f)

                record_count = len(data.get("features", [])) if "features" in data else len(data)

                print(f"[OK] Loaded {record_count} records from {found_path.name}")

                # Add to map
                layer_group = folium.FeatureGroup(name=config["name"], show=False)

                folium.GeoJson(
                    data,
                    style_function=lambda x, color=config["color"]: {
                        "color": color,
                        "weight": 2,
                        "fillOpacity": 0.3,
                    },
                    marker=folium.CircleMarker(
                        radius=5,
                        fill=True,
                        fillColor=config["color"],
                        color=config["color"],
                    ),
                ).add_to(layer_group)

                layer_group.add_to(m)

                results.append(APIResult(
                    success=True,
                    endpoint=str(found_path),
                    name=config["name"],
                    record_count=record_count,
                ))

            except Exception as e:
                print(f"[FAIL] Error loading {found_path}: {str(e)[:50]}")
                results.append(APIResult(
                    success=False,
                    endpoint=str(found_path),
                    name=config["name"],
                    error_message=str(e)[:100],
                ))
        else:
            searched = ", ".join(p.name for p in config["paths"])
            print(f"[SKIP] Not found (looked for: {searched})")
            results.append(APIResult(
                success=False,
                endpoint=file_id,
                name=config["name"],
                error_message=f"Local file not found",
            ))

    return results


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description="NYC Pedestrian Analysis - Map Generator"
    )
    parser.add_argument(
        "--local", action="store_true",
        help="Only load from local files (skip API calls)"
    )
    parser.add_argument(
        "--api", action="store_true",
        help="Only try API calls (skip local files)"
    )
    parser.add_argument(
        "--output", "-o", type=Path,
        default=None,
        help="Output path for HTML map"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("NYC PEDESTRIAN ANALYSIS - MAP GENERATOR")
    print("=" * 60)

    # Output path
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = args.output or OUTPUT_DIR / "nyc_pedestrian_map.html"

    # 1. Create base map first (always works)
    m = create_base_map(
        center=(40.7128, -74.0060),
        zoom=13,
    )

    all_results = []

    # 2a. Try local files first (unless --api only)
    if not args.api:
        local_results = load_local_files(m)
        all_results.extend(local_results)

    # 2b. Try API calls (unless --local only)
    if not args.local:
        lower_manhattan_bbox = STUDY_AREAS["lower_manhattan"]["bounds"]
        api_results = add_data_layers(m, bbox=lower_manhattan_bbox)
        all_results.extend(api_results)

    # 3. Add layer control
    folium.LayerControl(collapsed=False).add_to(m)

    # 4. Save map
    m.save(str(output_path))
    print(f"\n[SAVED] Map saved to: {output_path}")

    # 5. Print summary
    print_summary(all_results)

    # 6. Print helpful next steps
    success_count = sum(1 for r in all_results if r.success)

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    if success_count == 0:
        print("""
No data layers were loaded. To add data:

1. MANUAL DOWNLOAD: Visit NYC Open Data and download:
   - https://data.cityofnewyork.us/Transportation/Bi-Annual-Pedestrian-Counts/2de2-6x2h
   - https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95

   Save as GeoJSON to: spatial_analysis/data/raw/

2. Or run the data download script (requires network access):
   python main.py --download
""")
    else:
        print(f"\nLoaded {success_count} data layer(s) successfully!")

    print(f"\nOpen the map in a browser:\n  file://{output_path.absolute()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
