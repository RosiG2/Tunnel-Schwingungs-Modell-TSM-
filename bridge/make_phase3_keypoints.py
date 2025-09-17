cat > bridge/make_phase3_keypoints.py <<'PY'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt 5-Kernpunkte aus Phase 3★:
- liest: phase3_counts.md, phase3_r3_vs_rstar.csv, phase3_r3_vs_b.csv
- schreibt: KEYPOINTS_phase3.md
"""
from pathlib import Path
import re, csv

BR = Path(__file__).resolve().parents[1] / "bridge"
counts = (BR/"phase3_counts.md").read_text(encoding="utf-8")
vs_rS  = list(csv.DictReader((BR/"phase3_r3_vs_rstar.csv").open("r", encoding="utf-8")))
vs_b   = list(csv.DictReader((BR/"phase3_r3_vs_b.csv").open("r", encoding="utf-8")))

def topk(rows, key, k=3, reverse=True, fmt=None):
    rows = [r for r in rows if r.get(key) not in (None, "", "nan")]
    for r in rows:
        for f in ("r_star","r3","b",key):
            if f in r:
                try: r[f] = float(r[f])
                except: r[f] = float("nan")
    rows.sort(key=lambda r: r[key], reverse=reverse)
    out = []
    for r in rows[:k]:
        if fmt == "r3_vs_rS":
            out.append(f"- {r['zone']}: r★={r['r_star']:.6f} → r³={r['r3']:.6f} | Δ={r[key]:+.6f}")
        elif fmt == "r3_vs_b":
            out.append(f"- {r['zone']}: b={r['b']:.6f} → r³={r['r3']:.6f} | Δ={r[key]:+.6f}")
        else:
            out.append(f"- {r['zone']}: Δ={r[key]:+.6f}")
    return out

# Counts parsen
m1 = re.search(r"b@LB=(\d+),\s*r³@LB=(\d+),\s*b@UB=(\d+),\s*r³@UB=(\d+)", counts)
m2 = re.search(r"LIFT\(b\)=(\d+),\s*LIFT\(r³\)=(\d+)", counts)
b_lb=r_lb=b_ub=r_ub=lift_b=lift_r3=None
if m1: b_lb, r_lb, b_ub, r_ub = map(int, m1.groups())
if m2: lift_b, lift_r3 = map(int, m2.groups())

lines = ["# Phase 3★ – 5 Kernpunkte", ""]
# 1) Counts
if None not in (b_lb, r_lb, b_ub, r_ub, lift_b, lift_r3):
    lines += [
        "1) **Facetten- & LIFT-Counts**",
        f"   - b@LB={b_lb}, r³@LB={r_lb}, b@UB={b_ub}, r³@UB={r_ub}",
        f"   - LIFT(b)={lift_b}, LIFT(r³)={lift_r3}",
        ""
    ]

# 2–3) r³ vs r★
lines.append("2) **r³ vs r★ — Top-Anhebungen**")
lines += topk(vs_rS, "delta_r3_minus_rstar", k=3, reverse=True, fmt="r3_vs_rS") or ["- (keine)"]
lines.append("")
lines.append("3) **r³ vs r★ — Top-Absenkungen**")
lines += topk(vs_rS, "delta_r3_minus_rstar", k=3, reverse=False, fmt="r3_vs_rS") or ["- (keine)"]
lines.append("")

# 4–5) r³ vs b
lines.append("4) **r³ vs b — Top-Anhebungen**")
lines += topk(vs_b, "delta_r3_minus_b", k=3, reverse=True, fmt="r3_vs_b") or ["- (keine)"]
lines.append("")
lines.append("5) **r³ vs b — Top-Absenkungen**")
lines += topk(vs_b, "delta_r3_minus_b", k=3, reverse=False, fmt="r3_vs_b") or ["- (keine)"]
lines.append("")

(BR/"KEYPOINTS_phase3.md").write_text("\n".join(lines), encoding="utf-8")
print("[ok] wrote:", BR/"KEYPOINTS_phase3.md")
