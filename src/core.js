// Lorenz math shared by the page and the tie-out (scripts/08_tieout.py runs this file
// under macOS jsc). Same method as Eric's February 4, 2026 post: detailed occupations,
// total wages = jobs x annual mean wage, sorted by mean wage ascending, trapezoid Gini.
// Plain functions, no DOM.

// rows: [{key, e (jobs), w (annual mean wage), ...}] -> curve
function lorenz(rows) {
  const r = rows.slice().sort((a, b) => a.w - b.w || (a.key < b.key ? -1 : 1));
  let E = 0, W = 0;
  for (const p of r) { E += p.e; W += p.e * p.w; }
  const pts = [];
  let ce = 0, cw = 0, area = 0, px = 0, py = 0;
  for (const p of r) {
    ce += p.e; cw += p.e * p.w;
    const x = ce / E, y = cw / W;
    area += (x - px) * (y + py);
    pts.push({ row: p, x, y, x0: px, y0: py, jobShare: p.e / E, wageShare: p.e * p.w / W });
    px = x; py = y;
  }
  return { pts, jobs: E, wages: W, avgWage: W / E, gini: 1 - area };
}

// Share of wages earned by the lowest-paid fraction p of workers (linear inside an
// occupation, which is what the curve itself assumes).
function wageShareAt(curve, p) {
  let px = 0, py = 0;
  for (const q of curve.pts) {
    if (q.x >= p) return py + (q.y - py) * (q.x === px ? 0 : (p - px) / (q.x - px));
    px = q.x; py = q.y;
  }
  return 1;
}

function readouts(curve) {
  return {
    gini: curve.gini,
    bottomHalf: wageShareAt(curve, 0.5),
    top10: 1 - wageShareAt(curve, 0.9),
    avgWage: curve.avgWage,
    jobs: curve.jobs,
  };
}

// Latest (native) rows for an area from the packed data
function latestRows(D, areaId) {
  const L = D.latest[areaId];
  const out = [];
  for (let i = 0; i < L.o.length; i++) {
    const oc = D.occs[L.o[i]];
    out.push({ key: 'o' + L.o[i], occ: L.o[i], group: oc.group, major: oc.major, e: L.e[i], w: L.w[i] });
  }
  return out;
}

// Harmonized rows: frame years from the export; 2025 rebuilt by summing latest rows by group
function historyRows(D, areaId, year) {
  if (year === D.meta.latest_year) {
    const by = new Map();
    for (const r of latestRows(D, areaId)) {
      const g = by.get(r.group) || { e: 0, wsum: 0 };
      g.e += r.e; g.wsum += r.e * r.w; by.set(r.group, g);
    }
    const out = [];
    for (const [g, v] of by) out.push({ key: 'g' + g, group: g, major: D.groups[g].major, e: v.e, w: v.wsum / v.e });
    return out;
  }
  const F = D.history[areaId][String(year)];
  return F.g.map((g, i) => ({ key: 'g' + g, group: g, major: D.groups[g].major, e: F.e[i], w: F.t[i] / F.e[i] }));
}

// Share of jobs and wages by major group
function majorShares(curve, nMajors) {
  const out = Array.from({ length: nMajors }, (_, i) => ({ major: i, jobs: 0, wages: 0 }));
  for (const q of curve.pts) { out[q.row.major].jobs += q.jobShare; out[q.row.major].wages += q.wageShare; }
  return out;
}

if (typeof module !== 'undefined') module.exports = { lorenz, wageShareAt, readouts, latestRows, historyRows, majorShares };
