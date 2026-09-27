"""Export the data the viz needs to data/build/lorenz.json (columnar, integers).

latest  : May 2025, native detailed occupations, Eric's method (rows with both
          TOT_EMP and A_MEAN). Per area: occupation index, jobs, mean wage.
history : harmonized groups for 2013/2016/2019/2022 (2025 is rebuilt in the
          browser by summing latest rows into groups via occ -> group index).
          U.S. and states: all four frames. Metros: frames where eligible
          (05_boundary_check.py), using the matched frame-year area.
No Gini or share is stored for display; the page recomputes everything. Stored
reference Ginis are only for the tie-out.
"""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import usable, harmonize
from geo import area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT, OUT = os.path.join(ROOT, "data/interim"), os.path.join(ROOT, "data/build")
TYPES = {1: "U.S.", 2: "State", 3: "Territory", 4: "Metro area", 6: "Nonmetro area"}

d25 = pd.read_parquet(os.path.join(INT, "oews_2025.parquet"))
d25["akey"] = area_key(d25.area)
cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))
metrics = pd.read_parquet(os.path.join(INT, "area_metrics.parquet")); metrics["akey"] = area_key(metrics.area)
tests = pd.read_csv(os.path.join(INT, "history_tests.csv"), dtype={"akey": str, "start_area": str})
bound = pd.read_csv(os.path.join(INT, "metro_boundary_check.csv"), dtype={"area": str, "match_area": str})

# Major groups (22) from the 2025 major rows
maj = d25[d25.o_group == "major"].drop_duplicates("occ_code")
majors = sorted(zip(maj.occ_code.str[:2], maj.occ_title))
major_idx = {m: i for i, (m, _) in enumerate(majors)}

# Harmonized groups; color a merged group by the major group holding most U.S. jobs in 2025
hg = cmap[["hgroup", "hgroup_title"]].drop_duplicates("hgroup").sort_values("hgroup").reset_index(drop=True)
hg_idx = {h: i for i, h in enumerate(hg.hgroup)}
us25 = usable(d25[d25.area_type == 1]).merge(cmap[cmap.year == 2025][["occ_code", "hgroup"]], on="occ_code")
def group_major(h):
    rows = us25[us25.hgroup == h]
    code = rows.sort_values("tot_emp").occ_code.iloc[-1] if len(rows) else h.split("+")[0]
    return major_idx[code[:2]]
groups = [{"codes": h.split("+"), "title": t, "major": group_major(h)} for h, t in zip(hg.hgroup, hg.hgroup_title)]

# Occupations (2025 native detailed)
u = usable(d25)
occ = u.drop_duplicates("occ_code")[["occ_code", "occ_title"]].sort_values("occ_code").reset_index(drop=True)
occ_idx = {c: i for i, c in enumerate(occ.occ_code)}
c25 = cmap[cmap.year == 2025].set_index("occ_code").hgroup
occs = [{"code": c, "title": t, "major": major_idx[c[:2]], "group": hg_idx[c25[c]]} for c, t in zip(occ.occ_code, occ.occ_title)]

areas, latest = [], {}
for ak, a in d25.groupby("akey"):
    first = a.iloc[0]
    tot = a.loc[a.o_group == "total", "tot_emp"].iloc[0]
    ua = usable(a)
    if len(ua) == 0: continue
    det = a[a.o_group == "detailed"]
    m = metrics[(metrics.year == 2025) & (metrics.akey == ak)].iloc[0]
    areas.append({"id": ak, "title": first.area_title, "type": TYPES[int(first.area_type)],
                  "state": first.prim_state, "total_jobs": int(tot),
                  "jobs_topcoded": int(det.loc[det.a_mean_flag == "#", "tot_emp"].sum()),
                  "jobs_no_wage": int(det.loc[det.a_mean.isna() & (det.a_mean_flag != "#"), "tot_emp"].sum()),
                  "gini_sd": round(float(m.gini_sd), 5), "ref_gini": round(float(m.gini), 6),
                  # BLS all-occupation wage percentiles (annual): 10th, median, 90th
                  "p10": int(a.loc[a.o_group == "total", "a_pct10"].iloc[0]),
                  "p50": int(a.loc[a.o_group == "total", "a_median"].iloc[0]),
                  "p90": int(a.loc[a.o_group == "total", "a_pct90"].iloc[0])})
    key = list(zip(ua.occ_code, ua.tot_emp))
    assert ua.occ_code.is_unique, f"duplicate occupation in area {ak}"
    latest[ak] = {"o": [occ_idx[c] for c in ua.occ_code], "e": ua.tot_emp.astype(int).tolist(),
                  "w": ua.a_mean.round().astype(int).tolist()}
assert len({a["id"] for a in areas}) == len(areas), "duplicate area id"

# History frames
history = {}
frames_by_area = {}
for _, t in tests.iterrows():
    frames_by_area.setdefault(t.akey, {})[int(t.start)] = t
PCT = {}
H = {}
for y in (2013, 2016, 2019, 2022):
    dy = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet"))
    h = harmonize(dy[dy.area_type.isin([1, 2, 4])], cmap); h["akey"] = area_key(h.area); H[y] = h
    tot = dy[dy.o_group == "total"].assign(akey=lambda x: area_key(x.area))
    PCT[y] = tot.set_index("akey")[["a_median", "a_pct90"]]
for ak, starts in frames_by_area.items():
    fr = {}
    for y, t in sorted(starts.items()):
        rows = H[y][H[y].akey == t.start_area]
        assert rows.hgroup.is_unique, f"duplicate group {ak} {y}"
        mt = metrics[(metrics.year == y) & (metrics.akey == t.start_area)].iloc[0]
        fr[str(y)] = {"g": [hg_idx[x] for x in rows.hgroup], "e": rows.tot_emp.round().astype(int).tolist(),
                      "t": rows.wages.round().astype(int).tolist(),   # total wages; the page divides by jobs
                      "area_title": mt.area_title, "total_jobs": int(mt.total_emp),
                      "gini_sd": round(float(mt.gini_sd), 5), "ref_gini_harm": round(float(t.g0), 6),
                      "verdict_to_2025": t.verdict, "change_to_2025": round(float(t.ch_harm), 5),
                      "noise_to_2025": round(float(2 * t.sd + t.allowance), 5),
                      "boundary_change": None if pd.isna(t.boundary_change) or t.area_type != 4 else round(float(t.boundary_change), 4),
                      "rebuild_effect": round(float(t.rebuild_effect), 4),
                      "p50": int(PCT[y].loc[t.start_area, "a_median"]), "p90": int(PCT[y].loc[t.start_area, "a_pct90"])}
    history[ak] = fr

# Why a place has no history (shown when the History view is unavailable)
b16 = bound[bound.start == 2016].set_index("area")
for a in areas:
    if a["id"] in history: a["hist_note"] = None; continue
    if a["type"] == "Nonmetro area":
        a["hist_note"] = "BLS redrew nonmetro areas in 2018 and 2024, so earlier years cover different counties."
    elif a["type"] == "Territory":
        a["hist_note"] = "Territories are shown for May 2025 only."
    elif a["id"] in b16.index:
        b = b16.loc[a["id"]]
        if not b.measurable:
            a["hist_note"] = ("Its boundaries changed between 2016 and 2025, and the change cannot be measured "
                              "(New England towns and Connecticut's old counties are not in the county job counts).")
        elif b.change_share > 0.5:
            a["hist_note"] = "This metro area was created or split off from a larger one after 2016, so there is no earlier version to compare."
        else:
            a["hist_note"] = (f"Its boundaries changed between 2016 and 2025: {b.change_share:.1%} of jobs are in counties "
                              "that were added or removed, above our 2% limit.")
    else:
        a["hist_note"] = "Not enough comparable data for earlier years."

# Personal income by source (BEA), shares computed in the page. Thousands of dollars.
inc = pd.read_csv(os.path.join(INT, "bea_income_by_area.csv"), dtype={"area": str})
INC_COLS = ["personal_income", "wages", "supplements", "proprietors", "dividends_interest_rent", "transfers"]
for a in areas:
    rows = inc[(inc.area == a["id"]) & inc.complete]
    a["income"] = {str(r.year): [int(round(r[c] / 1000)) for c in INC_COLS] for _, r in rows.iterrows()} or None

# California: OEWS counts of home health and personal care aides jumped between May 2016
# and May 2017 (170,220 -> 545,840 statewide), very likely when In-Home Supportive Services
# caregivers began to be counted. Shown in the change-over-time view for California places
# whose history starts before 2017. Verdicts hold without the aide group (see DATASETS.md).
for a in areas:
    a["hist_caveat"] = None
    if a["id"] in history and (a["title"] == "California" or a["title"].endswith(", CA")) and min(int(y) for y in history[a["id"]]) < 2017:
        a["hist_caveat"] = ("California: BLS counts of home health and personal care aides rose 221% between May 2016 and May 2017, "
                            "very likely because caregivers paid through the state\u2019s In-Home Supportive Services program began to be counted. "
                            "That bubble\u2019s growth here is partly a counting change. The verdict above holds with that group left out.")

out = {"meta": {"latest_year": 2025, "frames": [2013, 2016, 2019, 2022, 2025],
                "source": "U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics, May 2013-May 2025",
                "income_cols": ["personal_income", "wages", "supplements", "proprietors", "dividends_interest_rent", "transfers"],
                "income_years": [2013, 2016, 2019, 2022, 2024],
                "ref_gini_harm_2025": {ak: round(float(metrics[(metrics.year == 2025) & (metrics.akey == ak)].gini_harm.iloc[0]), 6)
                                       for ak in history}},
       "majors": [{"code": m, "title": t} for m, t in majors], "groups": groups, "occs": occs,
       "areas": areas, "latest": latest, "history": history}
path = os.path.join(OUT, "lorenz.json")
with open(path, "w") as f:
    json.dump(out, f, separators=(",", ":"))
print(f"{len(areas)} areas, {len(occs)} occupations, {len(groups)} groups, {len(majors)} major groups,"
      f" {len(history)} areas with history; {os.path.getsize(path)/1e6:.1f} MB")
