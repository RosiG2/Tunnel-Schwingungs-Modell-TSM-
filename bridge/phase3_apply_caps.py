#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3: fügt zusätzliche Nebenbedingungen in bridge/tsm_pg_facets_lifted.json hinzu:
- optionale Gruppen-OBERgrenze (UB) für 'core' (z.B. ≤ 0.60)
- pro-Zone Delta-Korridor: |x_i - b_i| ≤ TAU (z.B. TAU = 0.10)
  --> implementiert als zusätzliche zone-LB/UB-LIFTS (x_i >= b_i-TAU; x_i <= b_i+TAU)
Idempotent: überschreibt vorhandene gleichnamige Phase-3-Lifts.
"""
import json
from pathlib import Path

# === PARAMETER ===
CORE_UB = 0.60       # None, wenn nicht gewünscht
DELTA_TAU = 0.10     # maximale Abweichung pro Zone von b (in Anteilspunkten); None zum Deaktivieren
CORE_ZONES = ["kohärent", "regulativ"]  # Mitglieder der Gruppe 'core'

BR = Path(__file__).resolve().parents[1] / "bridge"
J  = BR / "tsm_pg_facets_lifted.json"

def one_hot(n, i, val=1.0):
    return [float(val) if j == i else 0.0 for j in range(n)]

def upsert(lifts, new, key):
    """Ersetze Lift mit gleichem 'meta.key' oder füge hinzu."""
    out = []
    replaced = False
    for L in lifts:
        if L.get("meta", {}).get("key") == key:
            out.append(new); replaced = True
        else:
            out.append(L)
    if not replaced:
        out.append(new)
    return out

def main():
    d = json.loads(J.read_text(encoding="utf-8"))
    names = list(map(str, d["names"]))
    b = [float(v) for v in d["b"]]
    n = len(names)
    cons = d.setdefault("constraints", {})
    lifts = cons.setdefault("lifts", [])

    # --- Gruppen-UB für 'core' ---
    if CORE_UB is not None:
        core_idx = [names.index(z) for z in CORE_ZONES if z in names]
        a = [0.0]*n
        for i in core_idx: a[i] = 1.0
        L = {
            "type": "ub",
            "scope": "group",
            "group": "core",
            "zones": [names[i] for i in core_idx],
            "a": a,
            "c": float(CORE_UB),
            "meta": {"phase": "3", "key": "p3_group_core_ub", "note": f"core ≤ {CORE_UB:.2f}"}
        }
        lifts = upsert(lifts, L, "p3_group_core_ub")

    # --- Delta-Korridor je Zone: |x_i - b_i| ≤ TAU ---
    if DELTA_TAU is not None:
        for i, z in enumerate(names):
            # LB: x_i >= max(0, b_i - TAU)  -->  -x_i <= -m  (a = -e_i, c = -m)
            m_lb = max(0.0, b[i] - DELTA_TAU)
            L_lb = {
                "type": "lb",
                "scope": "zone",
                "zone": z,
                "a": [-1.0 if j == i else 0.0 for j in range(n)],
                "c": -float(m_lb),
                "meta": {"phase": "3", "key": f"p3_zone_lb_{i}", "note": f"{z}: x >= {m_lb:.4f} (b-τ)"}
            }
            lifts = upsert(lifts, L_lb, f"p3_zone_lb_{i}")

            # UB: x_i <= min(1, b_i + TAU)  -->  +x_i <= M  (a = +e_i, c = M)
            m_ub = min(1.0, b[i] + DELTA_TAU)
            L_ub = {
                "type": "ub",
                "scope": "zone",
                "zone": z,
                "a": one_hot(n, i, 1.0),
                "c": float(m_ub),
                "meta": {"phase": "3", "key": f"p3_zone_ub_{i}", "note": f"{z}: x <= {m_ub:.4f} (b+τ)"}
            }
            lifts = upsert(lifts, L_ub, f"p3_zone_ub_{i}")

    cons["lifts"] = lifts
    mm = d.setdefault("meta", {})
    notes = mm.setdefault("notes", [])
    tag = f"Phase 3: core_ub={CORE_UB}, delta_tau={DELTA_TAU}"
    if tag not in notes: notes.append(tag)

    J.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] updated lifts with Phase 3 caps ->", J)

if __name__ == "__main__":
    main()
