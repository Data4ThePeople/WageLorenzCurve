# Wage Inequality by City and State: Lorenz Curves of Payroll Wages by Occupation

An interactive chart of how payroll wages are split across occupations in 585 places in the United States: the U.S., every state, and every metro and nonmetro area. It uses May 2025 data from the Bureau of Labor Statistics, shows how states have changed since 2013 and most metro areas since 2016, and shows the income that wage data leaves out.

## Live links

- Interactive chart: https://data4thepeople.github.io/WageLorenzCurve/
- Post with the chart: https://www.data4thepeople.com/p/lorenz-chart-viz
- Follow-up post, five takeaways: https://www.data4thepeople.com/p/five-takeaways-wage-inequality

## What's here

- `dist/index.html`: the built chart, one self-contained page with the data inlined. GitHub Pages publishes this folder on every push to `main` (`.github/workflows/pages.yml`).
- `src/`: the page template (`template.html`) and the chart's math and drawing code (`core.js`).
- `scripts/`: the numbered Python pipeline, from loading the raw files to building the page and checking every number. `lorenz.py` holds the Lorenz curve and Gini functions; `geo.py` reads the metro county lists.
- `data/raw/`: where the source files go. They are not committed; see `data/raw/README.md`.
- `data/ref/`: BLS reference files used to match occupation codes across years and to define metro areas.
- `data/build/`: exported data, including `lorenz.json` (the data the chart uses), `day2_numbers.json` and `irs_income_sources_2023.csv`.
- `posts/`: the two posts, with their images.
- `analysis/`: working findings and the static charts for the five-takeaways post.
- `DATASETS.md`: full notes on every data source, its gaps and the checks run on it.
- `Visualizing Wage Dispersion and Occupational Pay Inequality.pdf`: the method for the first version of the chart, published February 4, 2026.
- `assets/`: Data 4 The People logos used on the page.

## Data sources

| Agency | Dataset | Used for |
|---|---|---|
| U.S. Bureau of Labor Statistics | Occupational Employment and Wage Statistics (OEWS), May "All data" files, 2011 to 2025 | Every Lorenz curve and Gini, and the top 10% vs. median wage readout |
| U.S. Bureau of Labor Statistics | Quarterly Census of Employment and Wages (QCEW), 2024 annual averages by county | Jobs weights to measure how much metro boundaries changed between years |
| U.S. Bureau of Economic Analysis | Personal income by source, counties (CAINC4), 2013-2024 | The "What this chart can't see" panel: income by source for each area |
| Internal Revenue Service | Statistics of Income, Table 1.4, tax year 2023 | The chart of where income comes from, by size of income |
| Internal Revenue Service | Statistics of Income, county data, tax year 2023 | Income by source for large counties (takeaway 5) |

All are U.S. government works in the public domain. File names, download addresses and known problems are in `DATASETS.md`.

## How to rebuild

Requirements: Python 3 with pandas, NumPy and matplotlib, and pandas' readers for Excel and parquet files. The page build and tie-out (steps 07 and 08) use macOS JavaScriptCore (`jsc`) and Google Chrome to check the page. No API key is needed.

1. Put the source files in `data/raw/` as listed in `DATASETS.md`: the OEWS "All data" files for 2011 to 2025, `qcew/qcew_2024_annual_industry10.csv`, `bea/CAINC4.zip`, `irs/23in14ar.xls` and `irs/23incyallnoagi.csv`.
2. Run the pipeline from the repo root, in this order:

```sh
python scripts/01_load_oews.py        # standardize each year's OEWS file to data/interim/
python scripts/02_harmonize_soc.py    # occupation groups that are stable from 2011 to 2025
python scripts/03_area_metrics.py     # coverage, Gini and noise band for every place and year
python scripts/05_boundary_check.py   # which metros kept stable boundaries (run before 04)
python scripts/04_history_tests.py    # change-over-time verdicts
python scripts/05b_bea_income.py      # BEA income by source for every area
python scripts/06_build_data.py       # export data/build/lorenz.json
python scripts/07_build_html.py       # build and check dist/index.html
python scripts/08_tieout.py           # recompute every number two ways and compare
```

3. For the post numbers and charts:

```sh
python scripts/09_findings.py         # candidate findings
python scripts/12_day2_numbers.py     # numbers for the five-takeaways post
python scripts/13_day2_charts.py      # static charts (also runs 10_irs_income_sources.py)
```

`scripts/10_irs_income_sources.py` and `scripts/11_hero.py` can also be run on their own to make the IRS income chart and the hero image.

## Method notes

- Each curve uses only detailed occupations. Total wages for an occupation are jobs (`TOT_EMP`) times the annual mean wage (`A_MEAN`), with occupations sorted by mean wage. The Gini here measures inequality between occupations' average pay in a place, not between individual workers, so it runs lower than person-level Gini figures.
- Occupation codes changed several times between 2011 and 2025. Codes are grouped using only BLS's own crosswalks, and jobs and wages are summed within each group, so no split of jobs between codes is assumed.
- Comparisons over time use only years that share no survey data: 2013, 2016, 2019, 2022 and 2025. Metros are compared only when their boundaries stayed close enough, as measured with QCEW jobs by county.
- A change counts as clear only if it is larger than two standard deviations of the noise estimated from BLS's published standard errors (300 draws), plus an allowance of 0.005 for the May 2021 change in BLS's estimation method where it applies, and if its direction holds on the shared set of occupations and at full detail.
- `scripts/08_tieout.py` reproduces the first published version (May 2024) and checks the page's own math against an independent Python computation for every place.

Data 4 The People
