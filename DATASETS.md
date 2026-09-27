# Datasets

## 1. BLS Occupational Employment and Wage Statistics (OEWS), May 2011 to May 2025

**What it is.** Employment and wage estimates by occupation and area from a
semiannual survey of about 1.1 million establishments (payroll jobs only; no
self-employed, no unincorporated owners, no private household workers). Each May
estimate pools six semiannual panels, so it covers three years of survey data.
Older panels are wage-adjusted to the reference period with the Employment Cost
Index.

**Files used.** The May "All data" XLSX for each year, 2011 to 2025, in
`data/raw/` (supplied by Eric; not committed). File names and column names vary
by year (`occ code` vs `occ_code`, `group` vs `o_group`, upper vs lower case,
`PRIM_STATE` added in 2020, `jobs_1000_orig` in 2019). `scripts/01_load_oews.py`
standardizes them to `data/interim/oews_<year>.parquet`, keeping cross-industry
rows (NAICS 000000, ownership 1235 or 5) for every area.

**API.** The BLS time-series database (and so the public API) holds only the
latest year: all 6,023,970 OE series begin and end in 2025 (checked
September 27, 2026). History must come from the annual files.

**Coverage.** U.S., 50 states + DC, Guam, Puerto Rico, Virgin Islands, metro
areas, nonmetro areas. Area counts: 641 (2011 to 2014), 654 to 655 (2015 to
2017, after the 2013 OMB metro redraw), 584 to 587 (2018 to 2023; metro
divisions dropped, nonmetro areas redrawn), 585 (2024 to 2025, new area
definitions).

**Occupation level (no double counting).** Every Lorenz curve uses only
detailed occupations. The label for that level changes by year: blank in 2011,
`detail` in 2012 to 2015, `detailed` from 2016. Total, major, minor and broad
rows are sums of detailed rows and are never added in.

**Wage measure.** Annual mean wage (`A_MEAN`), as in Eric's original method,
because it is published for more cells than the percentiles. Total wages for an
occupation = `TOT_EMP` x `A_MEAN`.

**Missing values and codes.**
- `**` employment not published (suppressed for confidentiality or quality).
  The occupation drops off the curve; its jobs are still in the area total.
- `*` wage not published.
- `#` wage at or above the top-code limit. The occupation drops off the curve.
  These are the highest-paid jobs, so dropping them understates the gap.
  Measured share of jobs lost this way: 0 nationally, median 0.01% for states,
  at most 0.87% in any metro.
- Hourly-only occupations (`HOURLY` = TRUE, for example performers) have no
  annual mean and drop off the curve. Annual-only occupations (teachers,
  pilots) have no hourly mean; that does not affect this analysis.

**Coverage of the curve** (share of an area's jobs that have both employment
and an annual mean), from `scripts/03_area_metrics.py`:

| Level | 2011 to 2020 | 2021 to 2025 |
|---|---|---|
| U.S. | 99.9% | 99.9% |
| States, median (lowest) | 98.5% (91%) | 98.8% (93%) |
| Metros, median (10th percentile) | 88% (77%) | 92% (84%) |
| Nonmetro, median (10th percentile) | 89% (76%) | 94% (89%) |

**Classification changes (occupations).**
- 2011: OES 2010 hybrid of 2000 and 2010 SOC.
- 2012 to 2018: 2010 SOC, with some OES-only combined codes.
- 2019 to 2020: OES hybrid of 2010 and 2018 SOC.
- 2021 onward: 2018 SOC.
Harmonized with BLS's own documents only (`data/ref/`):
`2010_and_2011_oes_classification.xls`, `oes_2019_hybrid_structure.xlsx`,
`soc_2010_to_2018_crosswalk.xlsx`. Codes linked by any split or merge form one
group (`scripts/02_harmonize_soc.py`). All detailed codes in all 15 years trace
to a group, with none left unmatched. About 830 codes per year become 753 to 755 groups.
Employment and total wages are summed within a group, so no allocation is
assumed. The largest group joins 14 current codes (most computer occupations
plus two "all other" management and business codes) because "all other" codes
chain together.
Effect on the Gini: grouping lowers it by 0.0007 to 0.0015 nationally, by a
similar amount every year.

**Estimation method change, May 2021.** BLS moved to a model-based estimator.
Observed in this data: metro coverage rises about 4 points and the metro
noise estimate halves from 2021. States and metros fell about 0.002 to 0.003 more than
the U.S. in each of 2020 to 2021 and 2021 to 2022, a combined gap of about
0.005. This could be the method, a real change, or both; the data cannot
separate them. History tests treat up to 0.005 of any sub-national change that
spans 2021 as possibly method-driven.

**Geography changes (metros).** Metros were redrawn in May 2015 (2013 OMB
delineations) and again in May 2024. County lists used:
`area_definitions_m2016`, `_2018`, `_m2019`, `_m2021`, `_m2022`, `_m2023`,
`_m2024` from BLS. BLS does not post county lists for 2011 to 2015 at the
standard address. Before 2024, New England metros are built from towns; from
2024, from counties (Connecticut uses planning regions). May 2025 uses the May
2024 definitions (identical area codes in both years' data).

Boundary check (`scripts/05_boundary_check.py`, using QCEW, dataset 2): each
2025 metro is matched to the frame-year metro sharing the most jobs (35 are
renumbered). Boundary change = jobs in counties in only one of the two
definitions / jobs in both combined. Eligible for history if under 2%. If a
metro lost whole counties that now form other 2025 areas, those areas are
merged back in to rebuild the old boundary; eligible if that moves the 2025
Gini by less than 0.002 (New York: Dutchess and Orange moved to Kiryas
Joel-Poughkeepsie-Newburgh, 2.9% of jobs, Gini effect 0.0009; New Orleans:
Slidell split off, effect 0.0013). Result, 2016 to 2025: 305 of 393 metros
eligible. Not eligible: most New England metros (towns that split counties;
Connecticut's old counties are not in current QCEW), metros newly split from
larger ones (Kenosha, Kiryas Joel-Poughkeepsie-Newburgh), and metros whose
boundaries changed by 2% or more.
County code fixes applied: 02261 -> 02063 + 02066, 46113 -> 46102,
51515 -> 51019, 12025 -> 12086; Kalawao County, HI (15005) has no QCEW row and
is counted as 0 jobs.

Nonmetro areas were redrawn in 2018 and 2024 and are shown for 2025 only.

**Metro files check.** Eric's `oesmYYma` files (MSA, BOS, aMSA) match the
All-data metro and nonmetro rows exactly (2016 and 2025: 0 employment and 0
wage differences). The aMSA files (2011 to 2017) are the 11 full metros that
also have divisions, and those rows are in All data too. No county lists.

**Top-code limit** (from each year's file descriptions): $187,200 a year
($90/hour) through May 2015; $208,000 ($100/hour) May 2016 to 2018. Later
years to be confirmed from the field descriptions.

**Overlap between years.** Adjacent May estimates share five of six panels.
Only years three apart share no survey data: 2013, 2016, 2019, 2022, 2025.

**Publisher's uncertainty.** Relative standard errors for employment
(`EMP_PRSE`) and mean wage (`MEAN_PRSE`) are published per cell. The Gini noise
band here comes from 300 draws perturbing each cell by its RSE, treated as
independent (an approximation). Median 1 SD: U.S. well under 0.001, states
0.0013, metros 0.0038 before 2021 and 0.0018 after.

**Revisions.** OEWS does not revise past May estimates.

**Units and rounding.** Employment rounded to tens; annual wages in nominal
dollars, rounded to whole dollars. The Gini is unaffected by inflation because
it depends only on shares.

**What the Gini measures here.** Inequality between occupations' average pay
in an area, not between individual workers. Pay differences inside an
occupation are not counted, so it runs lower than person-level Gini figures.

**License.** U.S. government work, public domain. Cite as U.S. Bureau of Labor
Statistics, Occupational Employment and Wage Statistics.

**History verdicts** (`scripts/04_history_tests.py`, change to May 2025 must
clear 2 x noise SD + 0.005 method allowance (states and metros, spans crossing
2021) + any boundary-rebuild effect, and agree in direction on the common
occupation set and at native detail):

| Start | U.S. | States: drop / rise / no clear change | Metros: drop / rise / no clear change |
|---|---|---|---|
| 2013 | drop | 49 / 0 / 2 | not tested (no county lists) |
| 2016 | drop | 47 / 0 / 4 | 229 / 1 / 75 |
| 2019 | drop | 32 / 0 / 19 | 167 / 2 / 138 |
| 2022 | drop | 15 / 11 / 25 | 108 / 56 / 143 |

**Reproduction check.** May 2024, NY-Newark-Jersey City metro Gini = 0.3148
and California: lowest-paid 40.2% of workers earn 21.7% of wages. Both match
the published February 4, 2026 post exactly.

## 2. BLS Quarterly Census of Employment and Wages (QCEW), 2024 annual averages

**What it is.** Count of jobs covered by unemployment insurance, by county,
from employer tax filings (a near-census, not a survey).

**File used.** `data.bls.gov/cew/data/api/2024/a/industry/10.csv` (all
industries), saved to `data/raw/qcew/`. Rows with own_code 0 (all ownerships)
and 5-digit county FIPS; field `annual_avg_emplvl`. 3,275 county rows, none
suppressed at this level.

**Use here.** Only as weights to measure how many jobs sit in the counties a
metro gained or lost between definitions. Not used in any Lorenz curve.

**Quirks.** Connecticut is reported by planning region (09110 to 09190), not
the old counties used in pre-2024 OEWS definitions. A single year (2024) is
used for all frame comparisons, which is adequate for a share-of-jobs threshold.

**License.** U.S. government work, public domain.
