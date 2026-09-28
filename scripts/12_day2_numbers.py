"""Numbers for the Day 2 post (five takeaways), agreed with Eric on September 28, 2026.

1. States, May 2025: Gini of payroll wages across occupations, share of payroll
   wages to the lowest-paid half, and the pay needed to be in the top 10% vs.
   the median (BLS all-occupation percentiles).
2. Metro areas, same three measures (Puerto Rico listed apart), plus metros
   with 500,000+ jobs.
3. Dollar gaps between higher-paid occupations (registered nurses, software
   developers, lawyers) and lower-paid ones (home health and personal care
   aides; fast food and counter workers) in the most and least unequal metros;
   New York home health aides 2016 to 2025.
4. Change over time: verdicts since 2016 and since 2022 (history tests).
5. Income sources on 2023 tax returns by county (IRS county file): median
   large county vs. the richest fifth vs. named counties.

Writes data/build/day2_numbers.json and prints every number.
"""
import json, os, sys, zipfile
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import usable
from geo import area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data/interim")
OUT = os.path.join(ROOT, "data/build/day2_numbers.json")
N = {}

d25 = pd.read_parquet(os.path.join(INT, "oews_2025.parquet")); d25["akey"] = area_key(d25.area)
met = pd.read_parquet(os.path.join(INT, "area_metrics.parquet")); met["akey"] = area_key(met.area)
m25 = met[met.year == 2025].set_index("akey")
tot = d25[d25.o_group == "total"].set_index("akey")


def half_share(g):
    u = usable(g).sort_values("a_mean", kind="stable")
    e = u.tot_emp.values; w = e * u.a_mean.values
    return float(np.interp(0.5, np.r_[0, np.cumsum(e) / e.sum()], np.r_[0, np.cumsum(w) / w.sum()]))


rows = []
for ak, g in d25[d25.area_type.isin([1, 2, 4])].groupby("akey"):
    rows.append(dict(akey=ak, title=g.area_title.iloc[0], type=int(g.area_type.iloc[0]), jobs=float(tot.loc[ak, "tot_emp"]),
                     gini=float(m25.loc[ak, "gini"]), half=half_share(g),
                     p90=float(tot.loc[ak, "a_pct90"]), p50=float(tot.loc[ak, "a_median"])))
R = pd.DataFrame(rows); R["top10_vs_median"] = R.p90 / R.p50 - 1
N["us"] = R[R.type == 1].iloc[0][["gini", "half", "top10_vs_median", "p90", "p50"]].to_dict()


def ranks(x, k=5):
    out = {}
    for col, most_first in (("gini", False), ("half", True), ("top10_vs_median", False)):
        y = x.sort_values(col, ascending=most_first)
        out[col] = {"most": y.head(k)[["title", col]].values.tolist(), "least": y.tail(k)[::-1][["title", col]].values.tolist()}
    rk = x[["gini", "half", "top10_vs_median"]].rank()
    out["agreement"] = {"gini_vs_half": float(rk.gini.corr(-rk.half)), "gini_vs_top10": float(rk.gini.corr(rk.top10_vs_median))}
    out["n"] = len(x)
    return out


states = R[R.type == 2]
metros = R[(R.type == 4) & ~R.title.str.contains(", PR")]
big = metros[metros.jobs >= 500_000]
N["states"] = ranks(states)
N["metros"] = ranks(metros)
N["big_metros"] = ranks(big)
pr = R[(R.type == 4) & R.title.str.contains(", PR")]
N["puerto_rico_gini_range"] = [float(pr.gini.min()), float(pr.gini.max()), int(len(pr))]

# 3. dollar gaps
OCC = {"31-1120": "Home health and personal care aides", "35-3023": "Fast food and counter workers",
       "29-1141": "Registered nurses", "15-1252": "Software developers", "23-1011": "Lawyers"}
METROS3 = {"41940": "San Jose", "41860": "San Francisco", "35620": "New York",
           "24420": "Grants Pass, OR", "27900": "Joplin, MO-KS", "31140": "Louisville, KY-IN"}
x = d25[d25.akey.isin(METROS3) & d25.occ_code.isin(OCC) & (d25.o_group == "detailed")]
W = x.pivot_table(index="akey", columns="occ_code", values="a_mean")
J = x.pivot_table(index="akey", columns="occ_code", values="tot_emp")
assert W.reindex(list(METROS3)).notna().all().all(), "an occupation is not published in a chosen metro"
gaps = {}
for ak, name in METROS3.items():
    gaps[name] = {"gini": float(m25.loc[ak, "gini"]),
                  "wages": {OCC[c]: float(W.loc[ak, c]) for c in OCC},
                  "jobs": {OCC[c]: float(J.loc[ak, c]) for c in OCC},
                  "gap_vs_aides": {OCC[c]: float(W.loc[ak, c] - W.loc[ak, "31-1120"]) for c in ("29-1141", "15-1252", "23-1011")},
                  "gap_vs_fastfood": {OCC[c]: float(W.loc[ak, c] - W.loc[ak, "35-3023"]) for c in ("29-1141", "15-1252", "23-1011")}}
N["gaps"] = gaps
# Riverside: most equal large metro, California (nurse check)
rv = d25[(d25.akey == "40140") & (d25.o_group == "detailed")].set_index("occ_code").a_mean
N["riverside_nurse_vs_aide_pct"] = float(rv["29-1141"] / rv["31-1120"] - 1)
# New York aides over the comparison years (combined codes before 2019)
cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))
ny = {}
for y in (2016, 2019, 2022, 2025):
    d = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet")); d["akey"] = area_key(d.area)
    codes = cmap[(cmap.year == y) & (cmap.hgroup == "31-1120")].occ_code
    a = d[(d.akey == "35620") & d.occ_code.isin(codes) & d.o_group.isin(["detailed", "detail"])]
    assert a.tot_emp.notna().all() and len(a) == len(codes)
    total = float(d[(d.akey == "35620") & (d.o_group == "total")].tot_emp.iloc[0])
    ny[y] = {"jobs": float(a.tot_emp.sum()), "share": float(a.tot_emp.sum() / total)}
nyd = d25[(d25.akey == "35620") & (d25.o_group == "detailed")].sort_values("tot_emp", ascending=False)
ny["largest_2025"] = nyd.occ_title.iloc[0]; ny["second_2025"] = [nyd.occ_title.iloc[1], float(nyd.tot_emp.iloc[1])]
N["ny_aides"] = ny

# 4. change over time
t = pd.read_csv(os.path.join(INT, "history_tests.csv"), dtype={"akey": str})
chg = {}
for s in (2016, 2022):
    for typ, lab in ((2, "states"), (4, "metros")):
        g = t[(t.start == s) & (t.area_type == typ)]
        v = g.verdict.value_counts()
        chg[f"{lab}_{s}"] = {"n": int(len(g)), "narrowed": int(v.get("clear drop", 0)), "widened": int(v.get("clear rise", 0)),
                              "no_clear_change": int(v.get("no clear change", 0)),
                              "widened_names": g[g.verdict == "clear rise"].sort_values("ch_harm", ascending=False)[["area_title", "ch_harm"]].values.tolist()}
us_t = t[t.akey == "99"].set_index("start")
chg["us"] = {str(s): [float(us_t.loc[s, "g0"]), float(us_t.loc[s, "g1"]), us_t.loc[s, "verdict"]] for s in (2016, 2022)}
jobs = m25.total_emp
top25 = [k for k in jobs[m25.area_type == 4].sort_values(ascending=False).index][:25]
b25 = t[t.akey.isin(top25) & t.start.isin([2016, 2022])]
chg["largest25"] = {str(s): b25[b25.start == s].verdict.value_counts().to_dict() for s in (2016, 2022)}
chg["largest25_widened_2022"] = b25[(b25.start == 2022) & (b25.verdict == "clear rise")].area_title.tolist()
N["change"] = chg

# 5. IRS county income sources, tax year 2023 (counties with 100,000+ residents, BEA 2024 population)
s = pd.read_csv(os.path.join(ROOT, "data/raw/irs/23incyallnoagi.csv"), dtype={"STATEFIPS": str, "COUNTYFIPS": str}, encoding="latin1")
s["fips"] = s.STATEFIPS.str.zfill(2) + s.COUNTYFIPS.str.zfill(3)
cty = s[s.COUNTYFIPS.str.zfill(3) != "000"].copy()
z = zipfile.ZipFile(os.path.join(ROOT, "data/raw/bea/CAINC4.zip"))
b = pd.read_csv(z.open("CAINC4__ALL_AREAS_1969_2024.csv"), encoding="latin1", dtype=str)
b.columns = [c.strip() for c in b.columns]; b = b[b.LineCode.notna()]
b["fips"] = b.GeoFIPS.str.strip().str.strip('"').str.strip()
pop = pd.to_numeric(b[b.LineCode.str.strip() == "20"].set_index("fips")["2024"], errors="coerce")
c = cty[cty.fips.isin(set(pop[pop >= 100_000].index))].copy()
c["agi_per_return"] = c.A00100 * 1000 / c.N1
SRC = {"Wages": ["A00200"], "Capital gains": ["A01000"], "Dividends and interest": ["A00600", "A00300"],
       "Partnership and S corporation": ["A26270"], "Sole proprietor": ["A00900"]}
for k, cols in SRC.items(): c[k] = c[cols].sum(axis=1) / c.A02650
c["Everything else"] = 1 - c[list(SRC)].sum(axis=1)
top = c[c.agi_per_return >= c.agi_per_return.quantile(0.8)]
cols = list(SRC) + ["Everything else"]
N["county"] = {"n": int(len(c)), "n_top": int(len(top)),
               "median": {"agi_per_return": float(c.agi_per_return.median()), **{k: float(c[k].median()) for k in cols}},
               "top_fifth": {"agi_per_return": float(top.agi_per_return.median()), **{k: float(top[k].median()) for k in cols}},
               "named": {}}
for f, name in (("36061", "Manhattan (New York County), NY"), ("06041", "Marin County, CA"), ("09190", "Western Connecticut"),
                ("06037", "Los Angeles County, CA"), ("12021", "Collier County, FL")):
    r = c[c.fips == f].iloc[0]
    N["county"]["named"][name] = {"agi_per_return": float(r.agi_per_return), **{k: float(r[k]) for k in cols}}
# Pooled shares by county income fifth (all income in the fifth added up), so each bar sums to 100%
c["fifth"] = pd.qcut(c.agi_per_return, 5, labels=["Poorest fifth", "Second fifth", "Middle fifth", "Fourth fifth", "Richest fifth"])
pooled = {}
for q, g in c.groupby("fifth", observed=True):
    t_ = g[["A02650"] + sum(SRC.values(), [])].sum()
    sh = {k: float(t_[cols_].sum() / t_.A02650) for k, cols_ in SRC.items()}
    sh["Everything else"] = 1 - sum(sh.values())
    pooled[str(q)] = {"counties": int(len(g)), "agi_per_return_median": float(g.agi_per_return.median()), **sh}
N["county"]["pooled_fifths"] = pooled
allc = cty[["A02650", "A00200", "A01000"]].sum()
N["county"]["all_counties_check"] = {"wages": float(allc.A00200 / allc.A02650), "capital_gains": float(allc.A01000 / allc.A02650)}
N["county"]["investment_lines_median"] = float((c["Capital gains"] + c["Dividends and interest"] + c["Partnership and S corporation"]).median())
N["county"]["investment_lines_top_fifth"] = float((top["Capital gains"] + top["Dividends and interest"] + top["Partnership and S corporation"]).median())

with open(OUT, "w") as f:
    json.dump(N, f, indent=1, default=float)
print(json.dumps(N, indent=1, default=float)[:6000])
