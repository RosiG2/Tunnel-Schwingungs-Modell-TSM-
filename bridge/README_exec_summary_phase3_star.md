# Executive-Summary — Phase 3★ (b → r³)

## Facetten- & LIFT-Counts
- b@LB=1, r³@LB=0, b@UB=0, r³@UB=0
- LIFT(b)=1, LIFT(r³)=1

## r³ vs r★ — Top-Anhebungen
- fragmentiert: r★=0.105469 → r³=0.315641 | Δ=0.210172
- kohärent: r★=0.182065 → r³=0.302179 | Δ=0.120114
- regulativ: r★=0.182065 → r³=0.302179 | Δ=0.120114
- nan: r★=0.530400 → r³=0.080000 | Δ=-0.450400

## r³ vs r★ — Top-Absenkungen
- nan: r★=0.530400 → r³=0.080000 | Δ=-0.450400
- kohärent: r★=0.182065 → r³=0.302179 | Δ=0.120114
- regulativ: r★=0.182065 → r³=0.302179 | Δ=0.120114
- fragmentiert: r★=0.105469 → r³=0.315641 | Δ=0.210172

## r³ vs b — Top-Anhebungen
- nan: b=0.000000 → r³=0.080000 | Δ=0.080000
- fragmentiert: b=0.333333 → r³=0.315641 | Δ=-0.017692
- kohärent: b=0.333333 → r³=0.302179 | Δ=-0.031154
- regulativ: b=0.333333 → r³=0.302179 | Δ=-0.031154

## r³ vs b — Top-Absenkungen
- regulativ: b=0.333333 → r³=0.302179 | Δ=-0.031154
- kohärent: b=0.333333 → r³=0.302179 | Δ=-0.031154
- fragmentiert: b=0.333333 → r³=0.315641 | Δ=-0.017692
- nan: b=0.000000 → r³=0.080000 | Δ=0.080000

## Artefakte
- Bindings r³: `bridge/tsm_pg_bindings_phase3_star.csv`
- r³ vs r★: `bridge/phase3_r3_vs_rstar.csv`
- r³ vs b:  `bridge/phase3_r3_vs_b.csv`

## Hinweise (heuristisch)
- Große Abweichung r³ vs r★: Δ-Korridor (τ) zu streng/locker? CORE_UB anpassen.