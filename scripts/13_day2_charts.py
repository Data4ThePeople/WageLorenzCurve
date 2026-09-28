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
BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"
BLUE, ORANGE, AQUA, YELLOW, VIOLET, GREY = "#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9", "#7a7f85"
plt.rcParams.update({"text.parse_math": False, "font.family": "DejaVu Sans", "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": INK})
SOURCE_OEWS = "Source: U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics, May 2025."
CREDIT = "Built by Data 4 The People"


def frame(title, subtitle, h=5.4):
    fig = plt.figure(figsize=(8, h), dpi=200, facecolor=BG)
    fig.text(0.04, 1 - 0.3 / h, title, fontsize=13.5, fontweight="bold", va="top")
    fig.text(0.04, 1 - 0.62 / h, subtitle, fontsize=8.8, color=MUTED, va="top")
    return fig


def legend_words(fig, items, y):
    x = 0.04
    for lab, col in items:
        t = fig.text(x, y, lab, fontsize=8.6, color=col, fontweight="bold", va="top")
        fig.canvas.draw(); x += t.get_window_extent().width / fig.bbox.width + 0.03


def footer(fig, source, note=None):
    if note: fig.text(0.04, 0.045, note, fontsize=6.4, color=MUTED)
    fig.text(0.04, 0.02, source, fontsize=6.4, color=MUTED)
    fig.text(0.96, 0.02, CREDIT, fontsize=6.4, color=MUTED, ha="right")


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
        ax = fig.add_axes([0.04 + i * 0.325, 0.1, 0.29, 0.66]); clean(ax)
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
            t = ax.text(0.01 * max(vals), yi, n, va="center", fontsize=6.9, color="#FFFFFF")
            name_end = inv.transform(t.get_window_extent(fig.canvas.get_renderer()))[1][0]
            ax.text(max(v, name_end) + 0.012 * max(vals), yi, fmt.format(v), va="center", fontsize=7, color=INK)
        ax.set_title(head, fontsize=8.6, color=INK, loc="left", pad=6)
    return fig


# 1. States
fig = three_measures("states", "The most and least unequal states, May 2025",
                     "Three ways to measure the pay gap. Five most and five least unequal states on each.", "01-states")
us = N["us"]
footer(fig, SOURCE_OEWS, f"U.S.: Gini {us['gini']:.3f}; lowest-paid half get {us['half']:.1%} of payroll wages; top 10% pay line {us['top10_vs_median']:.0%} above the median. Payroll (W-2) wages only.")
fig.savefig(os.path.join(OUT, "01-states-three-measures.png"), facecolor=BG); plt.close(fig)

# 2. Metros, all and 500,000+ jobs
fig = three_measures("metros", "The most and least unequal metro areas, May 2025",
                     f"All {N['metros']['n']} metro areas outside Puerto Rico. Five most and five least unequal on each measure.", "02-metros", shorten=True)
footer(fig, SOURCE_OEWS, "Payroll (W-2) wages only. Puerto Rico's six metro areas are left out; wages there are much lower overall.")
fig.savefig(os.path.join(OUT, "02a-metros-three-measures.png"), facecolor=BG); plt.close(fig)
fig = three_measures("big_metros", "Large metro areas: the most and least unequal, May 2025",
                     f"The {N['big_metros']['n']} metro areas with 500,000 or more jobs. Five most and five least unequal on each measure.", "02b", shorten=True)
footer(fig, SOURCE_OEWS, "Payroll (W-2) wages only.")
fig.savefig(os.path.join(OUT, "02b-large-metros-three-measures.png"), facecolor=BG); plt.close(fig)


# 3. Dollar gaps
def gap_chart(which, low_name, fname, title, short_low):
    G = N["gaps"]; metros = list(G)
    occs = ["Registered nurses", "Software developers", "Lawyers"]; ccol = [BLUE, ORANGE, AQUA]
    fig = frame(title, f"How much more each job pays per year than {low_name.lower()}, same metro area, May 2025.", h=6.0)
    legend_words(fig, list(zip(occs, ccol)), 1 - 0.95 / 6.0)
    ax = fig.add_axes([0.25, 0.1, 0.68, 0.7]); clean(ax)
    ys, labels = [], []
    for i, m in enumerate(metros):
        base = i * 4.2 + (1.2 if i >= 3 else 0)
        for j, (o, c) in enumerate(zip(occs, ccol)):
            v = G[m][which][o]; y = base + j
            ax.barh(y, v, color=c, height=0.8)
            ax.text(v + 3000, y, f"${v:,.0f}", va="center", fontsize=7, color=INK)
        ys.append(base + 1); labels.append(f"{m}\n{short_low}: ${G[m]['wages'][low_name]:,.0f}")
    ax.set_yticks(ys); ax.set_yticklabels(labels, fontsize=7.6); ax.invert_yaxis()
    ax.set_xticks([0, 100000, 200000]); ax.set_xticklabels(["$0", "$100,000", "$200,000"], fontsize=7)
    ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_xlim(0, max(G[m][which][o] for m in metros for o in occs) * 1.18)
    ax.text(-0.35, 1.2 + 0.0, "", transform=ax.get_yaxis_transform())
    fig.text(0.04, 0.785, "Most unequal metros", fontsize=7.6, color=ORANGE, fontweight="bold")
    fig.text(0.04, 0.42, "Least unequal metros", fontsize=7.6, color=BLUE, fontweight="bold")
    footer(fig, SOURCE_OEWS, "Average annual wages. Gap = higher-paid job's average minus the lower-paid job's average in the same metro area.")
    fig.savefig(os.path.join(OUT, fname), facecolor=BG); plt.close(fig)


gap_chart("gap_vs_aides", "Home health and personal care aides", "03a-gap-vs-home-health-aides.png",
          "The pay gap in dollars: higher-paid jobs vs. home health aides", "Aide pay")
gap_chart("gap_vs_fastfood", "Fast food and counter workers", "03b-gap-vs-fast-food.png",
          "The pay gap in dollars: higher-paid jobs vs. fast food workers", "Fast food pay")

# 4. Change over time
C = N["change"]
bars = [("States, since 2016", C["states_2016"]), ("States, since 2022", C["states_2022"]),
        ("Metro areas, since 2016", C["metros_2016"]), ("Metro areas, since 2022", C["metros_2022"])]
fig = frame("The gap between occupations: narrower since 2016, mixed since 2022",
            "Change in the Gini of payroll wages across occupations to May 2025, places with comparable data.", h=4.6)
legend_words(fig, [("Narrowed", BLUE), ("No clear change", "#9AA0A6"), ("Widened", ORANGE)], 1 - 0.95 / 4.6)
ax = fig.add_axes([0.24, 0.14, 0.72, 0.6]); clean(ax)
for i, (lab, c) in enumerate(bars):
    left = 0
    for k, col in (("narrowed", BLUE), ("no_clear_change", GREY), ("widened", ORANGE)):
        w = c[k] / c["n"]
        ax.barh(i, w, left=left, color=col, height=0.62, edgecolor=BG, linewidth=1.2)
        if w > 0.06: ax.text(left + w / 2, i, f"{c[k]}", ha="center", va="center", fontsize=8, color="#FFFFFF", fontweight="bold")
        left += w
ax.set_yticks(range(4)); ax.set_yticklabels([f"{l}\n({c['n']} places)" for l, c in bars], fontsize=8); ax.invert_yaxis()
ax.set_xlim(0, 1); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0%", "50%", "100%"], fontsize=7)
footer(fig, "Source: BLS OEWS, May 2016, 2022 and 2025. Data 4 The People analysis.",
       "A change counts only if it clears survey noise and our other checks. Years compared are three apart, so they share no survey data.")
fig.savefig(os.path.join(OUT, "04-change-since-2016-and-2022.png"), facecolor=BG); plt.close(fig)

# 5a. National IRS chart from Day 1 (same file)
shutil.copy(os.path.join(ROOT, "posts/lorenz-chart-viz/images/01-income-sources-by-income.png"), os.path.join(OUT, "05a-income-sources-by-income.png"))

# 5b. Counties by income fifth, plus named counties
CO = N["county"]; SRC = ["Wages", "Capital gains", "Dividends and interest", "Partnership and S corporation", "Sole proprietor", "Everything else"]
COLS = [BLUE, ORANGE, AQUA, YELLOW, VIOLET, GREY]
rows = [(f"{q}\n(median ${v['agi_per_return_median']:,.0f} per return)", v) for q, v in CO["pooled_fifths"].items()]
rows += [(n.replace(" (New York County), NY", ", NY").replace("Collier County, FL", "Collier County, FL (Naples)"), v)
         for n, v in CO["named"].items() if not n.startswith("Los Angeles")]
fig = frame("Where income comes from, by county", f"Share of total income on 2023 tax returns. {CO['n']} counties with 100,000+ residents, grouped by income per return.", h=6.0)
for i, ((lab, col)) in enumerate(zip(SRC, COLS)):
    pass
x = 0.04
for k, (lab, col) in enumerate(zip(SRC, COLS)):
    if k == 3: x = 0.04
    t = fig.text(x, 1 - (0.95 if k < 3 else 1.2) / 6.0, lab, fontsize=8.4, color=col if col != GREY else "#9AA0A6", fontweight="bold", va="top")
    fig.canvas.draw(); x += t.get_window_extent().width / fig.bbox.width + 0.03
ax = fig.add_axes([0.3, 0.1, 0.66, 0.66]); clean(ax)
y = np.arange(len(rows)); y = np.where(y >= 5, y + 0.5, y)
for yi, (lab, v) in zip(y, rows):
    left = 0
    for s, col in zip(SRC, COLS):
        w = max(v[s], 0)
        ax.barh(yi, w, left=left, color=col, height=0.7, edgecolor=BG, linewidth=1.1)
        if w >= 0.075: ax.text(left + w / 2, yi, f"{w*100:.0f}%", ha="center", va="center", fontsize=7.2, color="#181A1B" if col == YELLOW else "#FFFFFF", fontweight="bold")
        left += w
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=7.4); ax.invert_yaxis()
ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7)
ax.xaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
footer(fig, "Source: IRS Statistics of Income, county data, tax year 2023.",
       "Each fifth adds up all income in its counties. Everything else: pensions, retirement accounts, Social Security, rent and other income, net of losses.")
fig.savefig(os.path.join(OUT, "05b-income-sources-by-county.png"), facecolor=BG); plt.close(fig)
print("wrote", sorted(os.listdir(OUT)))
