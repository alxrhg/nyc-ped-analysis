"""
Analysis of RF_wknd_n20_am_models.pckl
Random Forest Regressor — NYC Pedestrian Count Prediction (Weekend AM, n=20)

This script loads the pickled scikit-learn RandomForestRegressor model,
extracts key properties, and generates summary visualizations.
"""

import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")

MODEL_PATH = "RF_wknd_n20_am_models.pckl"

# ── 1. Load model ────────────────────────────────────────────────────────────
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# ── 2. Basic model info ─────────────────────────────────────────────────────
print("=" * 65)
print("  NYC Pedestrian Analysis — Random Forest Model Summary")
print("  File: RF_wknd_n20_am_models.pckl")
print("=" * 65)

print(f"\nModel type       : {type(model).__name__}")
print(f"Number of trees  : {model.n_estimators}")
print(f"Number of features: {model.n_features_in_}")
print(f"Number of outputs : {model.n_outputs_}")
print(f"Criterion        : {model.get_params()['criterion']}")
print(f"Max depth         : {model.get_params()['max_depth']} (unlimited)")
print(f"Min samples split : {model.get_params()['min_samples_split']}")
print(f"Min samples leaf  : {model.get_params()['min_samples_leaf']}")
print(f"Max features      : {model.get_params()['max_features']}")
print(f"Bootstrap         : {model.get_params()['bootstrap']}")

# Derive feature labels (model was trained without feature_names_in_)
FEATURE_NAMES = [f"Feature {i}" for i in range(model.n_features_in_)]
if hasattr(model, "feature_names_in_"):
    FEATURE_NAMES = list(model.feature_names_in_)

# ── 3. Feature importances ──────────────────────────────────────────────────
importances = model.feature_importances_
sorted_idx = np.argsort(importances)[::-1]

print("\n" + "-" * 65)
print("  Feature Importances (Mean Decrease in Impurity)")
print("-" * 65)
for rank, idx in enumerate(sorted_idx, 1):
    bar = "█" * int(importances[idx] * 100)
    print(f"  {rank:2d}. {FEATURE_NAMES[idx]:<14s}  {importances[idx]:.4f}  {bar}")

# ── 4. Per-tree statistics ───────────────────────────────────────────────────
depths = [t.tree_.max_depth for t in model.estimators_]
n_leaves = [t.tree_.n_leaves for t in model.estimators_]
n_nodes = [t.tree_.node_count for t in model.estimators_]

print("\n" + "-" * 65)
print("  Tree Ensemble Statistics (across 100 trees)")
print("-" * 65)
for label, vals in [("Max depth", depths), ("Leaf count", n_leaves), ("Node count", n_nodes)]:
    arr = np.array(vals)
    print(f"  {label:<12s}  min={arr.min():5d}  mean={arr.mean():8.1f}"
          f"  median={int(np.median(arr)):5d}  max={arr.max():5d}")

# ── 5. Per-tree feature importances (for std-dev bars) ──────────────────────
tree_importances = np.array([t.feature_importances_ for t in model.estimators_])
imp_std = tree_importances.std(axis=0)

# ── 6. Visualizations ───────────────────────────────────────────────────────
fig = plt.figure(figsize=(16, 14))
fig.suptitle(
    "NYC Pedestrian Analysis — Random Forest Model\n"
    "(Weekend AM period, n_estimators=100, 10 features)",
    fontsize=15, fontweight="bold", y=0.98,
)

gs = GridSpec(2, 2, hspace=0.35, wspace=0.3, top=0.92, bottom=0.06)

# 6a. Feature importances bar chart
ax1 = fig.add_subplot(gs[0, 0])
order = np.argsort(importances)
ax1.barh(
    [FEATURE_NAMES[i] for i in order],
    importances[order],
    xerr=imp_std[order],
    color="#3b82f6",
    edgecolor="white",
    capsize=3,
)
ax1.set_xlabel("Mean Decrease in Impurity")
ax1.set_title("Feature Importances (with std dev)")

# 6b. Distribution of tree depths
ax2 = fig.add_subplot(gs[0, 1])
ax2.hist(depths, bins=range(min(depths), max(depths) + 2), color="#10b981",
         edgecolor="white", align="left")
ax2.set_xlabel("Max Tree Depth")
ax2.set_ylabel("Number of Trees")
ax2.set_title("Distribution of Tree Depths")
ax2.axvline(np.mean(depths), color="#ef4444", ls="--", lw=1.5,
            label=f"mean = {np.mean(depths):.1f}")
ax2.legend()

# 6c. Distribution of leaf counts
ax3 = fig.add_subplot(gs[1, 0])
ax3.hist(n_leaves, bins=20, color="#f59e0b", edgecolor="white")
ax3.set_xlabel("Number of Leaves")
ax3.set_ylabel("Number of Trees")
ax3.set_title("Distribution of Leaf Counts")
ax3.axvline(np.mean(n_leaves), color="#ef4444", ls="--", lw=1.5,
            label=f"mean = {np.mean(n_leaves):.1f}")
ax3.legend()

# 6d. Feature importance heatmap across individual trees (sampled)
ax4 = fig.add_subplot(gs[1, 1])
sample_idx = np.linspace(0, len(model.estimators_) - 1, 30, dtype=int)
sampled = tree_importances[sample_idx]
im = ax4.imshow(sampled.T, aspect="auto", cmap="YlOrRd", interpolation="nearest")
ax4.set_yticks(range(len(FEATURE_NAMES)))
ax4.set_yticklabels(FEATURE_NAMES, fontsize=8)
ax4.set_xlabel("Tree index (sampled 30 of 100)")
ax4.set_title("Per-Tree Feature Importances")
fig.colorbar(im, ax=ax4, shrink=0.8)

output_path = "model_analysis.png"
fig.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"\n  Saved visualization → {output_path}")

# ── 7. Summary table as CSV ─────────────────────────────────────────────────
summary_df = pd.DataFrame({
    "feature": FEATURE_NAMES,
    "importance_mean": importances,
    "importance_std": imp_std,
    "rank": np.argsort(np.argsort(-importances)) + 1,
})
summary_df = summary_df.sort_values("rank")
csv_path = "feature_importances.csv"
summary_df.to_csv(csv_path, index=False)
print(f"  Saved feature table → {csv_path}")

print("\n" + "=" * 65)
print("  Analysis complete.")
print("=" * 65)
