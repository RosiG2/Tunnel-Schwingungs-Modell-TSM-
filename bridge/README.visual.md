# Visual & Methods: Aggregations für Plot/Reporting


Dieses Modul erzeugt **plot-fertige CSVs** aus `computed.csv` und liefert eine kurze **Methods-Seite** für Veröffentlichungen/Readmes.


## Quickstart

python bridge/tsm_bridge_visualize_v0.1.py --in /tmp/comp.csv --out-prefix export/vis
--id-col "" --time-col ""

**Outputs** (alle CSV):
- `*_zone_distribution.csv` — Zonenanteile (count, pct)
- `*_K_hist_overall.csv` — Histogramm K (20 Bins [0,1])
- `*_K_stats_by_zone.csv` — Kennzahlen je Zone (min, p10, median, mean, p90, max, count)
- `*_K_hist_by_zone.csv` — Histogramm je Zone (20 Bins)
- `*_transition_matrix.csv` — Übergangsmatrix (optional; benötigt `--id-col` und `--time-col`)
- `*_coherence_index.csv` — Kohärenz‑Index = pct(kohärent) − pct(fragmentiert)


## Optionen
- `--id-col` (optional): Entitätenkennung (z. B. Person/Objekt). Wenn gesetzt **und** `--time-col` gesetzt ist, wird eine Übergangsmatrix erstellt.
- `--time-col` (optional): Zeitspalte (aufsteigend sortierbar). Unterstützt ISO‑Datum, Zahl oder beliebige sortierbare Strings.


## Plot‑Hinweise
- CSVs sind so gestaltet, dass Standard‑Plotter (Excel, Pandas/Matplotlib, Vega‑Lite) ohne weitere Transformationen funktionieren.
- Bins sind gleichbreit; Labels liegen in Spalten `bin_lo`, `bin_hi`.