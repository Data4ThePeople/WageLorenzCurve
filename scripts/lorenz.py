"""Lorenz curve and Gini, following Eric's published method: detailed occupations
only, total wages = TOT_EMP * A_MEAN, sort by A_MEAN ascending, trapezoid rule."""
import numpy as np

DETAILED = {"detailed", "detail", "detailed_or_blank"}


def gini(emp, mean):
    emp, mean = np.asarray(emp, float), np.asarray(mean, float)
    o = np.argsort(mean, kind="stable")
    emp, wages = emp[o], emp[o] * mean[o]
    x = np.r_[0, np.cumsum(emp) / emp.sum()]
    y = np.r_[0, np.cumsum(wages) / wages.sum()]
    return 1 - np.sum(np.diff(x) * (y[1:] + y[:-1]))


def usable(df):
    """Detailed rows that have both employment and an annual mean wage."""
    return df[df.o_group.isin(DETAILED) & df.tot_emp.notna() & df.a_mean.notna()]


def harmonize(df, cmap):
    """Sum employment and total wages within harmonized groups; mean = wages / emp."""
    u = usable(df).merge(cmap, on=["year", "occ_code"], how="left")
    assert u.hgroup.notna().all(), "occupation code missing from harmonized map"
    u = u.assign(wages=u.tot_emp * u.a_mean)
    g = u.groupby(["year", "area", "hgroup"], as_index=False)[["tot_emp", "wages"]].sum()
    return g.assign(a_mean=g.wages / g.tot_emp)
