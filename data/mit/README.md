# `data/mit/`

## Study area polygon (committed)

- **`study_area_bowery_houston_6th_canal.geojson`** — Quadrilateral from NYC **Street Centerline** (Open Data `inkn-q76z`): **Avenue of the Americas** (6th Ave, west), **Houston St** (W + E, north), **Bowery** (east), **Canal St** (south). Regenerate if DCP updates CSCL:

  `python scripts/build_study_area_polygon.py`

## Symlinks to your Downloads (optional)

- `NYCWalks_preprint.pdf` → `~/Downloads/Preprint.pdf`
- `models/*.pckl` → `~/Downloads/Model files/*.pckl`

Refresh after moving files:

```bash
ln -sf "$HOME/Downloads/Preprint.pdf" "$(git rev-parse --show-toplevel)/data/mit/NYCWalks_preprint.pdf"
for f in "$HOME/Downloads/Model files"/*.pckl; do
  ln -sf "$f" "$(git rev-parse --show-toplevel)/data/mit/models/$(basename "$f")"
done
```
