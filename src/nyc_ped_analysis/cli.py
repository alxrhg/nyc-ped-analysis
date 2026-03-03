"""Command-line entry point for running pedestrian collision summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import (
    build_summary,
    clean_collision_data,
    load_collision_data,
)


class PositiveInt(argparse.Action):
    """Ensure CLI values are positive integers."""

    def __call__(self, parser, namespace, values, option_string=None):
        if values <= 0:
            raise argparse.ArgumentTypeError("value must be positive")
        setattr(namespace, self.dest, values)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize NYC pedestrian collision data with borough totals, top"
            " locations, and monthly trends."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the CSV export from NYC Open Data",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON summary. Prints to stdout when omitted.",
    )
    parser.add_argument(
        "--top-locations",
        type=int,
        action=PositiveInt,
        default=10,
        help="How many street locations to include in the rankings (default: 10)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    data = load_collision_data(args.input)
    cleaned = clean_collision_data(data)
    summary = build_summary(cleaned, top_location_limit=args.top_locations)

    serialized = json.dumps(summary, indent=2)
    if args.output:
        args.output.write_text(serialized)
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
