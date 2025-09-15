#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Re-Margin der per-Zone Obergrenzen in bridge/tsm_pg_facets_lifted.json:
- setzt margin = 0.02 (statt z. B. 0.05)
- aktualisiert constraints.upper_bounds[i].c = min(1.0, max(b_i, r_i) + 0.02)
"""
import json
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"

def main():
    if not J.exists():
        raise FileNotFoundError(f"{J} nicht gefunden. Bitte Phase-1 JSON in bridge/ ablegen.")

    d = json.loads(J.read_text(encoding="utf-8"))
    names = d.get("names") or []
    b = d.get("b") or []
    r = d.get("r") or []
    if not names or not b or not r:
        raise ValueError("JSON unvollständig: 'names', 'b', 'r' erforderlich.")

    margin = 0.02
    new_ubs = []
    n = len(names)
    for i in range(n):
        bi = float(b[i]); ri = float(r[i])
        ub = min(1.0, max(bi, ri) + margin)
        new_ubs.append({
            "i": i,
            "a": [1.0 if j == i else 0.0 for j in range(n)],
            "c": ub
        })

    d.setdefault("constraints", {})["upper_bounds"] = new_ubs
    d.setdefault("meta", {})["margin"] = margin
    notes = d.setdefault("meta", {}).setdefault("notes", [])
    if "Phase 2: margin→0.02" not in notes:
        notes.append("Phase 2: margin→0.02")

    J.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] Updated margin to 0.02 and recomputed upper_bounds ->", J)

if __name__ == "__main__":
    main()
