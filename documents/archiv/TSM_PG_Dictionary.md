# TSM ↔ Positive Geometry – Mini‑Wörterbuch (v0.1)


**Zonen** (TSM): Indizes \(i=1..n\) mit Werten \(x_i\ge 0\).
**Positiver Raum**: \(\mathcal{P} = \{x\in\mathbb{R}^n_{\ge0}\,|\, Cx\le d, \; \mathbf{1}^\top x=1\;\text{(optional)}\}\).
**Facetten**: lineare Gleichungen (z. B. \(x_i=0\), Budget/Normalisierung, weitere Nebenbedingungen).
**Kanten/Adjazenzen**: Kopplungen/Abhängigkeiten zwischen Zonen (aus `R_estimates`).
**Resonanzgesetz (TSM)** ↔ **Residuen** der **kanonischen Form** \(\Omega(\mathcal{P})\) an Facetten/Unterfacetten.
**Baseline/Recommended**: zwei Punkte \(b,r\in\mathcal{P}\); der Verbindungsweg \([b,r]\subset\mathcal{P}\) „durchläuft“ Strukturen (aktive Facetten, Residuen).


## Konstruktion (praktisch)
1. **Normalisieren**: Skaliere Werte je Vektor auf Summe 1; erhalte \(b,r\in\Delta^{n-1}\) (Simplex).
2. **Nebenbedingungen**: Übersetze Zustands-/QC-Regeln in \(Cx\le d\) (H‑Darstellung).
3. **Kanonische Form**: Für Simplex/Polytop triangulieren; \(\Omega\) ist dlog‑artig (Symbolik, keine Metrik nötig).
4. **Residuen-Check**: Prüfe Factorization (Residuen addieren sich, Übergänge entlang Facetten).
5. **Mapping**: Kopplungen aus `R_estimates` → Gewichtungen von Facetten/Adjazenzen.


## Observables (Beispiele)
- **Facet‑Aktivität**: Facetten mit \(x_i\) nahe 0 entlang \([b,r]\).
- **Salienz pro Zone**: \(|r_i-b_i|\) und Einfluss aus Kopplungen.
- **Konservative Tests**: \(\sum_i x_i=1\), \(x_i\ge 0\), Monotonie ausgewählter Zonen.