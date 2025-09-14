# Wegbericht b → r (Simplex + gehobene Obergrenzen)

- Zonen: **4**
- Facetten-Ansatz: 0 ≤ x_i, Σx_i=1; per‑Zone UB = max(b_i, r_i)+0.05 (clamped ≤1).
- Facettenkontakt (untere Grenze x_i=0) an b oder r: **0** Zonen.
- Obergrenze aktiv (x_i = UB) an b oder r: **0** Zonen.

## Top‑Änderungen (mit Facettenstatus)
- nan: Δ=0.530400 | rel=nan | b=0.000000 → r=0.530400 [b@LB, r@LB, b@UB, r@UB]
- fragmentiert: Δ=-0.227864 | rel=-0.684 | b=0.333333 → r=0.105469
- kohärent: Δ=-0.151268 | rel=-0.454 | b=0.333333 → r=0.182065
- regulativ: Δ=-0.151268 | rel=-0.454 | b=0.333333 → r=0.182065

## Hinweise
- LB = Untere Facette (x_i=0), UB = obere Zonenkappe (max(b_i,r_i)+0.05).
- Ein LB/UB-Flag an r zeigt, dass die Empfehlung die jeweilige Grenze **berührt**; das kann ein aktives Residuum signalisieren.
- Nächster Schritt: RGN‑Regeln einziehen (Gruppenkappen, Mindestanteile) und Weg entlang aktivierter Facetten segmentieren.