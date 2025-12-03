"""
Data Download Module for NYC Pedestrian Spatial Analysis

Downloads and caches data from NYC Open Data, Census API, and other sources.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd
import geopandas as gpd
import requests
import yaml

from src import RAW_DATA_DIR, DEFAULT_CRS, GEOGRAPHIC_CRS, PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NYCOpenDataDownloader:
    """Download data from NYC Open Data Portal."""

    # Socrata API endpoints for NYC Open Data
    DATASETS = {
        "crash_data": {
            "endpoint": "h9gi-nx95",
            "name": "Motor Vehicle Collisions - Crashes",
        },
        "subway_stations": {
            "endpoint": "arq3-7z49",
            "name": "Subway Stations",
        },
        "bus_stops": {
            "endpoint": "qafz-7myz",
            "name": "Bus Stop Shelters",
        },
        "bike_lanes": {
            "endpoint": "7vsa-caz7",
            "name": "NYC Bike Routes",
        },
        "nycha": {
            "endpoint": "evjd-dqpz",
            "name": "NYCHA Developments",
        },
        "community_districts": {
            "endpoint": "yfnk-k7r4",
            "name": "Community Districts",
        },
        "street_centerlines": {
            "endpoint": "exjm-f27b",
            "name": "NYC Street Centerline (CSCL)",
        },
        "pedestrian_counts": {
            "endpoint": "fwpa-qxaf",
            "name": "Pedestrian Mobility Plan - Pedestrian Demand",
        },
    }

    BASE_URL = "https://data.cityofnewyork.us/resource"

    def __init__(self, output_dir: Optional[Path] = None, app_token: Optional[str] = None):
        """
        Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded data. Defaults to RAW_DATA_DIR.
            app_token: Socrata app token for higher rate limits (optional).
        """
        self.output_dir = output_dir or RAW_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.app_token = app_token

    def _get_headers(self) -> dict:
        """Get request headers with optional app token."""
        headers = {"Accept": "application/json"}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        return headers

    def download_crash_data(
        self,
        start_date: str = "2019-01-01",
        end_date: str = "2024-12-31",
        pedestrian_only: bool = True,
        limit: int = 500000,
    ) -> gpd.GeoDataFrame:
        """
        Download motor vehicle collision data.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            pedestrian_only: If True, filter for pedestrian-involved crashes.
            limit: Maximum number of records to retrieve.

        Returns:
            GeoDataFrame with crash data.
        """
        logger.info(f"Downloading crash data from {start_date} to {end_date}...")

        endpoint = self.DATASETS["crash_data"]["endpoint"]
        url = f"{self.BASE_URL}/{endpoint}.json"

        # Build query
        where_clauses = [
            f"crash_date >= '{start_date}'",
            f"crash_date <= '{end_date}'",
            "latitude IS NOT NULL",
            "longitude IS NOT NULL",
        ]

        if pedestrian_only:
            where_clauses.append(
                "(number_of_pedestrians_injured > 0 OR number_of_pedestrians_killed > 0)"
            )

        params = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$order": "crash_date DESC",
        }

        response = requests.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        logger.info(f"Retrieved {len(data)} crash records")

        if not data:
            logger.warning("No crash data retrieved")
            return gpd.GeoDataFrame()

        df = pd.DataFrame(data)

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["longitude"].astype(float),
                df["latitude"].astype(float)
            ),
            crs=GEOGRAPHIC_CRS,
        )

        # Save to file
        output_path = self.output_dir / "crash_data.geojson"
        gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Saved crash data to {output_path}")

        return gdf

    def download_pedestrian_demand(
        self,
        limit: int = 100000,
    ) -> gpd.GeoDataFrame:
        """
        Download Pedestrian Mobility Plan - Pedestrian Demand data.

        This dataset contains pedestrian volume estimates for street segments
        across NYC, essential for LTN suitability analysis.

        Dataset: https://data.cityofnewyork.us/Transportation/Pedestrian-Mobility-Plan-Pedestrian-Demand/fwpa-qxaf
        API: https://data.cityofnewyork.us/api/v3/views/fwpa-qxaf/query.json

        Args:
            limit: Maximum number of records to retrieve.

        Returns:
            GeoDataFrame with pedestrian demand data.
        """
        logger.info("Downloading Pedestrian Mobility Plan - Pedestrian Demand data...")

        endpoint = self.DATASETS["pedestrian_counts"]["endpoint"]

        # Use the v3 API endpoint as specified
        v3_url = f"https://data.cityofnewyork.us/api/v3/views/{endpoint}/query.json"

        try:
            # Try v3 API first
            response = requests.get(
                v3_url,
                headers=self._get_headers(),
                params={"$limit": limit},
                timeout=120,
            )
            response.raise_for_status()

            result = response.json()

            # v3 API returns data in a different structure
            if isinstance(result, dict):
                if "data" in result:
                    data = result["data"]
                    columns = result.get("columns", [])
                    column_names = [col.get("name", f"col_{i}") for i, col in enumerate(columns)]
                    df = pd.DataFrame(data, columns=column_names)
                else:
                    df = pd.DataFrame([result] if result else [])
            else:
                df = pd.DataFrame(result)

            logger.info(f"Retrieved {len(df)} pedestrian demand records from v3 API")

        except Exception as e:
            logger.info(f"v3 API failed ({e}), trying standard Socrata endpoint...")

            # Fall back to standard Socrata GeoJSON endpoint
            geojson_url = f"{self.BASE_URL}/{endpoint}.geojson"
            try:
                response = requests.get(
                    geojson_url,
                    headers=self._get_headers(),
                    params={"$limit": limit},
                    timeout=120,
                )
                response.raise_for_status()
                gdf = gpd.read_file(response.text)
                logger.info(f"Retrieved {len(gdf)} records as GeoJSON")

                # Save and return
                output_path = self.output_dir / "pedestrian_demand.geojson"
                gdf.to_file(output_path, driver="GeoJSON")
                logger.info(f"Saved pedestrian demand data to {output_path}")
                return gdf

            except Exception as e2:
                logger.info(f"GeoJSON also failed ({e2}), trying JSON...")

                # Final fallback to JSON
                json_url = f"{self.BASE_URL}/{endpoint}.json"
                response = requests.get(
                    json_url,
                    headers=self._get_headers(),
                    params={"$limit": limit},
                    timeout=120,
                )
                response.raise_for_status()
                df = pd.DataFrame(response.json())
                logger.info(f"Retrieved {len(df)} records as JSON")

        if df.empty:
            logger.warning("No pedestrian demand data retrieved")
            return gpd.GeoDataFrame()

        logger.info(f"Pedestrian demand columns: {list(df.columns)}")

        # Check for coordinate columns and create geometry
        lat_cols = [c for c in df.columns if "lat" in c.lower()]
        lon_cols = [c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()]

        # Also check for 'the_geom' or geometry columns
        geom_cols = [c for c in df.columns if "geom" in c.lower() or c == "geometry"]

        if geom_cols:
            geom_col = geom_cols[0]
            logger.info(f"Found geometry column: {geom_col}")

            # Parse geometry from WKT or GeoJSON
            from shapely import wkt
            from shapely.geometry import shape
            import json

            def parse_geometry(val):
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return None
                if isinstance(val, str):
                    try:
                        return wkt.loads(val)
                    except Exception:
                        try:
                            return shape(json.loads(val))
                        except Exception:
                            return None
                elif isinstance(val, dict):
                    try:
                        return shape(val)
                    except Exception:
                        return None
                return None

            df["geometry"] = df[geom_col].apply(parse_geometry)
            gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=GEOGRAPHIC_CRS)

        elif lat_cols and lon_cols:
            lat_col = lat_cols[0]
            lon_col = lon_cols[0]
            logger.info(f"Using coordinates: {lat_col}, {lon_col}")

            df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
            df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

            # Filter out rows without valid coordinates
            valid_coords = df[lat_col].notna() & df[lon_col].notna()
            df = df[valid_coords].copy()

            gdf = gpd.GeoDataFrame(
                df,
                geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                crs=GEOGRAPHIC_CRS,
            )
        else:
            # No geometry available, save as regular DataFrame
            logger.warning(
                "No coordinate columns found in pedestrian demand data. "
                "Saving as CSV for manual geocoding."
            )
            output_path = self.output_dir / "pedestrian_demand.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved pedestrian demand data to {output_path}")

            # Return GeoDataFrame with data but no geometry
            gdf = gpd.GeoDataFrame(df)
            gdf["geometry"] = None
            return gdf

        # Identify pedestrian volume columns
        volume_cols = [
            c for c in gdf.columns
            if any(term in c.lower() for term in ["ped", "volume", "count", "demand", "flow"])
            and c.lower() not in ["geometry", "the_geom"]
        ]
        if volume_cols:
            logger.info(f"Identified pedestrian volume columns: {volume_cols}")

        # Save to file
        output_path = self.output_dir / "pedestrian_demand.geojson"
        gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Saved pedestrian demand data to {output_path}")

        return gdf

    def download_geojson_dataset(self, dataset_key: str) -> gpd.GeoDataFrame:
        """
        Download a GeoJSON dataset from NYC Open Data.

        Args:
            dataset_key: Key from DATASETS dictionary.

        Returns:
            GeoDataFrame with the dataset.
        """
        if dataset_key not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_key}")

        dataset = self.DATASETS[dataset_key]
        logger.info(f"Downloading {dataset['name']}...")

        endpoint = dataset["endpoint"]
        url = f"{self.BASE_URL}/{endpoint}.geojson"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        gdf = gpd.read_file(response.text)
        logger.info(f"Retrieved {len(gdf)} records for {dataset['name']}")

        # Save to file
        output_path = self.output_dir / f"{dataset_key}.geojson"
        gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Saved to {output_path}")

        return gdf

    def download_all_datasets(self) -> dict[str, gpd.GeoDataFrame]:
        """
        Download all configured datasets.

        Returns:
            Dictionary mapping dataset keys to GeoDataFrames.
        """
        results = {}

        # Download crash data with filtering
        try:
            results["crash_data"] = self.download_crash_data()
        except Exception as e:
            logger.error(f"Failed to download crash data: {e}")

        # Download pedestrian demand data (critical for LTN suitability)
        try:
            results["pedestrian_demand"] = self.download_pedestrian_demand()
        except Exception as e:
            logger.error(f"Failed to download pedestrian demand data: {e}")

        # Download GeoJSON datasets
        geojson_datasets = [
            "subway_stations",
            "bus_stops",
            "bike_lanes",
            "nycha",
            "community_districts",
        ]

        for key in geojson_datasets:
            try:
                results[key] = self.download_geojson_dataset(key)
            except Exception as e:
                logger.error(f"Failed to download {key}: {e}")

        return results


class CensusDataDownloader:
    """Download data from the US Census API."""

    BASE_URL = "https://api.census.gov/data"

    # NYC county FIPS codes
    NYC_COUNTIES = {
        "061": "Manhattan",
        "047": "Brooklyn",
        "081": "Queens",
        "005": "Bronx",
        "085": "Staten Island",
    }

    # ACS variables to download
    VARIABLES = {
        # Population
        "B01003_001E": "total_population",
        # Income
        "B19013_001E": "median_household_income",
        # Vehicle ownership
        "B08201_001E": "total_households",
        "B08201_002E": "no_vehicle_households",
        "B08201_003E": "one_vehicle_households",
        # Race/ethnicity
        "B03002_001E": "total_pop_race",
        "B03002_003E": "white_alone",
        "B03002_004E": "black_alone",
        "B03002_006E": "asian_alone",
        "B03002_012E": "hispanic_latino",
        # Commute mode
        "B08301_001E": "total_workers",
        "B08301_010E": "public_transit_commuters",
        "B08301_019E": "walked_to_work",
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        api_key: Optional[str] = None,
        year: int = 2022,
    ):
        """
        Initialize the Census downloader.

        Args:
            output_dir: Directory to save downloaded data.
            api_key: Census API key (optional but recommended).
            year: ACS 5-year survey year.
        """
        self.output_dir = output_dir or RAW_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key
        self.year = year

    def download_acs_data(self) -> pd.DataFrame:
        """
        Download ACS 5-year estimates for NYC census tracts.

        Returns:
            DataFrame with census variables by tract.
        """
        logger.info(f"Downloading ACS {self.year} 5-year estimates...")

        variables = list(self.VARIABLES.keys())
        variable_str = ",".join(variables)

        all_data = []

        for county_fips, county_name in self.NYC_COUNTIES.items():
            logger.info(f"Downloading data for {county_name}...")

            url = f"{self.BASE_URL}/{self.year}/acs/acs5"
            params = {
                "get": f"NAME,{variable_str}",
                "for": "tract:*",
                "in": f"state:36 county:{county_fips}",
            }

            if self.api_key:
                params["key"] = self.api_key

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            headers = data[0]
            rows = data[1:]

            df = pd.DataFrame(rows, columns=headers)
            df["county_name"] = county_name
            all_data.append(df)

        combined_df = pd.concat(all_data, ignore_index=True)

        # Create GEOID for joining with tract geometries
        combined_df["GEOID"] = (
            combined_df["state"] + combined_df["county"] + combined_df["tract"]
        )

        # Rename columns
        rename_map = {old: new for old, new in self.VARIABLES.items()}
        combined_df = combined_df.rename(columns=rename_map)

        # Convert numeric columns
        for col in self.VARIABLES.values():
            if col in combined_df.columns:
                combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce")

        # Calculate derived variables
        combined_df["pct_no_vehicle"] = (
            combined_df["no_vehicle_households"] / combined_df["total_households"] * 100
        ).fillna(0)

        combined_df["pct_nonwhite"] = (
            (combined_df["total_pop_race"] - combined_df["white_alone"])
            / combined_df["total_pop_race"]
            * 100
        ).fillna(0)

        combined_df["pct_transit_commute"] = (
            combined_df["public_transit_commuters"] / combined_df["total_workers"] * 100
        ).fillna(0)

        # Save to file
        output_path = self.output_dir / "census_acs_data.csv"
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Saved census data to {output_path}")

        return combined_df

    def download_tract_geometries(self) -> gpd.GeoDataFrame:
        """
        Download census tract geometries from Census TIGER/Line.

        Returns:
            GeoDataFrame with tract geometries.
        """
        logger.info("Downloading census tract geometries...")

        # Use Census TIGER/Line API for tract boundaries
        url = f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/8/query"

        all_tracts = []

        for county_fips in self.NYC_COUNTIES.keys():
            params = {
                "where": f"STATE='36' AND COUNTY='{county_fips}'",
                "outFields": "*",
                "f": "geojson",
                "outSR": "4326",
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            gdf = gpd.read_file(response.text)
            all_tracts.append(gdf)

        combined_gdf = pd.concat(all_tracts, ignore_index=True)
        combined_gdf = gpd.GeoDataFrame(combined_gdf, crs=GEOGRAPHIC_CRS)

        # Save to file
        output_path = self.output_dir / "census_tracts.geojson"
        combined_gdf.to_file(output_path, driver="GeoJSON")
        logger.info(f"Saved tract geometries to {output_path}")

        return combined_gdf


def load_config() -> dict:
    """Load the spatial analysis configuration file."""
    config_path = PROJECT_ROOT / "spatial-analysis-config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def download_all_data(
    nyc_app_token: Optional[str] = None,
    census_api_key: Optional[str] = None,
) -> dict:
    """
    Download all data sources.

    Args:
        nyc_app_token: NYC Open Data app token.
        census_api_key: Census API key.

    Returns:
        Dictionary with download results.
    """
    results = {}

    # Download NYC Open Data
    nyc_downloader = NYCOpenDataDownloader(app_token=nyc_app_token)
    results["nyc_open_data"] = nyc_downloader.download_all_datasets()

    # Download Census data
    census_downloader = CensusDataDownloader(api_key=census_api_key)
    results["census_data"] = census_downloader.download_acs_data()
    results["census_tracts"] = census_downloader.download_tract_geometries()

    # Log summary
    logger.info("=" * 50)
    logger.info("Download Summary")
    logger.info("=" * 50)
    logger.info(f"NYC datasets downloaded: {len(results['nyc_open_data'])}")
    logger.info(f"Census tracts: {len(results['census_tracts'])}")

    return results


if __name__ == "__main__":
    # Run data download
    download_all_data()
