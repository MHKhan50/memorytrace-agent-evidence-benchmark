"""Create a dependency-free SVG plot from outputs/summary.csv."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = list(csv.DictReader((ROOT / "outputs" / "summary.csv").open(encoding="utf-8")))
if not rows:
    raise SystemExit("No summary rows. Run python3 run_benchmark.py first.")
W, H, left, top, pw, ph = 900, 560, 100, 70, 700, 390
def x(v): return left + float(v) * pw
def y(v): return top + (1 - float(v)) * ph
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<text x="450" y="32" text-anchor="middle" font-family="sans-serif" font-size="22">MemoryTrace: coverage vs stale-selection rate</text>']
for t in range(0, 11, 2):
    v = t / 10
    parts.append(f'<line x1="{left}" y1="{y(v):.1f}" x2="{left+pw}" y2="{y(v):.1f}" stroke="#dddddd"/>')
    parts.append(f'<text x="{left-15}" y="{y(v)+5:.1f}" text-anchor="end" font-family="sans-serif" font-size="13">{v:.1f}</text>')
    parts.append(f'<text x="{x(v):.1f}" y="{top+ph+25}" text-anchor="middle" font-family="sans-serif" font-size="13">{v:.1f}</text>')
parts += [f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ph}" stroke="black"/>',
          f'<line x1="{left}" y1="{top+ph}" x2="{left+pw}" y2="{top+ph}" stroke="black"/>',
          f'<text x="450" y="525" text-anchor="middle" font-family="sans-serif" font-size="16">Coverage</text>',
          f'<text x="24" y="265" transform="rotate(-90 24 265)" text-anchor="middle" font-family="sans-serif" font-size="16">Stale-selection rate</text>']
for i, r in enumerate(rows):
    cx, cy = x(r["coverage"]), y(r["stale_selection_rate"])
    label = r["policy"]
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="hsl({i*85},55%,42%)"/>')
    parts.append(f'<text x="{cx+10:.1f}" y="{cy-9:.1f}" font-family="sans-serif" font-size="13">{label}</text>')
parts.append('</svg>')
out = ROOT / "outputs" / "coverage_vs_risk.svg"
out.write_text("\n".join(parts), encoding="utf-8")
print(f"Wrote {out.relative_to(ROOT)}")
