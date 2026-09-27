"""Build harmonized occupation groups that are stable from May 2011 to May 2025.

Every detailed OEWS code used in any year is a node. Edges come only from BLS's
own documents (no title guessing):
  - 2010_and_2011_oes_classification.xls : OES 2010/2011 code <-> 2010 SOC code
  - oes_2019_hybrid_structure.xlsx       : OES 2019 code <-> 2018 SOC <-> OES 2018 code <-> 2010 SOC
  - soc_2010_to_2018_crosswalk.xlsx      : 2010 SOC <-> 2018 SOC
A harmonized group is a connected component. Employment and total wages are
additive, so summing within a group needs no allocation assumptions.
"""
import os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF, INT = os.path.join(ROOT, "data/ref"), os.path.join(ROOT, "data/interim")
CODE = re.compile(r"^\d\d-\d{4}$")


def codes_in(cell):
    return re.findall(r"\d\d-\d{4}", str(cell)) if pd.notna(cell) else []


def table(path, sheet, header_row):
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    df.columns = [str(c).strip() for c in df.iloc[header_row]]
    return df.iloc[header_row + 1:]


parent = {}
def find(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    parent[find(a)] = find(b)
def link(row_codes):
    row_codes = [c for c in row_codes if CODE.match(c.split(":")[1])]
    for c in row_codes[1:]:
        union(row_codes[0], c)
    for c in row_codes[:1]:
        find(c)

t = table(os.path.join(REF, "2010_and_2011_oes_classification.xls"), "OES use of combined SOC data", 9)
for _, r in t.iterrows():
    link([f"o10:{c}" for c in codes_in(r["OES 2010 code"])] + [f"s10:{c}" for c in codes_in(r["2010 SOC code"])])
t = table(os.path.join(REF, "oes_2019_hybrid_structure.xlsx"), "OES2019 Hybrid", 5)
for _, r in t.iterrows():
    link([f"o19:{c}" for c in codes_in(r["OES 2019 Estimates Code"])] + [f"s18:{c}" for c in codes_in(r["2018 SOC Code"])] +
         [f"o18:{c}" for c in codes_in(r["OES 2018 Estimates Code"])] + [f"s10:{c}" for c in codes_in(r["2010 SOC Code"])])
t = table(os.path.join(REF, "soc_2010_to_2018_crosswalk.xlsx"), "Sorted by 2010", 8)
for _, r in t.iterrows():
    link([f"s10:{c}" for c in codes_in(r["2010 SOC Code"])] + [f"s18:{c}" for c in codes_in(r["2018 SOC Code"])])

# Year -> which namespace its codes live in. 2012-2018 OES codes are 2010 SOC codes or
# OES-2018-style aggregates; 2019-2020 are OES 2019 hybrid; 2021+ are 2018 SOC.
def node_for(year, code):
    if year <= 2011: cands = [f"o10:{code}", f"s10:{code}"]
    elif year <= 2018: cands = [f"o18:{code}", f"s10:{code}", f"o10:{code}"]
    elif year <= 2020: cands = [f"o19:{code}", f"s18:{code}"]
    else: cands = [f"s18:{code}", f"o19:{code}"]
    for c in cands:
        if c in parent: return c
    return None

rows, unmatched = [], []
for y in range(2011, 2026):
    d = pd.read_parquet(os.path.join(INT, f"oews_{y}.parquet"), columns=["occ_code", "occ_title", "o_group"])
    det = d[d.o_group.isin(["detailed", "detail", "detailed_or_blank"])].drop_duplicates("occ_code")
    for code, title in zip(det.occ_code, det.occ_title):
        n = node_for(y, code)
        if n is None: unmatched.append((y, code, title))
        else: rows.append((y, code, title, find(n)))
m = pd.DataFrame(rows, columns=["year", "occ_code", "occ_title", "root"])
# Name each group by its members' codes in the latest year they appear
latest = m.groupby("root")["year"].max()
names = m.merge(latest.rename("ly").reset_index(), on="root").query("year == ly")
names = names.sort_values("occ_code")
lab = names.groupby("root").agg(hgroup=("occ_code", "+".join), hgroup_title=("occ_title", " / ".join))
m = m.merge(lab.reset_index(), on="root").drop(columns="root")
m.to_parquet(os.path.join(INT, "soc_harmonized_map.parquet"), index=False)
pd.DataFrame(unmatched, columns=["year", "occ_code", "occ_title"]).to_csv(os.path.join(INT, "soc_unmatched.csv"), index=False)

per_year = m.groupby("year").agg(codes=("occ_code", "nunique"), groups=("hgroup", "nunique"))
print(per_year.to_string())
print("unmatched codes:", len(unmatched)); print(pd.DataFrame(unmatched).drop_duplicates(1).to_string() if unmatched else "")
sizes = m.drop_duplicates(["year", "occ_code"]).groupby("hgroup").occ_code.nunique().sort_values(ascending=False)
print("groups total:", m.hgroup.nunique(), "| groups covering all 15 years:", (m.groupby("hgroup").year.nunique() == 15).sum())
print("largest groups (distinct codes over all years):"); print(sizes.head(12).to_string())
