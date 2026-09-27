"""Metro county lists from BLS OEWS area-definition files in data/ref/."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "data/ref")
# County list in force for each frame year. May 2025 uses the May 2024 definitions
# (checked: identical metro and nonmetro codes in the 2024 and 2025 data).
DEF_FILE = {2016: "area_definitions_m2016.xlsx", 2019: "area_definitions_m2019.xlsx",
            2022: "area_definitions_m2022.xlsx", 2025: "area_definitions_m2024.xlsx"}


def area_key(s):
    return s.astype(str).str.strip().str.lstrip("0")


def definitions(year):
    """One row per county (or New England town) with the metro it belongs to."""
    d = pd.read_excel(os.path.join(REF, DEF_FILE[year]), dtype=str)
    d.columns = [c.strip() for c in d.columns]
    code = next(c for c in d.columns if c.startswith("MSA code (incl") or c.endswith("MSA code") or c == "new_area")
    area = d[code].str.strip()
    if "MSA code for MSAs with divisions" in d.columns:     # 2016 lists divisions; roll up to the full MSA
        area = d["MSA code for MSAs with divisions"].fillna(area).str.strip()
    fips = (d["FIPS code"] if "FIPS code" in d.columns else d["FIPS"]).str.zfill(2)
    twp = d["Township code"].fillna("0").str.zfill(5) if "Township code" in d.columns else "00000"
    out = pd.DataFrame({"area": area_key(area), "county": fips + d["County code"].str.zfill(3), "town": twp})
    return out.drop_duplicates()


def county_sets(year):
    d = definitions(year)
    return (d.county + d.town).groupby(d.area).apply(frozenset)
