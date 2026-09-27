"""History tests across non-overlapping OEWS years (no shared survey panels).

For each area and each start frame (-> May 2025):
  1. Geography: states and U.S. are fixed. Metros use the match and eligibility
     from 05_boundary_check.py (boundary change under 2% of jobs, or an old
     boundary rebuilt in 2025 that moves the Gini less than 0.002).
  2. Noise: change must exceed 2 x combined SD from the RSE-based draws, plus
     an allowance for the May 2021 method change (0.005, states and metros,
     spans that cross 2021) and for any boundary rebuild effect.
  3. Suppression: recompute both years on harmonized groups published in BOTH
     years for that area ("common set"); the direction of change must agree.
  4. Grouping: harmonized change must agree in direction with native change.
Verdict: "clear drop" / "clear rise" if all pass, else "no clear change".
Run 05_boundary_check.py first.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import gini, harmonize
from geo import area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data/interim")
FRAMES = [2013, 2016, 2019, 2022, 2025]
METHOD_ALLOWANCE = 0.005

cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))[["year", "occ_code", "hgroup"]].drop_duplicates()
metrics = pd.read_parquet(os.path.join(INT, "area_metrics.parquet"))
metrics["akey"] = area_key(metrics.area)
bound = pd.read_csv(os.path.join(INT, "metro_boundary_check.csv"), dtype={"area": str, "match_area": str})
H = {}
for y in FRAMES:
    d = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet"))
    h = harmonize(d[d.area_type.isin([1, 2, 4])], cmap); h["akey"] = area_key(h.area); H[y] = h

# (start, 2025 area, start-year area, boundary rebuild effect)
pairs = []
m25 = metrics[metrics.year == 2025].set_index("akey")
for y0 in FRAMES[:-1]:
    for ak in m25.index[m25.area_type.isin([1, 2])]:
        pairs.append((y0, ak, ak, 0.0, 0.0))
    for _, b in bound[(bound.start == y0) & bound.eligible].iterrows():
        pairs.append((y0, b.area, b.match_area, abs(np.nan_to_num(b.rebuild_effect)), b.change_share))

rows = []
for y0, ak, ak0, rebuild, bshare in pairs:
    m0 = metrics[(metrics.year == y0) & (metrics.akey == ak0)]
    if m0.empty: continue
    m0, m1 = m0.iloc[0], m25.loc[ak]
    a0, a1 = H[y0][H[y0].akey == ak0], H[2025][H[2025].akey == ak]
    common = set(a0.hgroup) & set(a1.hgroup)
    c0, c1 = a0[a0.hgroup.isin(common)], a1[a1.hgroup.isin(common)]
    ch_harm = m1.gini_harm - m0.gini_harm
    allowance = (METHOD_ALLOWANCE if (y0 < 2021 and m1.area_type != 1) else 0) + rebuild
    sd = np.hypot(m0.gini_sd, m1.gini_sd)
    rows.append(dict(start=y0, akey=ak, start_area=ak0, area_title=m1.area_title, area_type=int(m1.area_type),
                     boundary_change=bshare, rebuild_effect=rebuild, cov0=m0.coverage, cov1=m1.coverage,
                     g0=m0.gini_harm, g1=m1.gini_harm, g0_native=m0.gini, g1_native=m1.gini,
                     ch_native=m1.gini - m0.gini, ch_harm=ch_harm,
                     ch_common=gini(c1.tot_emp, c1.a_mean) - gini(c0.tot_emp, c0.a_mean),
                     sd=sd, allowance=allowance))
r = pd.DataFrame(rows)
assert not r.duplicated(["start", "akey"]).any(), "duplicate area pairing"
r["clears_noise"] = r.ch_harm.abs() > 2 * r.sd + r.allowance
r["common_agrees"] = np.sign(r.ch_harm) == np.sign(r.ch_common)
r["native_agrees"] = np.sign(r.ch_harm) == np.sign(r.ch_native)
ok = r.clears_noise & r.common_agrees & r.native_agrees
r["verdict"] = np.where(ok, np.where(r.ch_harm < 0, "clear drop", "clear rise"), "no clear change")
r.to_csv(os.path.join(INT, "history_tests.csv"), index=False)

T = {1: "U.S.", 2: "states", 4: "metros"}
for (y0, t), g in r.groupby(["start", "area_type"]):
    v = g.verdict.value_counts()
    print(f"{y0}->2025 {T[t]:7s} n={len(g):3d} | clear drop {v.get('clear drop', 0):3d} | clear rise {v.get('clear rise', 0):3d}"
          f" | no clear change {v.get('no clear change', 0):3d} | median change {g.ch_harm.median():+.4f}")
