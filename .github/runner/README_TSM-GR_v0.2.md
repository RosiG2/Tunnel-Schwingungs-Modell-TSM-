# TSM–GR v0.2 – Runbook / README


Dieses README beschreibt, wie du **tsmgr_v02.py** verwendest (Ein‑Datei‑Runner: Modell, Zonenlogik, Tests, Sweeps). Es gibt **keine externen Abhängigkeiten** außer Python ≥3.9.


---


## 1) Dateien
- **Pflicht:** `tsmgr_v02.py` (dieser Runner)
- **Optional:** `params.json` (Parameter‑Overrides), `grid.json` (eigenes Sweep‑Grid)


**Outputs (pro Run):**
- `trajectory.csv` – Zeitreihe über τ: Position, Geschwindigkeit, K, ε, φ/varphi, Kdot, Zone
- `zones.csv` – Zonensequenz mit Dwell‑Zähler
- `run.log.jsonl` – Log pro Schritt (JSON Lines)
- (bei Sweeps) `sweep_summary.csv` – Kennzahlen pro Fall


---


## 2) Quickstart
```bash
# Einzellauf mit Defaults → ./out
python tsmgr_v02.py run --out ./out


# Sweep mit eingebautem Grid → ./out_sweeps
python tsmgr_v02.py sweep --out ./out_sweeps


# τ‑Reparametrisations‑Check (a=2) → ./out_checks
python tsmgr_v02.py taucheck --out ./out_checks


# Stabilitäts‑Guard → ./out_checks
python tsmgr_v02.py stabcheck --out ./out_checks