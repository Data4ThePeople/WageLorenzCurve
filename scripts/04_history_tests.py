"""History tests across non-overlapping OEWS years (no shared survey panels).

For each area and each pair of frame years (start -> 2025):
  1. Geography: metros must have the identical set of counties/towns in both years.
  2. Noise: change must exceed 2 x combined SD from the RSE-based draws.
  3. Suppression: recompute both years on harmonized groups published in BOTH
     years for that area ("common set"); the direction of change must agree.
  4. Grouping: harmonized change must agree in direction with native change.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import gini, harmonize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT, REF = os.path.join(ROOT, "data/interim"), os.path.join(ROOT, "data/ref")
FRAMES = [2013, 2016, 2019, 2022, 2025]
DEF_FILE = {2016: "area_definitions_m2016.xlsx", 2019: "area_definitions_m2019.xlsx",
            2022: "area_definitions_m2022.xlsx", 2025: "area_definitions_m2024.xlsx"}


def county_sets(year):
    d = pd.read_excel(os.path.join(REF, DEF_FILE[year]), dtype=str)
    d.columns = [c.strip() for c in d.columns]
    code = next(c for c in d.columns if c.startswith("MSA code (incl") or c.endswith("MSA code") or c == "new_area")
    div_parent = "MSA code for MSAs with divisions"
    area = d[code].str.strip()
    if div_parent in d.columns:          # 2016 lists divisions; roll up to the full MSA code
        area = d[div_parent].fillna(area).str.strip()
    twp = d["Township code"] if "Township code" in d.columns else "000"
    fips = d["FIPS code"] if "FIPS code" in d.columns else d["FIPS"]
    key = fips.str.zfill(2) + d["County code"].str.zfill(3) + pd.Series(twp, index=d.index).astype(str).str.zfill(5)
    return pd.DataFrame({"area": area.str.lstrip("0"), "key": key}).groupby("area").key.apply(frozenset)


def area_key(s):
    return s.astype(str).str.strip().str.lstrip("0")


cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))[["year", "occ_code", "hgroup"]].drop_duplicates()
metrics = pd.read_parquet(os.path.join(INT, "area_metrics.parquet"))
metrics["akey"] = area_key(metrics.area)
H = {}
for y in FRAMES:
    d = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet"))
    d = d[d.area_type.isin([1, 2, 4])]
    h = harmonize(d, cmap); h["akey"] = area_key(h.area); H[y] = h
defs = {y: county_sets(y) for y in DEF_FILE}

rows = []
for y0 in FRAMES[:-1]:
    y1 = 2025
    m0 = metrics[metrics.year == y0].set_index("akey"); m1 = metrics[metrics.year == y1].set_index("akey")
    for ak in m1.index.intersection(m0.index):
        t = m1.loc[ak, "area_type"]
        if t not in (1, 2, 4) or m0.loc[ak, "area_type"] != t:
            continue
        if t == 4:
            if y0 not in defs: continue
            same_geo = ak in defs[y0] and ak in defs[y1] and defs[y0][ak] == defs[y1][ak]
        else:
            same_geo = True
        a0, a1 = H[y0][H[y0].akey == ak], H[y1][H[y1].akey == ak]
        common = set(a0.hgroup) & set(a1.hgroup)
        c0, c1 = a0[a0.hgroup.isin(common)], a1[a1.hgroup.isin(common)]
        ch_native = m1.loc[ak, "gini"] - m0.loc[ak, "gini"]
        ch_harm = m1.loc[ak, "gini_harm"] - m0.loc[ak, "gini_harm"]
        ch_common = gini(c1.tot_emp, c1.a_mean) - gini(c0.tot_emp, c0.a_mean)
        sd = np.hypot(m0.loc[ak, "gini_sd"], m1.loc[ak, "gini_sd"])
        rows.append(dict(start=y0, akey=ak, area_title=m1.loc[ak, "area_title"], area_type=t, same_geo=same_geo,
                         cov0=m0.loc[ak, "coverage"], cov1=m1.loc[ak, "coverage"],
                         common_emp_share0=c0.tot_emp.sum() / m0.loc[ak, "total_emp"],
                         common_emp_share1=c1.tot_emp.sum() / m1.loc[ak, "total_emp"],
                         g0=m0.loc[ak, "gini_harm"], g1=m1.loc[ak, "gini_harm"],
                         ch_native=ch_native, ch_harm=ch_harm, ch_common=ch_common, sd=sd))
r = pd.DataFrame(rows)
r["clears_noise"] = r.ch_harm.abs() > 2 * r.sd
r["common_agrees"] = np.sign(r.ch_harm) == np.sign(r.ch_common)
r["native_agrees"] = np.sign(r.ch_harm) == np.sign(r.ch_native)
r["common_gap"] = (r.ch_common - r.ch_harm).abs()
r.to_csv(os.path.join(INT, "history_tests.csv"), index=False)

pd.set_option("display.width", 250)
T = {1: "U.S.", 2: "state", 4: "metro"}
for (y0, t), g in r.groupby(["start", "area_type"]):
    if t == 4: g_all, g = g, g[g.same_geo]
    print(f"{y0}->2025 {T[t]:6s} n={len(g):3d}" + (f" (of {len(g_all)} metros; {len(g)} same counties)" if t == 4 else "") +
          f" | median change {g.ch_harm.median():+.4f} | fell {(g.ch_harm < 0).mean():.0%}"
          f" | clears 2SD {g.clears_noise.mean():.0%} | common-set agrees {g.common_agrees.mean():.0%}"
          f" | native agrees {g.native_agrees.mean():.0%} | all 3 pass {(g.clears_noise & g.common_agrees & g.native_agrees).mean():.0%}"
          f" | median |common-harm| {g.common_gap.median():.4f}")
