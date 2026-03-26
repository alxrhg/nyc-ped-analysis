# Thesis results export

Generated for **writing after results**: use this file as the single index of numbers and outputs.

## Headline counts (crashes strictly **inside** study polygon)

| Metric | Value |
|--------|------:|
| Date filter (≥) | 2019-01-01 |
| Crashes inside quadrilateral | **2,528** |
| Pedestrians injured (sum of records) | **224** |
| Pedestrians killed (sum of records) | **3** |
| Crashes with any ped injured or killed | **219** |

*Envelope download (before polygon filter): 5,764 rows.*

## Files in this run

| File | Description |
|------|-------------|
| `outputs/results/crashes_study_polygon.csv` | One row per crash inside polygon |
| `outputs/results/crash_summary_by_year.csv` | Crashes and ped harm by year |
| `outputs/results/key_metrics.json` | Machine-readable metrics |

## Maps (Manhattan tract percentiles + study outline)

- `outputs/maps/01_pedestrian_intensity_percentile.png`
- `outputs/maps/02_crash_intensity_percentile.png`
- `outputs/maps/03_residential_intensity_percentile.png`



## Tracts touching study area (from maps pipeline)

Source: `outputs/maps/study_area_tract_rankings.csv`

      geoid                         ntaname  ped_pctile  crash_pctile  res_pctile   ped_metric  crash_n   hu_per_km2
36061003700 SoHo-Little Italy-Hudson Square   98.387097     97.580645   10.967742 2.137214e+06      812  6354.224026
36061004100 SoHo-Little Italy-Hudson Square   96.451613     98.387097   56.129032 1.958443e+06      858 20057.380474
36061004900 SoHo-Little Italy-Hudson Square   91.935484     81.774194   30.000000 1.551030e+06      472 14786.253670
36061004700 SoHo-Little Italy-Hudson Square   82.903226     79.677419   18.064516 1.263581e+06      465 10385.772851
36061004300 SoHo-Little Italy-Hudson Square   80.967742     90.000000   51.935484 1.250291e+06      574 19341.163127
36061004500 SoHo-Little Italy-Hudson Square   73.548387     65.806452    9.354839 1.075325e+06      364  5917.878697
36061005502               Greenwich Village   69.354839     56.129032   19.677419 1.024983e+06      310 11092.822314
36061005501               Greenwich Village   39.354839     13.709677   47.419355 7.407774e+05      101 18423.742796
36061003601                 Lower East Side   28.064516     66.935484   35.806452 5.798928e+05      370 15942.538601
36061003602                    East Village   24.838710     35.645161   49.677419 5.412942e+05      198 18883.061088


## Suggested **factual** bullets for the paper (edit, don’t overclaim)

- Between **2019-01-01** and the latest crash dates in the export, police reported **2,528** motor vehicle crashes with coordinates inside the study quadrilateral (6th Ave – Houston – Bowery – Canal centerlines).
- **219** of those crashes involved at least one pedestrian injured or killed (per NYPD fields).
- Borough-level tract maps in `outputs/maps` situate walking intensity (NYCWalks), crash concentration, and housing-unit density with the same study outline.

## Next step for the thesis draft

Paste tables into your Methods / Results, cite NYC Open Data (crashes, CSCL, census tracts, ACS) and MIT NYCWalks, then interpret **policy** in a separate Discussion section.
