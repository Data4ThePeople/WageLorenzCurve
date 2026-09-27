"""Tie-out: every number the page shows is recomputed two ways and compared.

1. Reproduction of the published post (May 2024): NY metro Gini 0.3148 and the
   California example (lowest-paid 40.2% of workers earn 21.7% of wages).
2. The page's own math (src/core.js, run under macOS jsc on data/build/lorenz.json)
   vs. an independent Python computation from the parquet files, for every
   place: Gini, lowest-paid-half share, top-10% share, average wage (May 2025),
   and the harmonized Gini for every history frame.
3. Headline numbers for the post.
"""
import json, os, subprocess, sys, tempfile
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import gini, usable, harmonize
from geo import area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data/interim")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
TOL = 1e-6


def curve(emp, mean):
    o = np.argsort(np.asarray(mean, float), kind="stable")
    e, w = np.asarray(emp, float)[o], np.asarray(emp, float)[o] * np.asarray(mean, float)[o]
    return np.r_[0, np.cumsum(e) / e.sum()], np.r_[0, np.cumsum(w) / w.sum()], w.sum() / e.sum()


def share_at(x, y, p):
    return float(np.interp(p, x, y))


print("1. Reproduction of the February 4, 2026 post (May 2024)")
d24 = pd.read_parquet(os.path.join(INT, "oews_2024.parquet"))
ny = usable(d24[d24.area == "35620"]); ca = usable(d24[d24.area_title == "California"])
g_ny = gini(ny.tot_emp, ny.a_mean); x, y, _ = curve(ca.tot_emp, ca.a_mean)
i = int(np.argmin(abs(x - 0.402)))
print(f"   NY metro Gini {g_ny:.4f} (published 0.3148) -> {'PASS' if round(g_ny, 4) == 0.3148 else 'FAIL'}")
print(f"   California point {x[i]*100:.1f}% of workers, {y[i]*100:.1f}% of wages (published 40.2% / 21.7%) -> "
      f"{'PASS' if (round(x[i]*100,1), round(y[i]*100,1)) == (40.2, 21.7) else 'FAIL'}")

print("2. Page math (jsc) vs Python, every place")
js = r"""
load('%s');
const D = JSON.parse(read('%s'));
const out = {latest:{}, hist:{}};
for (const a of D.areas) { const c = lorenz(latestRows(D, a.id)); out.latest[a.id] = readouts(c); }
for (const id in D.history) { out.hist[id] = {};
  for (const y of D.meta.frames) if (y === D.meta.latest_year || D.history[id][String(y)]) out.hist[id][y] = lorenz(historyRows(D, id, y)).gini; }
print(JSON.stringify(out));
""" % (os.path.join(ROOT, "src/core.js"), os.path.join(ROOT, "data/build/lorenz.json"))
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(js)
J = json.loads(subprocess.run([JSC, f.name], capture_output=True, text=True, check=True).stdout)

d25 = pd.read_parquet(os.path.join(INT, "oews_2025.parquet")); d25["akey"] = area_key(d25.area)
cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))[["year", "occ_code", "hgroup"]].drop_duplicates()
diffs = {"gini": 0, "bottomHalf": 0, "top10": 0, "avgWage": 0}
for ak, a in d25.groupby("akey"):
    u = usable(a)
    if not len(u): continue
    x, y, avg = curve(u.tot_emp, u.a_mean)
    py = {"gini": gini(u.tot_emp, u.a_mean), "bottomHalf": share_at(x, y, 0.5), "top10": 1 - share_at(x, y, 0.9), "avgWage": avg}
    for k in diffs:
        diffs[k] = max(diffs[k], abs(J["latest"][ak][k] - py[k]) / (py[k] if k == "avgWage" else 1))
print(f"   {len(J['latest'])} places, May 2025: max difference Gini {diffs['gini']:.2e}, lowest-half share {diffs['bottomHalf']:.2e},"
      f" top-10% share {diffs['top10']:.2e}, average wage (relative) {diffs['avgWage']:.2e}")
tests = pd.read_csv(os.path.join(INT, "history_tests.csv"), dtype={"akey": str, "start_area": str})
metrics = pd.read_parquet(os.path.join(INT, "area_metrics.parquet")); metrics["akey"] = area_key(metrics.area)
hd, n = 0, 0
for _, t in tests.iterrows():
    hd = max(hd, abs(J["hist"][t.akey][str(t.start)] - t.g0), abs(J["hist"][t.akey]["2025"] - t.g1)); n += 2
print(f"   {len(J['hist'])} places with history, {n} frame values: max difference harmonized Gini {hd:.2e}")
ok = max(diffs["gini"], diffs["bottomHalf"], diffs["top10"], hd) < TOL and diffs["avgWage"] < 1e-9
print("   ->", "PASS" if ok else "FAIL")

print("2a. Top 10% vs. median readout: exported percentiles vs. BLS all-occupation rows")
D0 = json.load(open(os.path.join(ROOT, "data/build/lorenz.json")))
bad, n = 0, 0
tot25 = d25[d25.o_group == "total"].set_index("akey")
for a in D0["areas"]:
    r = tot25.loc[a["id"]]; n += 1
    bad += int((a["p10"], a["p50"], a["p90"]) != (int(r.a_pct10), int(r.a_median), int(r.a_pct90)))
for ak, fr in D0["history"].items():
    for y, F in fr.items():
        t = tests[(tests.akey == ak) & (tests.start == int(y))].iloc[0]
        dd = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet"), columns=["area", "o_group", "a_median", "a_pct90"])
        rr = dd[(dd.o_group == "total") & (area_key(dd.area) == t.start_area)].iloc[0]; n += 1
        bad += int((F["p50"], F["p90"]) != (int(rr.a_median), int(rr.a_pct90)))
print(f"   {n} place-years checked; mismatches {bad} -> {'PASS' if bad == 0 else 'FAIL'}")
us = tot25.loc["99"]; print(f"   U.S. May 2025: top-10% line ${us.a_pct90:,.0f}, median ${us.a_median:,.0f}, {us.a_pct90/us.a_median-1:.0%} higher")

print("2b. Income by source (BEA): export vs BEA's own U.S. and state rows")
import zipfile
z = zipfile.ZipFile(os.path.join(ROOT, "data/raw/bea/CAINC4.zip"))
b = pd.read_csv(z.open("CAINC4__ALL_AREAS_1969_2024.csv"), encoding="latin1", dtype=str); b.columns = [c.strip() for c in b.columns]
b = b[b.LineCode.notna()]; b["fips"] = b.GeoFIPS.str.strip().str.strip('"').str.strip(); b["line"] = b.LineCode.str.strip()
D = json.load(open(os.path.join(ROOT, "data/build/lorenz.json")))
worst, checked = 0, 0
for a in D["areas"]:
    if a["type"] not in ("U.S.", "State") or not a["income"]: continue
    f = "00000" if a["type"] == "U.S." else a["id"].zfill(2) + "000"
    for y, vals in a["income"].items():
        for line, v in zip(["10", "50", "60", "70", "46", "47"], vals):
            src = float(b[(b.fips == f) & (b.line == line)][y].iloc[0])
            worst = max(worst, abs(src - v)); checked += 1
print(f"   {checked} values checked; max difference {worst:.0f} thousand dollars -> {'PASS' if worst <= 1 else 'FAIL'}")
us_inc = [a for a in D["areas"] if a["type"] == "U.S."][0]["income"]
for y in ("2013", "2024"):
    v = us_inc[y]; print(f"   U.S. {y}: wages {v[1]/v[0]:.1%}, employer benefits {v[2]/v[0]:.1%}, business owners {v[3]/v[0]:.1%}, dividends/interest/rent {v[4]/v[0]:.1%}, transfers {v[5]/v[0]:.1%}")

print("2c. IRS income by source (post chart): recomputed from the IRS file by scripts/10_irs_income_sources.py")
irs = pd.read_csv(os.path.join(ROOT, "data/build/irs_income_sources_2023.csv")).set_index("bracket")
t = irs.loc["$10 million or more"]
print(f"   $10M+ wages {t['Wages']*100:.1f}%; capital gains + dividends/interest + partnership/S corp "
      f"{(t['Capital gains'] + t['Dividends and interest'] + t['Partnership and S corporation'])*100:.1f}%; "
      f"all returns wages {irs.loc['All returns', 'Wages']*100:.1f}%  (post cites 17.0%, 76.4%, 66.1%)")

print("3. Headline numbers")
L = J["latest"]; A = {a: t for a, t in zip(d25.akey, d25.area_title)}
TY = dict(zip(d25.akey, d25.area_type))
us = [k for k, v in TY.items() if v == 1][0]
print(f"   U.S. May 2025: Gini {L[us]['gini']:.4f}; lowest-paid half earn {L[us]['bottomHalf']:.1%}; top-paid 10% earn {L[us]['top10']:.1%}; avg wage ${L[us]['avgWage']:,.0f}")
for t, name in ((2, "states"), (4, "metro areas"), (6, "nonmetro areas")):
    ks = sorted([k for k, v in TY.items() if v == t], key=lambda k: L[k]["gini"])
    print(f"   {name}: most equal {A[ks[0]]} {L[ks[0]]['gini']:.4f}; least equal {A[ks[-1]]} {L[ks[-1]]['gini']:.4f}")
us_t = tests[(tests.akey == us)].set_index("start")
for s0 in (2013, 2016):
    print(f"   U.S. harmonized Gini May {s0} {us_t.loc[s0, 'g0']:.4f} -> May 2025 {us_t.loc[s0, 'g1']:.4f} ({us_t.loc[s0, 'ch_harm']:+.4f}), {us_t.loc[s0, 'verdict']}")
for (s0, t), g in tests[tests.area_type.isin([2, 4])].groupby(["start", "area_type"]):
    v = g.verdict.value_counts()
    print(f"   {s0}->2025 {'states' if t == 2 else 'metros'}: {len(g)} places, clear drop {v.get('clear drop', 0)}, clear rise {v.get('clear rise', 0)}, no clear change {v.get('no clear change', 0)}")
