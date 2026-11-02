#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

BR = Path(__file__).resolve().parents[1] / "bridge"
stats = json.loads((BR / "phase1_stats.json").read_text(encoding="utf-8"))

n = stats["zones"]
lb_b = stats["binds"]["lb_b"]; lb_r = stats["binds"]["lb_r"]
ub_b = stats["binds"]["ub_b"]; ub_r = stats["binds"]["ub_r"]
Ltot = stats["lifts"]["total"]; Lb = stats["lifts"]["bind_b"]; Lr = stats["lifts"]["bind_r"]

top = stats.get("top10", [])[:3]  # nur Top 3 für die Executive
top_lines = [f"- {t['zone']}: Δ={t['delta']:.6f} | rel={t['rel_change']:.3f} | b={t['b']:.6f} → r={t['r']:.6f}" for t in top]

md = f"""# Executive-Summary (Phase 1, RGN-Lifts; auto-generiert)

1. **Setup:** TSM im Simplex (Σx=1, x≥0); Phase 0-Kappen: xᵢ ≤ max(bᵢ,rᵢ)+0.05.
2. **RGN-Lifts aktiv:** Insgesamt **{Ltot}** Lift-Constraints eingezogen (zone/gruppenbasiert).
3. **Facettenkontakt:** LB/UB-Bindings — b@LB={lb_b}, r@LB={lb_r}, b@UB={ub_b}, r@UB={ub_r} (bei **{n}** Zonen).
4. **LIFT-Bindings:** gebunden an b: **{Lb}**, an r: **{Lr}**. Details: `bridge/facet_activations_phase1.json`.
5. **Top-Änderungen (b→r):**
{chr(10).join(top_lines) if top_lines else "- (keine Daten)"}

**Quellen:** `bridge/wegbericht_b_to_r_phase1.md`, `bridge/tsm_pg_bindings_phase1.csv`, `bridge/facet_activations_phase1.json`, `bridge/phase1_stats.md`.
"""
(BR / "README_exec_summary_phase1.md").write_text(md, encoding="utf-8")
print("[ok] wrote bridge/README_exec_summary_phase1.md")
