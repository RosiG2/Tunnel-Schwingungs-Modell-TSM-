# Export: TSM → gemeinsame Physiknotation (v0.1)


Dieses Dokument ergänzt das Bridge‑Pack um **einen lauffähigen Exportpfad** aus `C,dphi,tau` → (F_res,F_cap,B,S) → K → einfache **GR‑Lesarten** (Metrik‑Stub *oder* effektiver Energie‑Impuls‑Tensor). Alles **ohne externe Abhängigkeiten**.


## Schnellstart
1. `python bridge/tsm_bridge_compute.py --in INPUT.csv --out computed.csv`
2. `python bridge/tsm_gr_exporter_v0.1.py --in computed.csv --out-prefix export/exp --mode matter --rho0 1.0 --w 0.0`


**Ergebnisse:**
- `export/exp_K_field.csv` — skalarer K‑Feld‑Export (aus B,S).
- `export/exp_T_eff.csv` — einfacher **T_{mu nu}^{(eff)}**‑Export (Staub/Fluid‑Stub).


> *Hinweis:* Wenn Du lieber den **Metrik‑Modus** testen willst, nutze `--mode metric`. Dann erzeugt der Exporter ein symbolisches Delta‑Metrik‑CSV (`exp_metric_stub.csv`).


## Parameter
- `--K-mode`: `B` (Default) oder `blend`: `K = (1-λ)·B + λ·(1-B)`, via `--lambda`.
- `--rho0`, `--w`: Dichte‑Skala und Zustandsgleichung (nur `--mode matter`).
- `--metric-a1,a2,a3`: Koeffizienten des Metrik‑Stubs (nur `--mode metric`).


## Minimaler E2E‑Test