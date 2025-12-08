import unittest

import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

from nyc_ped_analysis.analysis import (
    COL_BOROUGH,
    COL_CRASH_DATE,
    COL_LAT,
    COL_LON,
    COL_PED_INJURED,
    COL_PED_KILLED,
    COL_STREET,
    build_summary,
    clean_collision_data,
    compute_top_locations,
    load_collision_data,
)


def _base_frame():
    return pd.DataFrame(
        {
            COL_CRASH_DATE: pd.to_datetime(
                ["2023-01-15", "2023-01-15", "2023-02-20", "2023-02-21"]
            ),
            COL_BOROUGH: ["Manhattan", "Manhattan", "Queens", None],
            COL_LAT: [40.7, "40.8", 40.75, None],
            COL_LON: [-73.9, "-73.95", -73.8, -73.85],
            COL_STREET: ["Broadway", "broadway", "Main St", ""],
            COL_PED_INJURED: [1, "2", 0, 1],
            COL_PED_KILLED: [0, "0", 1, 0],
        }
    )


class TestAnalysis(unittest.TestCase):
    def test_load_collision_data_missing_columns(self):
        missing = pd.DataFrame({COL_CRASH_DATE: ["2023-01-01"]})
        with TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "collisions.csv"
            missing.to_csv(csv_path, index=False)

            with self.assertRaises(ValueError):
                load_collision_data(csv_path)

    def test_clean_collision_data_normalizes_values(self):
        cleaned = clean_collision_data(_base_frame())

        self.assertEqual(
            cleaned[COL_BOROUGH].tolist(), ["MANHATTAN", "MANHATTAN", "QUEENS"]
        )
        self.assertEqual(
            cleaned[COL_STREET].tolist(), ["BROADWAY", "BROADWAY", "MAIN ST"]
        )
        self.assertEqual(cleaned[COL_PED_INJURED].sum(), 3)
        self.assertEqual(cleaned[COL_PED_KILLED].sum(), 1)
        self.assertIn(cleaned[COL_LAT].dtype.kind, {"f", "i"})
        self.assertIn(cleaned[COL_LON].dtype.kind, {"f", "i"})

    def test_compute_top_locations_rejects_non_positive_limit(self):
        cleaned = clean_collision_data(_base_frame())

        with self.assertRaises(ValueError):
            compute_top_locations(cleaned, limit=0)

    def test_build_summary_validates_limit(self):
        cleaned = clean_collision_data(_base_frame())

        with self.assertRaises(ValueError):
            build_summary(cleaned, top_location_limit=-1)

    def test_build_summary_outputs_serializable_dict(self):
        cleaned = clean_collision_data(_base_frame())
        summary = build_summary(cleaned, top_location_limit=2)

        self.assertEqual(set(summary.keys()), {"boroughs", "top_locations", "monthly_trend"})
        self.assertEqual(summary["top_locations"][0]["street"], "BROADWAY")


if __name__ == "__main__":
    unittest.main()
