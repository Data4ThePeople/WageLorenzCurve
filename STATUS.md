# Status

Project: WageLorenzCurve
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: lorenz-chart-viz (Day 1; replaces the February 4, 2026 post in place)
Step: 2g (waiting to start)
Since: 2026-09-27

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | 2026-09-27 | Viz live at data4thepeople.github.io/WageLorenzCurve; candidate findings in analysis/candidate_findings.md |
| 2a | Draft with brackets resolved | 2026-09-27 | Claude-written draft at Eric's request; replaces the February post in place |
| 2b | Eric's edit, Claude's look-over | 2026-09-27 | Items 1-15 accepted; IRS chart and crosswalk write-up added |
| 2c | Slice markup | 2026-09-27 | 129 blocks; spacers between blurbs |
| 2d | Hero 1680x1080 + alt text | 2026-09-27 | U.S. May 2025 curve rendered at hero scale; alt 463 characters |
| 2e | SEO | 2026-09-27 | Retargeted to wage inequality by city and state; dataset schema, 14 FAQ entries |
| 2f | Pushed to Prismic (draft) | 2026-09-27 | Updated document aYJX3BAAACIAbrYU in the Migration Release; 96 slices; images QXqFczhLJVJhoXjV (IRS chart), ziKWhU2NZtEJ_P01 (hero) |
| 2g | Mailchimp teaser | | |

## Stale

None. (2a-2d were stale after /step back 1 on 2026-09-27; re-run the same day at Eric's instruction.)

## Log

- 2026-09-27 Step 1 opened. Topic: rebuild the OEWS occupational Lorenz curve
  (published February 4, 2026, Tableau) as a self-contained viz on May 2025
  data, add storytelling enhancements, and animate history if it holds up.
- 2026-09-27 Reproduction check passed (NY metro 2024 Gini 0.3148; CA 40.2% /
  21.7%). History assessment: U.S. and states 2013-2025 and same-county metros
  2016-2025 pass; big metros blocked by the 2024 redraw. Next: QCEW check on
  changed counties. See DATASETS.md.
- 2026-09-27 QCEW boundary check: 305 metros eligible for history from 2016
  (New York and New Orleans via rebuilt old boundaries). Viz built
  (`dist/index.html`): May 2025 view, change over time 2013-2025, tooltip,
  readouts, ranking strip, group shares, compare, table view. Tie-out passes
  (`scripts/08_tieout.py`). Published to GitHub Pages.
- 2026-09-27 Eric's review: bubbles colored by major group again (first two SOC
  digits) with click-to-highlight; dropdown place pickers with type-ahead.
  Reframed to "Occupational Pay Gaps by Place": payroll wages only, verdicts
  describe the gap between occupations, permanent caveat. Added BEA income by
  source ("What this chart can't see"). Removed the Gini trend chart; the
  all-places Gini strip now animates through the years.
- 2026-09-27 Candidate findings for Day 2 (`analysis/candidate_findings.md`);
  BLS data issues found and handled (2013 file error; California 2017 counting
  change for home health and personal care aides, noted in the viz).
- 2026-09-27 Step 1 confirmed by Eric. Plan: two posts. Day 1 reintroduces
  the viz (what changed, how to use it, method, limits); Day 2 gives five
  takeaways chosen from the candidate list (home health aides in New York
  required). Each post runs 2a to 2g under its own slug.
- 2026-09-27 Step 2a opened for Day 1, slug occupational-pay-gaps-by-place
  (proposed). At Eric's request Claude wrote the first draft (normally Eric
  provides it). Open items: link to the February 4, 2026 post; send date
  (draft assumes Monday, September 28, with Day 2 on Tuesday, September 29).
- 2026-09-27 Decision: Day 1 replaces the February 4, 2026 post in place
  (https://www.data4thepeople.com/p/lorenz-chart-viz, Prismic document
  aYJX3BAAACIAbrYU). Draft moved to posts/lorenz-chart-viz; front matter keeps
  date 2026-02-04, adds updated 2026-09-28 and prismic_id. The importer's
  update replaces the page body and does not carry author or tags: at 2f,
  re-set author and the Visualization tag in Prismic before publishing.
- 2026-09-27 Title confirmed by Eric: "Occupational Pay Gaps by Place: An Interactive
  Lorenz Curve for Every U.S. State and Metro Area" (replaces the February title).
- 2026-09-27 Step 2a confirmed by Eric.
- 2026-09-27 2b: Eric accepted look-over items 1-15. Added the IRS income-by-
  source chart (images/01-income-sources-by-income.png, tax year 2023) after
  "Read this first", expanded Step 3 on the crosswalk (home health aides
  example), added IRS to data sources, DATASETS.md and the tie-out.
- 2026-09-27 Step 2b confirmed by Eric.
- 2026-09-27 Step 2c confirmed by Eric.
- 2026-09-27 2d: hero rendered from the U.S. May 2025 curve at hero scale (scripts/11_hero.py), padded with hero pad (4%), alt text 463 characters; hero check ok.
- 2026-09-27 Step 2d confirmed by Eric.
- 2026-09-27 2e: meta title, description, keywords and dataset schema written (Dataset, WebPage, WebApplication, FAQPage with 11 questions); target searches proposed by Claude for Eric to confirm.
- 2026-09-27 /step back 1: add top-10%-vs-median readout (BLS all-occupation percentiles) to the viz; SEO retarget approved (items 1-7 of the competition analysis).
- 2026-09-27 Step 1 rework done: top 10% vs. median readout live (tie-out 1,712 place-years, 0 mismatches). Post retargeted: new H1 and title, meta, keywords, rankings section, three new common questions. Waiting for Eric to re-confirm Step 1, then 2a-2d re-run in order.
- 2026-09-27 Combined occupation groups now named after their largest member (the 14-code Software Developers group was labeled Entertainment and Recreation Managers); earlier-year codes shown in the tooltip; grouping-effect statements corrected in the viz, post Step 3 and DATASETS.md; Eric's paragraph on historical comparison added to Step 3.
- 2026-09-27 Step 1 re-confirmed by Eric. Eric asked to move through 2a-2f to the Prismic Migration Release.
- 2026-09-27 2a and 2b re-run: changes since last confirmation are the approved SEO items (1-7) and Eric's Step 3 paragraph; every new number checked against the data (rankings, Gini values, top-10% vs median, U.S. line, Puerto Rico range). No issues.
- 2026-09-27 2c re-run: 165 blocks, no back-to-back blurbs; embed cache tag updated to v=20260927c.
- 2026-09-27 2d re-run: hero title text now Wage Inequality by City and State; alt text updated; hero check ok. 2e confirmed via Eric's approval of the SEO retarget. Moving to 2f.
- 2026-09-27 2f: dry run then publish. Updated draft aYJX3BAAACIAbrYU (slug lorenz-chart-viz) in the Migration Release. Before publishing in Prismic: set author (Eric Pachman) and the Visualization tag, which the update does not carry. Not verified by read-back (no PRISMIC_READ_TOKEN).
- 2026-09-27 Publication date and time set to 2026-09-27 21:00 EDT (updated date the same); Updated blurb now reads September 27, 2026; draft re-pushed.
- 2026-09-27 Send plan confirmed: Day 1 (lorenz-chart-viz) publishes tonight, September 27; Day 2 (five takeaways) publishes Monday night, September 28, matching the Tomorrow line.
