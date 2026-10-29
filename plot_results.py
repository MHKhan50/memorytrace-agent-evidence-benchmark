"""Dependency-free SVG charts from the outputs folder."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COLOURS = {"provenance_gate": "#2a78d6", "strict_evidence": "#eb6834", "conflict_abstain": "#1f9e75"}


def _rows(name):
    return list(csv.DictReader((ROOT / "outputs" / name).open(encoding="utf-8")))


def create_chart():
    rows = _rows("summary.csv")
    W, H, left, top, pw, ph = 900, 560, 100, 70, 700, 390

    def x(v):
        return left + float(v) * pw

    def y(v):
        return top + (1 - float(v)) * ph
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" viewBox="0 0 {0} {1}">'.format(W, H),
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="450" y="32" text-anchor="middle" font-family="sans-serif" font-size="22">'
             'MemoryTrace: coverage vs stale-selection rate</text>']
    for t in range(0, 11, 2):
        v = t / 10
        parts.append('<line x1="{}" y1="{:.1f}" x2="{}" y2="{:.1f}" stroke="#dddddd"/>'.format(left, y(v), left + pw, y(v)))
        parts.append('<text x="{}" y="{:.1f}" text-anchor="end" font-family="sans-serif" font-size="13">{:.1f}</text>'.format(
            left - 15, y(v) + 5, v))
        parts.append('<text x="{:.1f}" y="{}" text-anchor="middle" font-family="sans-serif" font-size="13">{:.1f}</text>'.format(
            x(v), top + ph + 25, v))
    parts += ['<line x1="{0}" y1="{1}" x2="{0}" y2="{2}" stroke="black"/>'.format(left, top, top + ph),
              '<line x1="{0}" y1="{1}" x2="{2}" y2="{1}" stroke="black"/>'.format(left, top + ph, left + pw),
              '<text x="450" y="525" text-anchor="middle" font-family="sans-serif" font-size="16">Coverage</text>',
              '<text x="24" y="265" transform="rotate(-90 24 265)" text-anchor="middle" font-family="sans-serif" '
              'font-size="16">Stale-selection rate</text>']
    for i, r in enumerate(rows):
        cx, cy = x(r["coverage"]), y(r["stale_selection_rate"])
        parts.append('<circle cx="{:.1f}" cy="{:.1f}" r="7" fill="hsl({},55%,42%)"/>'.format(cx, cy, i * 85))
        parts.append('<text x="{:.1f}" y="{:.1f}" font-family="sans-serif" font-size="13">{}</text>'.format(
            cx + 10, cy - 9, r["policy"]))
    parts.append("</svg>")
    out = ROOT / "outputs" / "coverage_vs_risk.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def create_noise_chart():
    """Two panels against label noise: wrong answers, and unsafe memory use (unsupported + no consent + stale)."""
    rows = _rows("noise_sweep.csv")
    W, H = 920, 470
    panels = [("Wrong answers (share of all questions)", lambda r: float(r["wrong_answer_rate"]), 0.8, 70),
              ("Unsafe memory used (unverified, no consent or stale)",
               lambda r: float(r["unsupported_rate"]) + float(r["nonconsensual_rate"]) + float(r["stale_rate"]), 0.2, 500)]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" viewBox="0 0 {0} {1}" '
             'font-family="Helvetica, Arial, sans-serif">'.format(W, H),
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<text x="70" y="30" font-size="18" fill="#1f1e1c">MemoryTrace: what happens when the labels are wrong</text>']
    top, bottom, pw = 80, 380, 360
    xs = sorted({float(r["label_noise"]) for r in rows})
    for title, fn, ymax, left in panels:
        def px(v):
            return left + pw * v / max(xs)

        def py(v):
            return bottom - (bottom - top) * v / ymax
        parts.append('<text x="{}" y="{}" font-size="13" fill="#1f1e1c">{}</text>'.format(left, top - 12, title))
        for i in range(5):
            v = ymax * i / 4
            parts.append('<line x1="{}" x2="{}" y1="{:.1f}" y2="{:.1f}" stroke="#e6e5e1"/>'.format(left, left + pw, py(v), py(v)))
            parts.append('<text x="{}" y="{:.1f}" font-size="11" text-anchor="end" fill="#52514e">{:.0%}</text>'.format(
                left - 6, py(v) + 4, v))
        for v in xs:
            parts.append('<text x="{:.1f}" y="{}" font-size="11" text-anchor="middle" fill="#52514e">{:.0%}</text>'.format(
                px(v), bottom + 18, v))
        parts.append('<text x="{}" y="{}" font-size="12" text-anchor="middle" fill="#52514e">Label error rate</text>'.format(
            left + pw // 2, bottom + 38))
        for pol, col in COLOURS.items():
            pts = [(px(float(r["label_noise"])), py(fn(r))) for r in rows if r["policy"] == pol]
            parts.append('<polyline fill="none" stroke="{}" stroke-width="2.5" points="{}"/>'.format(
                col, " ".join("{:.1f},{:.1f}".format(a, b) for a, b in pts)))
            for a, b in pts:
                parts.append('<circle cx="{:.1f}" cy="{:.1f}" r="4" fill="{}"/>'.format(a, b, col))
    for i, (pol, col) in enumerate(COLOURS.items()):
        x0 = 70 + i * 220
        parts.append('<rect x="{}" y="{}" width="14" height="4" fill="{}"/>'.format(x0, H - 22, col))
        parts.append('<text x="{}" y="{}" font-size="12" fill="#1f1e1c">{}</text>'.format(x0 + 20, H - 16, pol))
    parts.append("</svg>")
    out = ROOT / "outputs" / "noise_effects.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


if __name__ == "__main__":
    print("Wrote", create_chart().relative_to(ROOT))
