# TSM ↔ Positive Geometry — Phase 1 Executive Summary (RGN-Lifts aktiv)

**Stand**: automatisch erstellt für das Repo *Tunnel-Schwingungs-Modell-TSM-* (Ordner `/bridge`).  
**Kern-Artefakte (Phase 1):**
- `bridge/wegbericht_b_to_r_phase1.md` – Wegbericht b→r inkl. Facetten‑/Lift‑Status
- `bridge/tsm_pg_bindings_phase1.csv` – Tabelle aller Zonen mit Bindings (LB/UB/LIFT)
- `bridge/facet_activations_phase1.json` – Liste aller RGN‑Lift‑Ungleichungen mit Slack/Binding (b/r)

## TL;DR
- b und r liegen im **Simplex** (Σx=1, x≥0).  
- **Phase‑0** brachte pro‑Zone Oberkappen \(x_i ≤ \max(b_i,r_i)+0.05\).  
- **Phase‑1** zieht **RGN‑Lifts** ein (Mindestanteile, Gruppenkappen, zonale Bounds).  
- Der Weg b→r kann nun **zusätzliche aktive Facetten** berühren (LB/UB/LIFT).

> **Hinweis:** Exakte Zahlen variieren mit den RGN‑Regeln. Für eine kompakte Statistik kann `bridge/quickstats_phase1.py`
> ausgeführt werden – erzeugt `bridge/phase1_stats.md` & `bridge/phase1_stats.json`.

## Empfohlene Verlinkungen
- Wegbericht: `bridge/wegbericht_b_to_r_phase1.md`
- Bindings (CSV): `bridge/tsm_pg_bindings_phase1.csv`
- Lift‑Aktivierungen (JSON): `bridge/facet_activations_phase1.json`

## Interpretation (Kurzleitfaden)
- **LB (x_i=0)**: Zone in b oder r an der unteren Facette → potenzielle Abschaltung.  
- **UB (x_i=UB)**: Zone in b oder r an der Kappe → Limit/Sättigung.  
- **LIFT[..]**: RGN‑Regel aktiv (zonen‑/gruppenbasiert). Tags zeigen, welche Regel b/r bindet.
