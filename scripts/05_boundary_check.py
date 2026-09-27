"""How much did each metro's boundary change between a frame year and May 2025?

Jobs by county come from QCEW 2024 annual averages (all ownerships, all
industries). For each 2025 metro, the frame-year metro sharing the most jobs is
its match (this also catches renumbered metros). Boundary change = jobs in
counties inside one definition but not the other, divided by jobs in the union.
A metro is eligible for history against that frame if the change is under 2%.

Counties QCEW cannot measure make a metro unmeasurable (and so ineligible):
New England towns where the county is split between areas, and Connecticut's
old counties (QCEW now reports Connecticut by planning region).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import definitions, area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data/interim")
THRESHOLD = 0.02
# County-equivalents renamed or split since 2016, mapped to their current codes.
RENAMED = {"02261": ["02063", "02066"],   # Valdez-Cordova split, 2019
           "46113": ["46102"],            # Shannon County renamed Oglala Lakota, 2015
           "51515": ["51019"],            # Bedford city merged into Bedford County, 2013
           "12025": ["12086"]}            # Dade County recoded as Miami-Dade, 1997 (still 12025 in the 2016 list)
NO_PAYROLL = {"15005"}                    # Kalawao County, HI: not published in QCEW; population under 100

q = pd.read_csv(os.path.join(ROOT, "data/raw/qcew/qcew_2024_annual_industry10.csv"),
                dtype={"area_fips": str, "own_code": str})
q = q[(q.own_code == "0") & q.area_fips.str.match(r"^\d{5}$") & ~q.area_fips.str.endswith("000")]
JOBS = dict(zip(q.area_fips, q.annual_avg_emplvl))


def county_jobs(c):
    if c in JOBS: return JOBS[c]
    if c in NO_PAYROLL: return 0
    if c in RENAMED and all(r in JOBS for r in RENAMED[c]): return sum(JOBS[r] for r in RENAMED[c])
    return np.nan


def metro_units(year):
    """area -> set of whole counties, plus a flag if any part-county town makes it unmeasurable."""
    d = definitions(year)
    towns = d[d.town != "00000"]
    split = towns.groupby("county").area.nunique()
    split = set(split[split > 1].index)                     # county divided between areas
    metros = set(area_key(pd.read_parquet(os.path.join(INT, f"oews_{year}.parquet"), columns=["area", "area_type"])
                          .query("area_type == 4").area))
    d = d[d.area.isin(metros)]
    units = d.groupby("area").county.apply(frozenset)
    partial = d[d.county.isin(split)].groupby("area").size().index
    return units, set(partial)


u25, p25 = metro_units(2025)
titles = (pd.read_parquet(os.path.join(INT, "oews_2025.parquet"), columns=["area", "area_title"])
          .drop_duplicates().assign(area=lambda x: area_key(x.area)).set_index("area").area_title)
rows = []
for y0 in (2016, 2019, 2022):
    u0, p0 = metro_units(y0)
    for a, c25 in u25.items():
        best, best_shared = None, -1
        for o, c0 in u0.items():
            shared = sum(county_jobs(c) for c in c25 & c0 if not np.isnan(county_jobs(c)))
            if shared > best_shared: best, best_shared = o, shared
        c0 = u0[best]
        union = c25 | c0
        jobs = {c: county_jobs(c) for c in union}
        unmeasured = [c for c, j in jobs.items() if np.isnan(j)]
        measurable = not unmeasured and a not in p25 and best not in p0
        diff = sum(jobs[c] for c in c25 ^ c0 if not np.isnan(jobs[c]))
        tot = sum(j for j in jobs.values() if not np.isnan(j))
        rows.append(dict(start=y0, area=a, area_title=titles.get(a), match_area=best, same_code=(best == a),
                         identical=(c25 == c0), counties_added=len(c25 - c0), counties_dropped=len(c0 - c25),
                         change_share=diff / tot if tot else np.nan, measurable=measurable,
                         unmeasured_counties=";".join(unmeasured),
                         eligible=measurable and diff / tot < THRESHOLD))
r = pd.DataFrame(rows)
r.to_csv(os.path.join(INT, "metro_boundary_check.csv"), index=False)
for y0, g in r.groupby("start"):
    print(f"{y0}->2025: {len(g)} metros | identical counties {g.identical.sum()} | measurable {g.measurable.sum()} "
          f"| change < 2%: {g.eligible.sum()} | renumbered matches {(~g.same_code).sum()}")
big = r[(r.start == 2016) & r.area_title.str.contains(
    "New York|Los Angeles|Chicago|Dallas|Houston|Washington-Arl|Philadelphia|Miami|Atlanta|Boston|Phoenix|San Francisco|Seattle|Detroit|Minneapolis")]
print(big[["area_title", "match_area", "counties_added", "counties_dropped", "change_share", "measurable", "eligible"]]
      .round(4).to_string(index=False))


# Second pass: rebuild the old boundary in 2025 for metros that failed only
# because they lost counties that now form whole other 2025 areas (e.g. New York
# lost Dutchess and Orange to Kiryas Joel-Poughkeepsie-Newburgh). Merge those
# areas' occupations back in and measure how much the 2025 Gini moves. If it
# moves less than MAX_EFFECT and the leftover (unrebuilt) jobs are under 0.5%,
# the metro is eligible, with the effect recorded and shown.
from lorenz import gini, harmonize
MAX_EFFECT, MAX_LEFTOVER = 0.002, 0.005
d25 = definitions(2025)
home = d25.drop_duplicates("county").set_index("county").area          # county -> 2025 area
area_counties = d25.groupby("area").county.apply(frozenset)
cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))[["year", "occ_code", "hgroup"]].drop_duplicates()
H25 = harmonize(pd.read_parquet(os.path.join(INT, "oews_2025.parquet")), cmap)
H25["akey"] = area_key(H25.area)
r["rebuild_areas"], r["rebuild_effect"], r["leftover_share"] = "", np.nan, np.nan
for i, row in r[r.measurable & ~r.eligible].iterrows():
    y0 = row.start
    c0 = metro_units(y0)[0][row.match_area]; c25 = u25[row.area]
    if c25 - c0:                                   # gained counties: cannot rebuild by merging
        continue
    dropped = c0 - c25
    receivers = {home.get(c) for c in dropped if c in home.index}
    whole = {a for a in receivers if a and area_counties[a] <= dropped}
    rebuilt = set().union(*[area_counties[a] for a in whole]) if whole else set()
    union_jobs = sum(county_jobs(c) for c in c25 | c0)
    leftover = sum(county_jobs(c) for c in dropped - rebuilt) / union_jobs
    if not whole: continue
    parts = H25[H25.akey.isin({row.area} | whole)]
    merged = parts.groupby("hgroup", as_index=False)[["tot_emp", "wages"]].sum()
    now = H25[H25.akey == row.area]
    effect = gini(merged.tot_emp, merged.wages / merged.tot_emp) - gini(now.tot_emp, now.wages / now.tot_emp)
    r.loc[i, ["rebuild_areas", "rebuild_effect", "leftover_share"]] = [";".join(sorted(whole)), effect, leftover]
    if abs(effect) < MAX_EFFECT and leftover < MAX_LEFTOVER:
        r.loc[i, "eligible"] = True
r.to_csv(os.path.join(INT, "metro_boundary_check.csv"), index=False)
print("\nAfter rebuilding old boundaries:")
for y0, g in r.groupby("start"):
    print(f"{y0}->2025: eligible {g.eligible.sum()} of {len(g)} | rebuilt and passed {(g.rebuild_areas.ne('') & g.eligible).sum()}"
          f" | rebuilt and failed {(g.rebuild_areas.ne('') & ~g.eligible).sum()}")
x = r[(r.start == 2016) & r.rebuild_areas.ne("")]
print(x[["area_title", "change_share", "rebuild_effect", "leftover_share", "eligible"]].round(4).to_string(index=False))
