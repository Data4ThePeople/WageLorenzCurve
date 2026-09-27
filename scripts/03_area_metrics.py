"""Per area and year: coverage, native and harmonized Gini, and a noise band.

Noise band: 300 draws where each occupation's employment and mean wage are
perturbed by BLS's published relative standard errors (EMP_PRSE, MEAN_PRSE),
treated as independent normal errors. This ignores correlation between cells,
so it is an approximation of sampling error, not an exact one.
"""
import os, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lorenz import gini, usable, harmonize, DETAILED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data/interim")
DRAWS = 300


def gini_draws(emp, mean, eprse, mprse, rng):
    e = emp * (1 + rng.standard_normal((DRAWS, len(emp))) * np.nan_to_num(eprse, nan=0) / 100)
    m = mean * (1 + rng.standard_normal((DRAWS, len(mean))) * np.nan_to_num(mprse, nan=0) / 100)
    e, m = np.clip(e, 0, None), np.clip(m, 1, None)
    o = np.argsort(m, axis=1)
    e, w = np.take_along_axis(e, o, 1), np.take_along_axis(e * m, o, 1)
    x = np.c_[np.zeros(DRAWS), np.cumsum(e, 1) / e.sum(1, keepdims=True)]
    y = np.c_[np.zeros(DRAWS), np.cumsum(w, 1) / w.sum(1, keepdims=True)]
    return 1 - np.sum(np.diff(x, axis=1) * (y[:, 1:] + y[:, :-1]), axis=1)


def run(year):
    rng = np.random.default_rng(year)
    cmap = pd.read_parquet(os.path.join(INT, "soc_harmonized_map.parquet"))[["year", "occ_code", "hgroup"]].drop_duplicates()
    d = pd.read_parquet(os.path.join(INT, f"oews_{year}.parquet"))
    harm = harmonize(d, cmap)
    rows = []
    for area, a in d.groupby("area"):
        tot = a.loc[a.o_group == "total", "tot_emp"].iloc[0]
        det = a[a.o_group.isin(DETAILED)]
        u = usable(a)
        h = harm[harm.area == area]
        g = gini_draws(u.tot_emp.values, u.a_mean.values, u.emp_prse.values, u.mean_prse.values, rng)
        rows.append(dict(
            year=year, area=area, area_title=a.area_title.iloc[0], area_type=int(a.area_type.iloc[0]),
            total_emp=tot, n_occ=len(u), n_hgroups=len(h),
            coverage=u.tot_emp.sum() / tot,                                    # share of area jobs on the curve
            lost_topcode=det.loc[det.a_mean_flag == "#", "tot_emp"].sum() / tot,
            lost_nowage=det.loc[det.a_mean.isna() & (det.a_mean_flag != "#"), "tot_emp"].sum() / tot,
            n_emp_suppressed=int((det.tot_emp_flag == "**").sum()),
            gini=gini(u.tot_emp, u.a_mean), gini_harm=gini(h.tot_emp, h.a_mean),
            gini_sd=g.std(), gini_p05=np.percentile(g, 5), gini_p95=np.percentile(g, 95),
            prse_missing=float(u.emp_prse.isna().mean())))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    with Pool(8) as p:
        out = pd.concat(p.map(run, range(2011, 2026)), ignore_index=True)
    out.to_parquet(os.path.join(INT, "area_metrics.parquet"), index=False)
    print(len(out), "area-years")
