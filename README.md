# NYC Pedestrian-First Street Design: Spatial Analysis

A spatial analysis toolkit for identifying potential Low Traffic Neighborhood (LTN) locations in New York City, with a focus on pedestrian safety and equity.

**Author:** Alexander Huang
**Institution:** The New School - Urban Studies
**Project:** Pedestrian Way in New York City (Thesis)

## Research Questions

- **Central Question:** Why has NYC failed to implement pedestrian-first infrastructure despite favorable conditions?
- **Spatial Focus:**
  - Where in NYC are potential locations to deploy Low Traffic Neighborhoods?
  - How has congestion pricing changed the traffic landscape?
  - What problems do pedestrians in NYC face (spatially)?

## Features

- **Data Pipeline:** Automated download from NYC Open Data, Census API, and MTA sources
- **Crash Analysis:** Kernel density estimation and DBSCAN clustering for pedestrian crash hotspots
- **Suitability Analysis:** Weighted multi-criteria analysis for LTN site selection
- **Equity Analysis:** Demographic overlay to assess distributional implications
- **Visualization:** Static (matplotlib) and interactive (Folium) mapping

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/nyc-ped-analysis.git
cd nyc-ped-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Run complete analysis pipeline
python main.py --all

# Or run individual stages
python main.py --download       # Download data
python main.py --process        # Process raw data
python main.py --analyze all    # Run all analyses
python main.py --visualize      # Generate maps
```

## Project Structure

```
nyc-ped-analysis/
├── main.py                          # Main entry point
├── requirements.txt                 # Python dependencies
├── spatial-analysis-config.yaml     # Configuration file
├── src/
│   ├── __init__.py                 # Package initialization
│   ├── data_download.py            # NYC Open Data & Census API downloads
│   ├── data_processing.py          # Data cleaning and transformation
│   ├── crash_analysis.py           # Pedestrian crash clustering
│   ├── suitability_analysis.py     # LTN site suitability scoring
│   ├── equity_analysis.py          # Demographic equity assessment
│   └── visualization.py            # Map generation
├── spatial_analysis/
│   ├── data/
│   │   ├── raw/                    # Downloaded data
│   │   ├── processed/              # Cleaned data
│   │   └── external/               # External datasets
│   ├── analysis/
│   │   ├── crashes/                # Crash analysis outputs
│   │   ├── suitability/            # Suitability results
│   │   └── equity/                 # Equity analysis outputs
│   └── outputs/
│       ├── maps/                   # Generated maps
│       ├── figures/                # Charts and figures
│       └── tables/                 # CSV outputs
└── tests/                          # Unit tests
```

## Data Sources

### NYC Open Data
- **Motor Vehicle Collisions:** Pedestrian-involved crashes (2019-2024)
- **Pedestrian Demand:** DOT pedestrian volume estimates
- **Subway Stations:** MTA station locations
- **Bus Stops:** Bus stop shelter locations
- **NYCHA Developments:** Public housing locations
- **Community Districts:** Administrative boundaries

### Census / ACS
- Population demographics
- Median household income
- Vehicle ownership rates
- Commute mode (transit, walking)
- Race/ethnicity

## Study Areas

### Primary Sites
1. **Chinatown/SoHo** - Equity-critical case with high pedestrian volumes
2. **Financial District** - Extreme case with highest pedestrian volumes

### Context Area
- **Lower Manhattan** - Broader context for boundary effects analysis

## Analysis Modules

### 1. Crash Cluster Analysis
Identifies concentrations of pedestrian injuries/fatalities using:
- Kernel Density Estimation (bandwidth: 200 ft)
- DBSCAN clustering for hotspot detection
- Temporal pattern analysis (by year, time of day, etc.)

### 2. LTN Suitability Analysis
Weighted multi-criteria analysis with configurable weights:

| Criterion | Weight | Direction |
|-----------|--------|-----------|
| Pedestrian Volume | 20% | Higher is better |
| Transit Access | 15% | Closer is better |
| Low Vehicle Ownership | 15% | Higher is better |
| Crash Rate | 15% | Higher priority |
| Commercial Frontage | 10% | Higher is better |
| Residential Density | 10% | Higher is better |
| Street Width | 10% | Narrower is better |
| Cut-through Potential | 5% | Higher priority |

### 3. Equity Analysis
Assesses distributional implications:
- Demographic comparison (intervention areas vs citywide)
- NYCHA proximity analysis
- Combined suitability + equity scoring

## Configuration

Edit `spatial-analysis-config.yaml` to customize:
- Study area boundaries
- Analysis parameters
- Suitability criteria weights
- Output formats

## API Keys (Optional)

For better rate limits, set environment variables:
```bash
export NYC_OPENDATA_TOKEN="your-token"
export CENSUS_API_KEY="your-key"
```

## Outputs

### Maps
- Study area context map
- Crash hotspot heatmap
- LTN suitability choropleth
- Equity overlay map

### Data Exports
- `suitability_results.geojson` - Full results with scores
- `top_20_candidates.csv` - Highest scoring areas
- `equity_analysis_report.md` - Findings summary

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- NYC Open Data Portal
- U.S. Census Bureau
- Open Plans NYC (cut-through traffic research)
- The New School Urban Studies Program
