"""Personal income by source for every OEWS area (BEA CAINC4, 2013-2024).

Context for what the Lorenz curve cannot see. Counties are summed into the
OEWS May 2024 area definitions (used for May 2025), so boundaries match the
OEWS areas exactly. U.S. and states use BEA's own rows.

BEA combines some Virginia independent cities with a county, and Maui with
Kalawao; a combination is assigned to an area only when every piece lies in
that area. An area's value for a year is reported only if every one of its
counties has a published value that year.
"""
import os, re, sys, zipfile
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import definitions, area_key

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT, REF = os.path.join(ROOT, "data/interim"), os.path.join(ROOT, "data/ref")
YEARS = ["2013", "2016", "2019", "2022", "2024"]
LINES = {"10": "personal_income", "50": "wages", "60": "supplements", "70": "proprietors",
         "46": "dividends_interest_rent", "47": "transfers"}

z = zipfile.ZipFile(os.path.join(ROOT, "data/raw/bea/CAINC4.zip"))
b = pd.read_csv(z.open("CAINC4__ALL_AREAS_1969_2024.csv"), encoding="latin1", dtype=str)
b.columns = [c.strip() for c in b.columns]
b = b[b.LineCode.notna()]
b["fips"] = b.GeoFIPS.str.strip().str.strip('"').str.strip()
b["line"] = b.LineCode.str.strip()
b = b[b.line.isin(LINES)]
long = b.melt(id_vars=["fips", "GeoName", "line"], value_vars=YEARS, var_name="year", value_name="v")
long["v"] = pd.to_numeric(long.v.str.strip(), errors="coerce") * 1000        # thousands of dollars -> dollars
W = long.pivot_table(index=["fips", "year"], columns="line", values="v", aggfunc="first").rename(columns=LINES)
names = b.drop_duplicates("fips").set_index("fips").GeoName.str.strip().str.rstrip("*").str.strip()

# County -> OEWS area (May 2024 definitions)
defs = definitions(2025)
raw = pd.read_excel(os.path.join(REF, "area_definitions_m2024.xlsx"), dtype=str)
raw["county"] = raw.FIPS.str.zfill(2) + raw["County code"].str.zfill(3)
cname = dict(zip(raw.county, raw["County name"].str.strip()))
home = defs.drop_duplicates("county").set_index("county").area

# BEA combined areas -> member county FIPS, matched by name within the state
combo_members = {}
by_name = {(c[:2], n.lower()): c for c, n in cname.items()}
for f, n in names.items():
    if "+" not in n or not re.match(r"^\d{5}$", f): continue
    st = f[:2]
    parts = [p.strip() for p in re.split(r"[,+]", n.rsplit(",", 1)[0])]
    want = [parts[0] + " County"] + [re.sub(r"\s+City$", "", p) + " city" for p in parts[1:]]
    if st == "15": want = ["Maui County", "Kalawao County"]
    members = [by_name.get((st, w.lower())) for w in want]
    if None in members:
        raise SystemExit(f"cannot match BEA combined area {f} {n}: {want}")
    combo_members[f] = members

unit_area, problems = {}, []
for f, members in combo_members.items():
    areas = {home.get(m) for m in members}
    if len(areas) == 1 and None not in areas: unit_area[f] = areas.pop()
    else: problems.append((f, names[f], areas))
for c in home.index:
    if c in W.index.get_level_values(0) and not any(c in m for m in combo_members.values()):
        unit_area[c] = home[c]
covered = {m for f in unit_area if f in combo_members for m in combo_members[f]} | {c for c in unit_area if c not in combo_members}
missing = sorted(set(home.index) - covered)
split_combo_areas = {home.get(m) for f, *_ in problems for m in combo_members[f]}

rows = []
for y in YEARS:
    Wy = W.xs(y, level="year")
    units = pd.DataFrame({"area": pd.Series(unit_area)}).join(Wy, how="left")
    for area, g in units.groupby("area"):
        complete = g[list(LINES.values())].notna().all().all()
        bad = area in split_combo_areas or any(home.get(m) == area for m in missing)
        rows.append({"area": area, "year": int(y), "complete": bool(complete and not bad), **g[list(LINES.values())].sum().to_dict()})
# U.S. and states straight from BEA
st_codes = {f: f for f in names.index if re.match(r"^\d\d000$", f)}
for y in YEARS:
    Wy = W.xs(y, level="year")
    for f in st_codes:
        if f not in Wy.index: continue
        r = Wy.loc[f]
        area = "99" if f == "00000" else str(int(f[:2]))          # OEWS: U.S. = 99, states = FIPS without zero-padding
        rows.append({"area": area, "year": int(y), "complete": bool(r.notna().all()), **r.to_dict()})
out = pd.DataFrame(rows)
out.loc[~out.complete, list(LINES.values())] = np.nan
out.to_csv(os.path.join(INT, "bea_income_by_area.csv"), index=False)

oews = pd.read_parquet(os.path.join(INT, "oews_2025.parquet"), columns=["area", "area_title", "area_type"]).drop_duplicates()
oews["akey"] = area_key(oews.area)
have = set(out[out.complete & (out.year == 2024)].area)
print("Virginia/Hawaii combined areas:", len(combo_members), "| split across OEWS areas:", problems or "none")
print("OEWS counties with no BEA unit:", missing or "none")
for t, n in [(1, "U.S."), (2, "states"), (4, "metros"), (6, "nonmetro"), (3, "territories")]:
    ks = oews[oews.area_type == t].akey
    print(f"{n}: {ks.isin(have).sum()} of {len(ks)} have complete 2024 income by source")
us = out[out.area == "99"].set_index("year")
print((us[["wages", "supplements", "proprietors", "dividends_interest_rent", "transfers"]].div(us.personal_income, axis=0) * 100).round(1).to_string())
