# Methods — Gemeinsame Notation & Validierung


**Datenbasis.** Ausgehend von Spalten \(C,\,\Delta\varphi,\,\tau\) werden \(F_{\mathrm{res}}\), \(F_{\mathrm{cap}}\), \(B\), \(S\) und die Zonen mittels eines Cap‑Quantils (Default \(q=0{.}99\)) bestimmt.


**Skalenfreiheit.** \(B=\mathrm{ECDF}(F_{\mathrm{cap}})\) und \(S=1-B\) sind rangbasiert und damit robust gegenüber globalen Skalenfaktoren; \(\varepsilon\) (in Grad) verhindert Singularitäten bei \(\Delta\varphi\to 0\).


**Exportpfad.** Das gemeinsame Skalarfeld \(K\) wird standardmäßig als \(K=B\) verwendet (Alternative: Blend mit \(\lambda\)). Daraus folgen zwei gleichwertige Lesarten: (i) *Metric‑Stub* \(\delta g = a_1\,K\) und (ii) *Matter‑Stub* \(T^{(\mathrm{eff})}_{\mu\nu}\) mit \(\rho=\rho_0 K\), \(p=w\,\rho\).


**Validierung.** Der Validator prüft: Spaltenvollständigkeit, Wertebereiche, Identität \(S=1-B\), Zonenregel und optional einen Byte‑genauen Vergleich gegen Referenz‑Outputs. CI‑Workflows führen Compute→Export→Validation aus.


**Sensitivität.** Kleine Variationen um die Defaults (\(\pm\,\Delta\) in \(\varepsilon\), Cap‑Quantil, \(B\)‑Schwellen) ändern die Zonierung kontrolliert; die Stabilität wird als mittlere Übereinstimmung über das Raster berichtet.


**Visualisierung.** Aggregations‑CSVs liefern Verteilungen und Kennzahlen (Histogramme, Zonenanteile, Übergangsmatrix). Sie sind plotter‑agnostisch und für Audits reproduzierbar.


**Governance & Transparenz.** Alle Parameter stehen in JSON‑Defaults/Schema, alle Ausgaben sind CSV/JSON mit deterministischer Berechnung. So sind wissenschaftliche Replikation, Audits und spätere Publikation (inkl. Pre‑Registration) unterstützt.