"""Standardize the OEWS May "All data" files (2011-2025) into one parquet per year.

Keeps cross-industry rows (NAICS 000000) for every area type. BLS special
symbols are kept as flags rather than silently becoming NaN:
  *   wage not available          **  employment not available
  #   wage >= top-code threshold  ~   under 0.5% of estimate
"""
import glob, os, re, sys
from multiprocessing import Pool
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, OUT = os.path.join(ROOT, "data/raw"), os.path.join(ROOT, "data/interim")

RENAME = {"occ code": "occ_code", "occ title": "occ_title", "group": "o_group",
          "loc_q": "loc_quotient", "pct_tot": "pct_total", "jobs_1000_orig": "jobs_1000"}
KEEP = ["area", "area_title", "area_type", "prim_state", "naics", "own_code", "occ_code",
        "occ_title", "o_group", "tot_emp", "emp_prse", "h_mean", "a_mean", "mean_prse",
        "a_pct10", "a_pct25", "a_median", "a_pct75", "a_pct90", "annual", "hourly"]
NUM = ["tot_emp", "emp_prse", "h_mean", "a_mean", "mean_prse",
       "a_pct10", "a_pct25", "a_median", "a_pct75", "a_pct90"]


# Values in BLS's own files that are errors, set to missing (documented in DATASETS.md).
KNOWN_ERRORS = [
    # May 2013 U.S. Hunters and Trappers shows exactly 99,999 jobs; the occupation is not published nationally in 2012 or 2014.
    dict(year=2013, area="99", occ_code="45-3021", field="tot_emp"),
]


def year_of(path):
    m = re.search(r"(20\d\d)", os.path.basename(path))
    return int(m.group(1))


def load(path):
    yr = year_of(path)
    df = pd.read_excel(path, sheet_name=0, dtype=str)
    df.columns = [RENAME.get(c.strip().lower(), c.strip().lower()) for c in df.columns if c is not None] + \
                 list(df.columns[len([c for c in df.columns if c is not None]):])
    df = df.loc[:, [c for c in df.columns if isinstance(c, str) and not c.startswith("unnamed")]]
    df["naics"] = df["naics"].str.strip()
    df = df[df["naics"] == "000000"].copy()
    for c in KEEP:
        if c not in df.columns:
            df[c] = None
    df = df[KEEP]
    for c in ["area", "occ_code", "o_group", "area_title", "occ_title"]:
        df[c] = df[c].astype(str).str.strip()
    df["o_group"] = df["o_group"].str.lower().replace({"nan": "detailed_or_blank"})
    for c in NUM:
        raw = df[c].astype(str).str.strip()
        df[c + "_flag"] = raw.where(raw.isin(["*", "**", "#", "~"]))
        df[c] = pd.to_numeric(raw.str.replace(",", ""), errors="coerce")
    df["area_type"] = pd.to_numeric(df["area_type"], errors="coerce").astype("Int64")
    for e in KNOWN_ERRORS:
        if e["year"] == yr:
            hit = (df.area == e["area"]) & (df.occ_code == e["occ_code"])
            assert hit.sum() == 1, f"known error not found: {e}"
            df.loc[hit, e["field"]] = float("nan"); df.loc[hit, e["field"] + "_flag"] = "error"
    df.insert(0, "year", yr)
    df.to_parquet(os.path.join(OUT, f"oews_{yr}.parquet"), index=False)
    return yr, len(df), df["area"].nunique()


if __name__ == "__main__":
    files = sorted(set(glob.glob(os.path.join(RAW, "**/*.xlsx"), recursive=True)))
    files = [f for f in files if re.search(r"(all_data_M_|all_oes_data_|oes_data_)20\d\d\.xlsx$", f)
             and not os.path.basename(f).startswith("~$")]
    if len(sys.argv) > 1:
        files = [f for f in files if str(year_of(f)) in sys.argv[1:]]
    with Pool(min(8, len(files))) as p:
        for yr, n, na in sorted(p.map(load, files)):
            print(f"{yr}: {n:,} cross-industry rows, {na} areas")
