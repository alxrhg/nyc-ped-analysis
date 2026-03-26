"""3D “prism” / bar map: extrude census tracts by a numeric attribute (matplotlib 3D)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors as mcolors
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3d projection
from shapely.geometry.base import BaseGeometry

# NYC State Plane: horizontal units are US survey feet (same factor used elsewhere).
FT_TO_M = 0.3048


def _study_outline_xy_m(study_wgs84: BaseGeometry) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return list of (x_m, y_m) rings in EPSG:2263 for polygon / multipolygon exterior."""
    gs = gpd.GeoSeries([study_wgs84], crs=4326).to_crs(2263)
    geom = gs.iloc[0]
    parts: list[Any] = list(getattr(geom, "geoms", [geom]))
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for p in parts:
        if p is None or p.is_empty:
            continue
        x, y = p.exterior.xy
        out.append((np.asarray(x, dtype=float) * FT_TO_M, np.asarray(y, dtype=float) * FT_TO_M))
    return out


def plot_tract_metric_3d_bars(
    tracts: gpd.GeoDataFrame,
    column: str,
    outfile: Path,
    *,
    study_geom_wgs84: Optional[BaseGeometry] = None,
    max_height_m: float = 900.0,
    footprint_scale: float = 0.42,
    cmap: str = "Greys",
    figsize: tuple[float, float] = (11.0, 9.0),
    dpi: int = 200,
    elev: float = 28.0,
    azim: float = -65.0,
    title: str | None = None,
    zlabel: str | None = None,
    alpha: float = 0.92,
) -> None:
    """
    Draw each tract as a vertical **3D bar** at its EPSG:2263 centroid.

    * **Footprint** — square side ``footprint_scale * sqrt(area_m²)`` (clamped), so large
      tracts read wider than small ones.
    * **Height** — linearly maps the chosen **column** between min/max (non-NaN) to
      ``[0, max_height_m]``.
    * **Color** — same normalization with ``cmap`` (default ``Greys``: higher = darker).

    This is a **schematic** view: bars are not true extruded footprints; distances are planar
    meters in the projected CRS (not Web Mercator).
    """
    if column not in tracts.columns:
        raise KeyError(f"Column {column!r} not in GeoDataFrame")
    t = tracts.to_crs(2263)
    cen = t.geometry.centroid
    xm = cen.x.to_numpy(dtype=float) * FT_TO_M
    ym = cen.y.to_numpy(dtype=float) * FT_TO_M
    area_m2 = (t.geometry.area.to_numpy(dtype=float) * (FT_TO_M**2)).clip(min=1e-6)
    side = np.sqrt(area_m2) * float(footprint_scale)
    side = np.clip(side, 25.0, 1200.0)

    v = pd.to_numeric(tracts[column], errors="coerce")
    ok = v.notna().to_numpy()
    if not ok.any():
        raise ValueError(f"No finite values in column {column!r}")
    vmin = float(np.nanmin(v[ok]))
    vmax = float(np.nanmax(v[ok]))
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax <= vmin:
        vmax = vmin + 1e-9
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    cmap_obj = plt.get_cmap(cmap)

    dz_full = np.zeros(len(tracts), dtype=float)
    vn = np.asarray(v, dtype=float)
    dz_full[ok] = (vn[ok] - vmin) / (vmax - vmin) * float(max_height_m)

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    for i in range(len(tracts)):
        if not ok[i]:
            continue
        dx = dy = side[i]
        xi = xm[i] - dx / 2.0
        yi = ym[i] - dy / 2.0
        zi = 0.0
        dzi = max(dz_full[i], 1e-6)
        c = cmap_obj(norm(float(vn[i])))
        ax.bar3d(
            xi,
            yi,
            zi,
            dx,
            dy,
            dzi,
            color=c,
            alpha=alpha,
            shade=True,
            linewidth=0.0,
        )

    if study_geom_wgs84 is not None:
        for xs, ys in _study_outline_xy_m(study_geom_wgs84):
            ax.plot(xs, ys, np.zeros_like(xs), color="crimson", linewidth=2.0, zorder=10)

    ax.set_xlabel("Easting (m, EPSG:2263 → m)")
    ax.set_ylabel("Northing (m)")
    ax.set_zlabel(zlabel or f"Height ∝ {column} (0–{max_height_m:.0f} m)")
    ttl = title or f"Manhattan tracts — 3D bars: {column}"
    ax.set_title(ttl, fontsize=12, pad=12)

    xr = float(xm.max() - xm.min()) or 1.0
    yr = float(ym.max() - ym.min()) or 1.0
    zr = float(max_height_m)
    ax.set_box_aspect((xr, yr, zr))

    ax.view_init(elev=elev, azim=azim)
    ax.grid(True, linestyle=":", alpha=0.35)

    m = plt.cm.ScalarMappable(norm=norm, cmap=cmap_obj)
    m.set_array([])
    fig.colorbar(m, ax=ax, shrink=0.55, pad=0.08, label=column)

    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outfile, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
