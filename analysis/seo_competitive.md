# Search competition for the wage-gap tool (September 27, 2026)

Method: live web searches for the phrases people use, noting who ranks, what
they offer, and where they are weak. Results are from one search engine on one
day; rankings move. No search-volume data was available, so demand is judged
from what ranks and how recently it was published.

| Search cluster | Who ranks now | What they offer | Weakness | Can we win? |
|---|---|---|---|---|
| "wage gap", "pay gap", "wage gap by city/state" | Pew, NWLC, Business.com, Chamber of Commerce, GoodHire | Gender pay gap by metro/state, some calculators | Different topic (gender) | No for the bare phrase. The intent is gender. |
| "wage inequality by state (map/chart)", "states with widest wage gaps" | Visual Capitalist (Ranked: states with widest wage gaps), SmartAsset via Stacker, syndicated to dozens of local TV sites Sept 11, 2026 | One number per state: top-10% wage threshold vs median (OEWS May 2025), static chart | States only; one statistic; static; "increasing/decreasing" compares May 2024 to May 2025, which share most of their survey data | Yes. Interactive, every state and 393 metros, occupation detail, tested change since 2013. |
| "wage inequality by metro area / city", "which city has the biggest pay gap" | HowMuch.net (2014-2015 maps), EPI (top 1% income, IRS, older), Brookings (2016), The Ladders | Old maps, income not wages | Stale (8-12 years), not interactive, income not wages | Yes. Freshest and only interactive metro-level wage tool found. |
| "income inequality by state/metro", "gini coefficient by state" | Census/ACS Gini (World Population Review, SHADAC, Visual Capitalist), EPI | Household income Gini | They measure all household income, which is the right answer for that search | Not as the primary target. Our measure is payroll wages; ranking for "income inequality" invites the misreading Eric wants to avoid. Answer it in an FAQ instead. |
| "wage inequality [city]" (e.g., New York) | Local government and Fed reports (NYC Comptroller, NY Fed), local news | Deep single-city reports | One city each; not comparable across places | Partly. The tool covers every city, but it is one URL and the place-level text is inside the iframe, so crawlers cannot see it. Crawlable rankings in the post help. |
| "wage inequality chart/tool/interactive", "compare cities" | EPI interactives, MIT Atlas of Inequality, Stanford income segregation maps, Census visualizations | Research-grade tools on other measures | None cover wages by occupation by metro | Yes, as a tool: "interactive wage inequality chart for every city." |
| "is wage inequality getting worse" | Stacker/SmartAsset syndications (Sept 2026), Oxfam/Forbes | Year-over-year state changes; top-income reports | Year-over-year OEWS change is mostly overlapping survey data | Yes, with Day 2: tested change since 2013/2016 and the mixed picture since 2022. |

## What we have that no ranking page has

1. Every state and every metro area in one interactive tool, May 2025.
2. Occupation-level detail: which jobs sit where on the curve.
3. Change over time tested against survey noise, on years that share no survey data.
4. The income the chart leaves out (BEA) and the IRS income-by-source chart.
5. The same top-10% and median wage figures competitors use are available for all 585 places in our data (all-occupations percentiles), not only states.

## Constraint

The place-by-place results live inside the embedded tool, which search engines do
not read as part of the post. Anything we want to rank for has to appear as
ordinary text on the page: headings, rankings, and question-and-answer pairs.
