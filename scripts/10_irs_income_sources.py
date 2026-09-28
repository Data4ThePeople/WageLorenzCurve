"""Where income comes from, by size of income: IRS Statistics of Income Table 1.4,
tax year 2023 (all returns). Static chart for the post, dark house palette.

Shares are of "total income" on the return. Capital gains = capital gain
distributions + taxable net gain on Schedule D - taxable net loss. Partnership
and S corporation and sole proprietor income are net income minus net loss.
"Everything else" is total income minus the named sources (pensions, IRA
distributions, Social Security, rent, royalties, farm, other income, and losses).
Returns with no adjusted gross income are left out of the brackets (their
total income is negative) but included in "All returns".
"""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data/raw/irs/23in14ar.xls")
import argparse
_ap = argparse.ArgumentParser(); _ap.add_argument("--scale", type=float, default=1.0); _ap.add_argument("--out", default=None)
_args = _ap.parse_args()
FS = _args.scale      # text scale; 1.0 for the Day 1 image, larger for Day 2
OUT_PNG = _args.out or os.path.join(ROOT, "posts/lorenz-chart-viz/images/01-income-sources-by-income.png")
OUT_CSV = os.path.join(ROOT, "data/build/irs_income_sources_2023.csv")

x = pd.read_excel(SRC, header=None, dtype=str)
x = x.apply(lambda c: c.str.replace(r"\s+", " ", regex=True).str.strip() if c.dtype == object else c)
assert "Tax Year 2023" in x.iloc[0, 0] and "thousands of dollars" in x.iloc[1, 0]
# Amount columns, confirmed against the header rows (label sits one column to the left)
COL = dict(returns=1, total=4, wages=6, interest=20, dividends=24, sole_inc=32, sole_loss=34,
           cg_dist=36, cg_gain=38, cg_loss=40, part_inc=68, part_loss=70, scorp_inc=72, scorp_loss=74)
assert "Total wages" in x.iloc[2, 5] and "Taxable interest" in x.iloc[2, 19] and "Ordinary dividends" in x.iloc[2, 23]
assert "Net income" in x.iloc[3, 31] and "Net loss" in x.iloc[3, 33]
assert "Taxable net gain" in x.iloc[3, 37] and "Taxable net loss" in x.iloc[3, 39]
assert "Partnership" in x.iloc[2, 67] and "S corporation" in x.iloc[2, 71]

end = next(i for i in range(9, 60) if str(x.iloc[i, 0]).startswith("Taxable returns"))
first = {x.iloc[i, 0]: i for i in range(8, end)}          # the "All returns" block only
assert len(first) == end - 8, "duplicate row labels in the All returns block"
def row(label):
    r = x.iloc[first[label]]
    return {k: float(r[c]) for k, c in COL.items()}

BRACKETS = [
    ("Under $50,000", ["$1 under $5,000", "$5,000 under $10,000", "$10,000 under $15,000", "$15,000 under $20,000",
                       "$20,000 under $25,000", "$25,000 under $30,000", "$30,000 under $40,000", "$40,000 under $50,000"]),
    ("$50,000 to $100,000", ["$50,000 under $75,000", "$75,000 under $100,000"]),
    ("$100,000 to $200,000", ["$100,000 under $200,000"]),
    ("$200,000 to $500,000", ["$200,000 under $500,000"]),
    ("$500,000 to $1 million", ["$500,000 under $1,000,000"]),
    ("$1 million to $5 million", ["$1,000,000 under $1,500,000", "$1,500,000 under $2,000,000", "$2,000,000 under $5,000,000"]),
    ("$5 million to $10 million", ["$5,000,000 under $10,000,000"]),
    ("$10 million or more", ["$10,000,000 or more"]),
]
SOURCES = [("wages", "Wages"), ("cg", "Capital gains"), ("divint", "Dividends and interest"),
           ("pscorp", "Partnership and S corporation"), ("sole", "Sole proprietor"), ("other", "Everything else")]

def shares(labels):
    t = {k: 0.0 for k in COL}
    for l in labels:
        for k, v in row(l).items(): t[k] += v
    parts = dict(wages=t["wages"], cg=t["cg_dist"] + t["cg_gain"] - t["cg_loss"], divint=t["dividends"] + t["interest"],
                 pscorp=t["part_inc"] - t["part_loss"] + t["scorp_inc"] - t["scorp_loss"], sole=t["sole_inc"] - t["sole_loss"])
    parts["other"] = t["total"] - sum(parts.values())
    return t["returns"], {k: v / t["total"] for k, v in parts.items()}

rows = [("All returns", *shares(["All returns, total"]))] + [(name, *shares(ls)) for name, ls in BRACKETS]
# brackets must add back to the published total (all returns = no-AGI row + brackets)
n_sum = sum(r[1] for r in rows[1:]) + row("No adjusted gross income")["returns"]
assert abs(n_sum - row("All returns, total")["returns"]) < 5, n_sum
for name, n, s in rows:
    assert abs(sum(s.values()) - 1) < 1e-9 and min(s.values()) > -0.02, (name, s)

df = pd.DataFrame([{"bracket": name, "returns": n, **{lab: s[k] for k, lab in SOURCES}} for name, n, s in rows])
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True); df.to_csv(OUT_CSV, index=False)
print(df.assign(**{lab: (df[lab] * 100).round(1) for _, lab in SOURCES}).to_string(index=False))
top = dict(zip(df.bracket, df.to_dict("records")))["$10 million or more"]
print(f"\n$10M+: wages {top['Wages']*100:.1f}%; capital gains + dividends/interest + partnership/S corp "
      f"{(top['Capital gains'] + top['Dividends and interest'] + top['Partnership and S corporation'])*100:.1f}%")

# ---------------------------------------------------------------- chart
BG, INK, MUTED, GRID = "#181A1B", "#BBBDC0", "#8C9094", "#2A2E31"
COLORS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9", "#7a7f85"]   # dark categorical slots 1-4 and 7 (validated, CVD pass); neutral grey = everything else
plt.rcParams.update({"text.parse_math": False, "font.family": "DejaVu Sans", "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": INK})
fig = plt.figure(figsize=(8, 5.4), dpi=200, facecolor=BG)
ax = fig.add_axes([0.25 + 0.04 * (FS > 1), 0.12, 0.63 - 0.04 * (FS > 1), 0.64], facecolor=BG)
labels = [r[0] for r in rows][::-1]
data = df.iloc[::-1].reset_index(drop=True)
y = np.arange(len(labels)); y = y + np.where(np.array(labels) == "All returns", 0.35, 0)   # small gap above the brackets
left = np.zeros(len(labels))
for (k, lab), col in zip(SOURCES, COLORS):
    w = np.clip(data[lab].values, 0, None)
    ax.barh(y, w, left=left, height=0.68, color=col, edgecolor=BG, linewidth=1.2)
    for yi, l0, wi in zip(y, left, w):
        if wi >= 0.075:
            ax.text(l0 + wi / 2, yi, f"{wi*100:.0f}%", ha="center", va="center", fontsize=7.6 * FS, color="#FFFFFF" if col != "#c98500" else "#181A1B", fontweight="bold")
    left += w
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.4 * FS)
for t, lab in zip(ax.get_yticklabels(), labels):
    if lab == "All returns": t.set_fontweight("bold")
ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=7.6 * FS)
ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
for yi, n in zip(y, data.returns.values):
    ax.text(1.015, yi, f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:,.0f}K" if n >= 1e3 else f"{n:,.0f}", va="center", fontsize=7.2 * FS, color=MUTED, transform=ax.get_yaxis_transform())
ax.text(1.015, y.max() + 0.75, "Returns", fontsize=7.2 * FS, color=MUTED, transform=ax.get_yaxis_transform(), va="center")
fig.text(0.04, 0.945, "Where income comes from, by size of income", fontsize=13.5 * FS, fontweight="bold", color=INK)
fig.text(0.04, 0.9, "Share of total income on 2023 federal tax returns, by adjusted gross income", fontsize=9 * FS, color=MUTED)
# legend as colored words
for i, ((k, lab), col) in enumerate(zip(SOURCES, COLORS)):
    if i in (0, 3): xpos, ypos = 0.04, (0.848 if i == 0 else 0.812)
    t = fig.text(xpos, ypos, lab, fontsize=8.4 * FS, color=col if col != "#7a7f85" else "#9AA0A6", fontweight="bold")
    fig.canvas.draw(); xpos += t.get_window_extent().width / fig.bbox.width + 0.028
fig.text(0.04, 0.045, "Everything else: pensions, retirement accounts, Social Security, rent and other income, net of losses.", fontsize=6.4 * FS, color=MUTED)
fig.text(0.04, 0.02, "Source: IRS Statistics of Income, Table 1.4, tax year 2023, all returns.", fontsize=6.4 * FS, color=MUTED)
fig.text(0.96, 0.02, "Built by Data 4 The People", fontsize=6.4 * FS, color=MUTED, ha="right")
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
fig.savefig(OUT_PNG, facecolor=BG)
print("wrote", OUT_PNG)
