# Status

Project: WageLorenzCurve
Process: ~/.claude/d4tp-process/PROCESS.md

## Current

Post: none yet
Step: 1
Since: 2026-09-27

## Steps

| Step | What | Confirmed | Notes |
|---|---|---|---|
| 1  | Exploration and analysis | | |
| 2a | Draft with brackets resolved | | |
| 2b | Eric's edit, Claude's look-over | | |
| 2c | Slice markup | | |
| 2d | Hero 1680x1080 + alt text | | |
| 2e | SEO | | |
| 2f | Pushed to Prismic (draft) | | |
| 2g | Mailchimp teaser | | |

## Stale

None.

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
