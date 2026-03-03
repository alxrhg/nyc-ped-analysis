# Code Review

The project now includes a small Python package for summarizing NYC pedestrian
collision data. When reviewing changes consider the following:

- Data validation: input CSVs should clearly validate required columns and parse
  dates consistently.
- Dependency footprint: keep dependencies light unless geo features require an
  additional library.
- Testability: favor pure functions in `src/nyc_ped_analysis` so summaries can be
  unit-tested with fixture data.
