# Data layout

Download assets from the MIT City Form Lab **NYCWalks** project page:

- [NYCWalks — City Form Lab](https://cityform.mit.edu/projects/nycwalks)

## Your MIT filenames (standard release)

| Local download | Put in repo |
|----------------|-------------|
| `NYC_pednetwork_estimates_counts_2018-2019.geojson` | `mit/NYC_pednetwork_estimates_counts_2018-2019.geojson` (symlink recommended) or `raw/` copy |
| `SHP/NYC_pednetwork_estimates_counts_2018-2019.*` | Optional; GeoJSON is enough for this codebase |
| `Model files/RF_*.pckl` | `data/mit/models/` symlinks or copies |
| `Preprint.pdf` | `data/mit/NYCWalks_preprint.pdf` (optional) |

**Symlink example** (keeps ~276 MB GeoJSON out of duplicate storage):

```bash
ln -sf "$HOME/Downloads/NYC_pednetwork_estimates_counts_2018-2019.geojson" \
  "$(git rev-parse --show-toplevel)/data/mit/NYC_pednetwork_estimates_counts_2018-2019.geojson"
```

Field dictionary and model naming: [`docs/mit_nycwalks_files.md`](../docs/mit_nycwalks_files.md).

## Legacy names

| Path | Notes |
|------|--------|
| `raw/nycwalks_network.geojson` | Still detected by map script |
| `../RF_wknd_n20_am_models.pckl` | Weekend AM model; also in repo root |

Large **copies** under `data/raw/` with extensions above are ignored; **symlinks** in `data/mit/` are small and can be committed.
