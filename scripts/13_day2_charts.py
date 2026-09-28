"""Static charts for the Day 2 post, from data/build/day2_numbers.json (run 12 first).

Dark house palette (#181A1B background, #BBBDC0 text), every chart titled,
legends as colored words, colors from the validated dark categorical slots.
Charts go to analysis/day2_charts/ until step 2a sets the slug.
"""
import json, os, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = json.load(open(os.path.join(ROOT, "data/build/day2_numbers.json")))
OUT = os.path.join(ROOT, "analysis/day2_charts"); os.makedirs(OUT, exist_ok=True)
FS = 1.35   # text scale for Day 2 charts (Eric: larger text)
BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"
BLUE, ORANGE, AQUA, YELLOW, VIOLET, GREY = "#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9", "#7a7f85"
plt.rcParams.update({"text.parse_math": False, "font.family": "DejaVu Sans", "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": INK})
SOURCE_OEWS = "Source: BLS Occupational Employment and Wage Statistics, May 2025."
CREDIT = "Built by Data 4 The People"


def frame(title, subtitle, h=5.4):
    fig = plt.figure(figsize=(8, h), dpi=200, facecolor=BG)
    fig.text(0.04, 1 - 0.3 / h, title, fontsize=13.5 * FS, fontweight="bold", va="top")
    fig.text(0.04, 1 - 0.62 / h, subtitle, fontsize=8.8 * FS, color=MUTED, va="top")
    return fig


def legend_words(fig, items, y):
    x = 0.04
    for lab, col in items:
        t = fig.text(x, y, lab, fontsize=8.6 * FS, color=col, fontweight="bold", va="top")
        fig.canvas.draw(); x += t.get_window_extent().width / fig.bbox.width + 0.03


def footer(fig, source, note=None):
    if note: fig.text(0.04, 0.045, note, fontsize=6.4 * FS, color=MUTED)
    fig.text(0.04, 0.02, source, fontsize=6.4 * FS, color=MUTED)
    fig.text(0.96, 0.02, CREDIT, fontsize=6.4 * FS, color=MUTED, ha="right")


def clean(ax):
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); ax.set_facecolor(BG)


def short(t):
    return (t.replace("-Sunnyvale-Santa Clara", "").replace("-Newark-Jersey City", "").replace("-Oakland-Fremont", "")
             .replace("-Stamford-Danbury", "").replace("-Sandy Springs-Roswell", "").replace("-Pasadena-The Woodlands", "")
             .replace("-San Bernardino-Ontario", "").replace("-Wyoming-Kentwood", "").replace("/Jefferson County", "")
             .replace("-Cheektowaga", "").replace("-Vancouver-Hillsboro", "").replace("-Henderson-North Las Vegas", "")
             .replace("-Arlington-Alexandria", "").replace("-Concord-Gastonia", "").replace("-Chula Vista-Carlsbad", "")
             .replace("-Carmel-Greenwood", ""))


def three_measures(key, title, subtitle, fname, shorten=False):
    """Three panels: Gini, lowest-paid half's share, top 10% vs median. 5 most (orange) and 5 least (blue) unequal each."""
    fig = frame(title, subtitle, h=6.2)
    legend_words(fig, [("Most unequal", ORANGE), ("Least unequal", BLUE)], 1 - 0.95 / 6.2)
    specs = [("gini", "Gini of payroll wages\nacross occupations", "{:.3f}"),
             ("half", "Share of wages to the\nlowest-paid half", "{:.1%}"),
             ("top10_vs_median", "Top 10% pay line vs.\nthe median wage", "{:.0%}")]
    for i, (col, head, fmt) in enumerate(specs):
        ax = fig.add_axes([0.04 + i * 0.325, 0.1, 0.29, 0.6]); clean(ax)
        most, least = N[key][col]["most"], N[key][col]["least"]
        names = [short(n) if shorten else n for n, _ in most] + [short(n) if shorten else n for n, _ in least]
        vals = [v for _, v in most] + [v for _, v in least]
        cols = [ORANGE] * len(most) + [BLUE] * len(least)
        y = np.r_[np.arange(len(most)), np.arange(len(least)) + len(most) + 0.6][::-1]
        lo = min(vals) * 0.0
        ax.barh(y, vals, color=cols, height=0.72, left=lo)
        ax.set_xlim(0, max(vals) * 1.28); ax.set_yticks([]); ax.set_xticks([])
        fig.canvas.draw(); inv = ax.transData.inverted()
        for yi, v, n in zip(y, vals, names):
            t = ax.text(0.01 * max(vals), yi, n, va="center", fontsize=6.9 * FS, color="#FFFFFF")
            name_end = inv.transform(t.get_window_extent(fig.canvas.get_renderer()))[1][0]
            ax.text(max(v, name_end) + 0.012 * max(vals), yi, fmt.format(v), va="center", fontsize=7 * FS, color=INK)
        ax.set_title(head, fontsize=8.6 * FS, color=INK, loc="left", pad=6)
    return fig


# 1. States
fig = three_measures("states", "Most and least unequal states, May 2025",
                     "Five most and five least unequal on three measures.", "01-states")
us = N["us"]
footer(fig, SOURCE_OEWS, f"U.S.: Gini {us['gini']:.3f}; lowest-paid half {us['half']:.1%}; top 10% line {us['top10_vs_median']:.0%} above median. Payroll wages only.")
fig.savefig(os.path.join(OUT, "01-states-three-measures.png"), facecolor=BG); plt.close(fig)

# 1b. Lorenz curves: New York vs. Maine (most and least unequal states by the Gini), May 2025
import sys, pandas as pd
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from lorenz import usable, gini as _gini
_d = pd.read_parquet(os.path.join(ROOT, "data/interim/oews_2025.parquet"))
fig = frame("How far the curve bows shows the gap", "Share of payroll wages by share of workers, May 2025.", h=6.4)
ax = fig.add_axes([0.14, 0.17, 0.62, 0.62]); clean(ax); ax.set_aspect("equal")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
for v in (0.25, 0.5, 0.75, 1): ax.plot([v, v], [0, 1], color=GRID, lw=0.6, zorder=0); ax.plot([0, 1], [v, v], color=GRID, lw=0.6, zorder=0)
ax.plot([0, 1], [0, 1], ls=(0, (5, 4)), color=MUTED, lw=1.4)
ax.text(0.36, 0.40, "Equal pay line", rotation=45, rotation_mode="anchor", color=MUTED, fontsize=8 * FS)
LZ = {}
for name, col, lx in (("New York", ORANGE, 0.62), ("Maine", BLUE, 0.45)):
    u = usable(_d[_d.area_title == name]).sort_values("a_mean", kind="stable")
    e = u.tot_emp.values; w = e * u.a_mean.values
    x = np.r_[0, np.cumsum(e) / e.sum()]; y = np.r_[0, np.cumsum(w) / w.sum()]
    g = _gini(u.tot_emp, u.a_mean); h = float(np.interp(0.5, x, y)); LZ[name] = (g, h)
    ax.plot(x, y, color=col, lw=2.4)
    ax.plot([0.5], [h], "o", color=col, ms=6)

legend_words(fig, [(f"Maine, Gini {LZ['Maine'][0]:.3f}", BLUE), (f"New York, Gini {LZ['New York'][0]:.3f}", ORANGE)], 1 - 0.95 / 6.4)
assert abs(LZ["New York"][0] - dict((n, v) for n, v in N["states"]["gini"]["most"])["New York"]) < 1e-9
ax.plot([0.5, 0.5], [0, max(v[1] for v in LZ.values())], ls=(0, (2, 3)), color=INK, lw=0.9)
ax.text(0.52, 0.06, f"Lowest-paid half of workers:\nMaine {LZ['Maine'][1]:.1%} of wages\nNew York {LZ['New York'][1]:.1%}", fontsize=7.8 * FS, color=INK)
ax.set_xticks([0, .5, 1]); ax.set_yticks([0, .5, 1])
ax.set_xticklabels(["0%", "50%", "100%"], fontsize=7.5 * FS); ax.set_yticklabels(["0%", "50%", "100%"], fontsize=7.5 * FS)
ax.set_xlabel("Share of workers, lowest paid to highest paid", fontsize=8 * FS, color=INK)
ax.set_ylabel("Share of total wages", fontsize=8 * FS, color=INK)
ax.text(0.03, 0.97, "The farther a curve bows\nbelow the equal pay line,\nthe bigger the gap.", fontsize=8.6 * FS, color=INK, va="top", transform=ax.transAxes)
footer(fig, SOURCE_OEWS, "Payroll wages only. Each curve adds up occupations from lowest to highest average pay.")
fig.savefig(os.path.join(OUT, "01b-lorenz-new-york-vs-maine.png"), facecolor=BG); plt.close(fig)

# 2. Metros, all and 500,000+ jobs
fig = three_measures("metros", "Most and least unequal metro areas, May 2025",
                     f"{N['metros']['n']} metro areas outside Puerto Rico, three measures.", "02-metros", shorten=True)
footer(fig, SOURCE_OEWS, "Payroll wages only. Puerto Rico's six metros are left out; wages there are much lower.")
fig.savefig(os.path.join(OUT, "02a-metros-three-measures.png"), facecolor=BG); plt.close(fig)
fig = three_measures("big_metros", "Most and least unequal large metros, May 2025",
                     f"The {N['big_metros']['n']} metro areas with 500,000 or more jobs, three measures.", "02b", shorten=True)
footer(fig, SOURCE_OEWS, "Payroll wages only.")
fig.savefig(os.path.join(OUT, "02b-large-metros-three-measures.png"), facecolor=BG); plt.close(fig)


# 3. Dollar gaps
def gap_chart(which, low_name, fname, title, short_low):
    G = N["gaps"]; metros = list(G)
    occs = ["Registered nurses", "Software developers", "Lawyers"]; ccol = [BLUE, ORANGE, AQUA]
    fig = frame(title, "How much more each job pays per year, same metro area, May 2025.", h=6.0)
    legend_words(fig, list(zip(occs, ccol)), 1 - 0.95 / 6.0)
    ax = fig.add_axes([0.25, 0.1, 0.66, 0.66]); clean(ax)
    ys, labels = [], []
    for i, m in enumerate(metros):
        base = i * 4.2 + (1.2 if i >= 3 else 0)
        for j, (o, c) in enumerate(zip(occs, ccol)):
            v = G[m][which][o]; y = base + j
            ax.barh(y, v, color=c, height=0.8)
            ax.text(v + 3000, y, f"${v:,.0f}", va="center", fontsize=7 * FS, color=INK)
        ys.append(base + 1); labels.append(f"{m}\n{short_low}: ${G[m]['wages'][low_name]:,.0f}")
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=7.6 * FS); ax.invert_yaxis()
    ax.set_xticks([0, 100000, 200000]); ax.set_xticklabels(["$0", "$100,000", "$200,000"], fontsize=7 * FS)
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_xlim(0, max(G[m][which][o] for m in metros for o in occs) * 1.18)
    ax.text(-0.35, 1.2 + 0.0, "", transform=ax.get_yaxis_transform())
    fig.text(0.04, 0.765, "Most unequal metros", fontsize=7.6 * FS, color=ORANGE, fontweight="bold")
    fig.text(0.04, 0.42, "Least unequal metros", fontsize=7.6 * FS, color=BLUE, fontweight="bold")
    footer(fig, SOURCE_OEWS, "Gap = difference in average annual wages within the same metro area.")
    fig.savefig(os.path.join(OUT, fname), facecolor=BG); plt.close(fig)


gap_chart("gap_vs_aides", "Home health and personal care aides", "03a-gap-vs-home-health-aides.png",
          "The pay gap in dollars vs. home health aides", "Aide pay")
gap_chart("gap_vs_fastfood", "Fast food and counter workers", "03b-gap-vs-fast-food.png",
          "The pay gap in dollars vs. fast food workers", "Fast food pay")

# 4. Change over time
C = N["change"]
bars = [("States, since 2016", C["states_2016"]), ("States, since 2022", C["states_2022"]),
        ("Metro areas, since 2016", C["metros_2016"]), ("Metro areas, since 2022", C["metros_2022"])]
fig = frame("Narrower since 2016, mixed since 2022",
            "Change in the Gini of payroll wages across occupations, to May 2025.", h=4.6)
legend_words(fig, [("Narrowed", BLUE), ("No clear change", "#9AA0A6"), ("Widened", ORANGE)], 1 - 0.95 / 4.6)
ax = fig.add_axes([0.28, 0.15, 0.68, 0.58]); clean(ax)
for i, (lab, c) in enumerate(bars):
    left = 0
    for k, col in (("narrowed", BLUE), ("no_clear_change", GREY), ("widened", ORANGE)):
        w = c[k] / c["n"]
        ax.barh(i, w, left=left, color=col, height=0.62, edgecolor=BG, linewidth=1.2)
        if w > 0.06: ax.text(left + w / 2, i, f"{c[k]}", ha="center", va="center", fontsize=8 * FS, color="#FFFFFF", fontweight="bold")
        left += w
ax.set_yticks(range(4)); ax.set_yticklabels([f"{l}\n({c['n']} places)" for l, c in bars], fontsize=8 * FS); ax.invert_yaxis()
ax.set_xlim(0, 1); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0%", "50%", "100%"], fontsize=7 * FS)
footer(fig, "Source: BLS OEWS, May 2016, 2022 and 2025.",
       "A change counts only if it clears survey noise and our other checks.")
fig.savefig(os.path.join(OUT, "04-change-since-2016-and-2022.png"), facecolor=BG); plt.close(fig)

# 5a. National IRS chart from Day 1 (same file)
import subprocess, sys
subprocess.run([sys.executable, os.path.join(ROOT, "scripts/10_irs_income_sources.py"), "--scale", str(FS),
                "--out", os.path.join(OUT, "05a-income-sources-by-income.png")], check=True, capture_output=True)

# 5b. Counties by income fifth, plus named counties
CO = N["county"]; SRC = ["Wages", "Capital gains", "Dividends and interest", "Partnership and S corporation", "Sole proprietor", "Everything else"]
COLS = [BLUE, ORANGE, AQUA, YELLOW, VIOLET, GREY]
rows = [(f"{q}\n(median ${v['agi_per_return_median']:,.0f} per return)", v) for q, v in CO["pooled_fifths"].items()]
rows += [(n.replace(" (New York County), NY", ", NY").replace("Collier County, FL", "Collier County, FL (Naples)"), v)
         for n, v in CO["named"].items() if not n.startswith("Los Angeles")]
fig = frame("Where income comes from, by county", f"2023 tax returns, {CO['n']} counties with 100,000+ people, by income per return.", h=6.0)
for i, ((lab, col)) in enumerate(zip(SRC, COLS)):
    pass
x = 0.04
for k, (lab, col) in enumerate(zip(SRC, COLS)):
    if k == 3: x = 0.04
    t = fig.text(x, 1 - (0.95 if k < 3 else 1.2) / 6.0, lab, fontsize=8.4 * FS, color=col if col != GREY else "#9AA0A6", fontweight="bold", va="top")
    fig.canvas.draw(); x += t.get_window_extent().width / fig.bbox.width + 0.03
ax = fig.add_axes([0.33, 0.11, 0.63, 0.63]); clean(ax)
y = np.arange(len(rows)); y = np.where(y >= 5, y + 0.5, y)
for yi, (lab, v) in zip(y, rows):
    left = 0
    for s, col in zip(SRC, COLS):
        w = max(v[s], 0)
        ax.barh(yi, w, left=left, color=col, height=0.7, edgecolor=BG, linewidth=1.1)
        if w >= 0.075: ax.text(left + w / 2, yi, f"{w*100:.0f}%", ha="center", va="center", fontsize=7.2 * FS, color="#181A1B" if col == YELLOW else "#FFFFFF", fontweight="bold")
        left += w
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.4 * FS); ax.invert_yaxis()
ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7 * FS)
ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
footer(fig, "Source: IRS Statistics of Income, county data, tax year 2023.",
       "Everything else: pensions, retirement accounts, Social Security, rent, other.")
fig.savefig(os.path.join(OUT, "05b-income-sources-by-county.png"), facecolor=BG); plt.close(fig)
print("wrote", sorted(os.listdir(OUT)))
