"""Hero source image: a simplified U.S. Lorenz curve, May 2025, rendered at hero
scale (1680x1080) in the dark house palette. `hero pad` then adds the padding.

Same data and method as the viz's May 2025 view (detailed occupations, jobs x
mean wage, sorted by mean wage). Bubble colors match the viz's major-group colors.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import usable, gini

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "posts/lorenz-chart-viz/images/lorenz-chart-viz-hero-source.png")

# same colors as MAJOR_COLOR in src/template.html
MAJOR_COLOR = {'11': '#1f4e9c', '13': '#5b8fd9', '15': '#6a3d9a', '17': '#9a7bd0', '19': '#bda4e6',
    '21': '#14694a', '23': '#2e9e6e', '25': '#62c08e', '27': '#9dd6ae', '29': '#b2182b', '31': '#e07a7a',
    '33': '#8c510a', '35': '#e6862b', '37': '#d9b33b', '39': '#b68a5a', '41': '#c2378f', '43': '#e58fc3',
    '45': '#7f8c3a', '47': '#2f6b75', '49': '#5fa3ad', '51': '#8a8a8a', '53': '#4a4a4a'}
BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"

d = pd.read_parquet(os.path.join(ROOT, "data/interim/oews_2025.parquet"))
u = usable(d[d.area_type == 1]).sort_values("a_mean", kind="stable")
e, w = u.tot_emp.values, (u.tot_emp * u.a_mean).values
x, y = np.cumsum(e) / e.sum(), np.cumsum(w) / w.sum()
G = gini(u.tot_emp, u.a_mean)
half = float(np.interp(0.5, np.r_[0, x], np.r_[0, y]))
assert round(G, 4) == 0.2837 and round(half * 100, 1) == 30.2, (G, half)   # matches the tie-out

plt.rcParams.update({"text.parse_math": False, "font.family": "DejaVu Sans"})
fig = plt.figure(figsize=(16.8, 10.8), dpi=100, facecolor=BG)
side = 860                                                   # square plot, in pixels
ax = fig.add_axes([0.065, 0.075, side / 1680, side / 1080], facecolor=BG)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
for s in ax.spines.values(): s.set_visible(False)
for v in (0.5, 1):
    ax.plot([v, v], [0, 1], color=GRID, lw=1, zorder=0); ax.plot([0, 1], [v, v], color=GRID, lw=1, zorder=0)
ax.plot([0, 1], [0, 0], color=GRID, lw=1.5, zorder=0); ax.plot([0, 0], [0, 1], color=GRID, lw=1.5, zorder=0)
ax.set_xticks([0, .5, 1]); ax.set_yticks([0, .5, 1])
ax.set_xticklabels(["0%", "50%", "100%"], fontsize=15, color=MUTED); ax.set_yticklabels(["0%", "50%", "100%"], fontsize=15, color=MUTED)
ax.tick_params(length=0, pad=8)
ax.fill_between(np.r_[0, x], np.r_[0, x], np.r_[0, y], color="#8FBFAF", alpha=0.08, lw=0, zorder=1)
ax.plot([0, 1], [0, 1], ls=(0, (6, 5)), color=MUTED, lw=2, zorder=2)
ax.text(0.62, 0.655, "Equal pay line", rotation=45, rotation_mode="anchor", color=MUTED, fontsize=15, ha="center", va="bottom")
ax.plot(np.r_[0, x], np.r_[0, y], color=INK, lw=2.5, zorder=3)
share = e / e.sum()
r = 34 * np.sqrt(share / share.max())                   # points, largest bubble ~34 pt radius
order = np.argsort(-r)
cols = [MAJOR_COLOR[c[:2]] for c in u.occ_code]
ax.scatter(x[order], y[order], s=(np.maximum(r[order], 2.2)) ** 2, c=[cols[i] for i in order], alpha=0.85,
           edgecolors=BG, linewidths=1.2, zorder=4)
ax.plot([0.5, 0.5, 0], [0, half, half], ls=(0, (2, 3)), color=INK, lw=1.4, zorder=5)
ax.text(0.02, half + 0.025, f"Lowest-paid half: {half*100:.1f}% of wages", color=INK, fontsize=16, fontweight="bold", zorder=6)
fig.text(0.065, 0.945, "Share of total payroll wages vs. share of workers, U.S., May 2025", fontsize=16, color=MUTED)

tx = 0.62
fig.text(tx, 0.74, "Occupational\nPay Gaps\nby Place", fontsize=52, fontweight="bold", color=INK, va="top", linespacing=1.05)
fig.text(tx, 0.43, f"{half*100:.1f}%", fontsize=64, fontweight="bold", color="#8FBFAF", va="top")
fig.text(tx, 0.325, "of U.S. payroll wages go to\nthe lowest-paid half of workers", fontsize=22, color=INK, va="top", linespacing=1.25)
fig.text(tx, 0.2, "Every state, metro and rural area\nPayroll (W-2) wages only", fontsize=17, color=MUTED, va="top", linespacing=1.35)
fig.text(tx, 0.075, "Data 4 The People  ·  Source: BLS OEWS, May 2025", fontsize=14, color=MUTED)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, facecolor=BG)
print("wrote", OUT, f"Gini {G:.4f}, lowest-paid half {half*100:.1f}%")
