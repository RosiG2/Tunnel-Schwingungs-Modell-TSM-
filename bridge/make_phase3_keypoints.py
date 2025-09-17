python - <<'PY'
from pathlib import Path
content = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt 5 Kernpunkte aus Phase 3★:
- liest: phase3_counts.md, phase3_r3_vs_rstar.csv, phase3_r3_vs_b.csv
- schreibt: KEYPOINTS_phase3.md
"""
from pathlib import Path
import re, csv

BR = Path(__file__).resolve().parents[1] / "bridge"
counts_p = BR/"phase3_counts.md"
vs_rS_p  = BR/"phase3_r3_vs_rstar.csv"
vs_b_p   = BR/"phase3_r3_vs_b.csv"
out_p    = BR/"KEYPOINTS_phase3.md"

def load_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def topk(rows, key, k=3, reverse=True, mode=""):
    rows = [dict(r) for r in rows if r.get(key) not in (None, "", "nan")]
    for r in rows:
        for f in ("r_star","r3","b",key):
            if f in r:
                try: r[f] = float(r[f])
                except: r[f] = float("nan")
    rows.sort(key=lambda r: r.get(key, float("nan")), reverse=reverse)
    out = []
    for r in rows[:k]:
        if mode == "r3_vs_rS":
            out.append(f"- {r['zone']}: r★={r.get('r_star', float('nan')):.6f} → r³={r.get('r3', float('nan')):.6f} | Δ={r.get(key, float('nan')):+.6f}")
        elif mode == "r3_vs_b":
            out.append(f"- {r['zone']}: b={r.get('b', float('nan')):.6f} → r³={r.get('r3', float('nan')):.6f} | Δ={r.get(key, float('nan')):+.6f}")
        else:
            out.append(f"- {r['zone']}: Δ={r.get(key, float('nan')):+.6f}")
    return out

# Inputs laden
counts = counts_p.read_text(encoding="utf-8")
vs_rS  = load_csv(vs_rS_p)
vs_b   = load_csv(vs_b_p)

# Counts parsen
m1 = re.search(r"b@LB=(\\d+),\\s*r³@LB=(\\d+),\\s*b@UB=(\\d+),\\s*r³@UB=(\\d+)", counts)
m2 = re.search(r"LIFT\\(b\\)=(\\d+),\\s*LIFT\\(r³\\)=(\\d+)", counts)
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
else:
    lines += ["1) **Facetten- & LIFT-Counts** – (nicht gefunden)", ""]

# 2–3) r³ vs r★
lines.append("2) **r³ vs r★ — Top-Anhebungen**")
lines += topk(vs_rS, "delta_r3_minus_rstar", k=3, reverse=True,  mode="r3_vs_rS") or ["- (keine)"]
lines.append("")
lines.append("3) **r³ vs r★ — Top-Absenkungen**")
lines += topk(vs_rS, "delta_r3_minus_rstar", k=3, reverse=False, mode="r3_vs_rS") or ["- (keine)"]
lines.append("")

# 4–5) r³ vs b
lines.append("4) **r³ vs b — Top-Anhebungen**")
lines += topk(vs_b, "delta_r3_minus_b", k=3, reverse=True,  mode="r3_vs_b") or ["- (keine)"]
lines.append("")
lines.append("5) **r³ vs b — Top-Absenkungen**")
lines += topk(vs_b, "delta_r3_minus_b", k=3, reverse=False, mode="r3_vs_b") or ["- (keine)"]
lines.append("")

out_p.write_text("\\n".join(lines), encoding="utf-8")
print("[ok] wrote:", out_p)
'''
Path('bridge/make_phase3_keypoints.py').write_text(content, encoding='utf-8')
print("[ok] wrote clean file bridge/make_phase3_keypoints.py")
PY
