# PGKM-014 – Intrinsische Rank-2-Lösung und Full-C-Repräsentation

**Forschungsstatus:** `NONCANONICAL_RESEARCH_SYNTHESIS`
**Geltungsbereich:** 90330, reduziert QQ; unabhängige Full-C-Repräsentationsgrenze

## Forschungsfrage und Ausgangspunkt

Die Schur-Rücksubstitution arbeitet ohne det(K_Schur), beweist aber nicht allein 64D Full-C.

## Definition und Prüfgegenstand

90330, reduziert QQ; unabhängige Full-C-Repräsentationsgrenze

## Ergebnisse und Geltung

- **PGKC-029 [G3_LEMMA_MODAL]** Intrinsische modale Rank-2-Rücksubstitution lässt sich im reduzierten QQ-Modell ohne Division durch det(K_Schur) durchführen. *[ORIGINAL_LEMMA_GELESEN]*
- **PGKC-030 [REDUCED_ONLY]** Das nachgereichte G3-Lemma grenzt einen behaupteten reduced-QQ-Rootcount=3 ausdrücklich vom exakten 64D Full-C-SC-Satz ab. *[ORIGINAL_LEMMA_GELESEN]*

## Gegenbefunde und Grenzen

- **Grenze zu PGKC-029:** Keine automatische 64D Full-C-Zertifikation.
- **Grenze zu PGKC-030:** Beweis- und Repräsentationsobjekte nicht verschmelzen.

## Ableitung und Interpretation

Die Beziehungen gelten entsprechend ihrem angegebenen Typ und Geltungsbereich.
**Tragender Schur-Rechenschritt:** Der Originaltext konstruiert für jede modale Zeile `q_j=(A_j-rB_j)/(2 ε(μ_j−ξ))`, `z_(2j)=(B_j-bq_j)/d`, womit `(q_j,z_(2j)) K_j=(A_j,B_j)` folgt, ohne Division durch `det(K_Schur)`. Voraussetzung sind die separat angegebenen Nichtdegenerationsstrata. Die Zahl 3 der echten reduzierten intrinsischen Rank-2-Lösungen ist kein automatisch gleiches Objekt wie ein exact full-64D-SC-Satz. Quelle: `SRC-014`.
- `E028` → `PGKC-030` **BEWEIS_SCOPE**: Die modale Inversion erfasst nicht allein die Full-C-64D-Repräsentationsgenauigkeit. *(QUELLENGETRAGEN)*
- `E036` → `PGKC-001` **NICHT_PHYSISCHE_BEWEISUEBERTRAGUNG**: Exakte reduktive QQ-Lösung und emergente 3D-Geometrie sind verschiedene Problemstellungen. *(GELTUNGSUNTERSCHIED)*

## Fachliche Beziehungen

- [PGKM-001 – Reversibler Ausgangskern und historische Schutzgrenzen](PGKM-001.md)

## TSM-Anschluss

Kein quellenbelegter TSM-Fachanschluss im Pilot zugewiesen.

## Offene Gegenprüfungen

- Zuerst die jeweils ausgewiesenen historischen Geltungs- und Reproduktionsgrenzen schließen, bevor eine stärkere Wirkung behauptet wird.

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-029`** (FORMAL_BEGRENZT; `G3_LEMMA_MODAL`): Intrinsische modale Rank-2-Rücksubstitution lässt sich im reduzierten QQ-Modell ohne Division durch det(K_Schur) durchführen.
- **`PGKC-030`** (GELTUNG; `REDUCED_ONLY`): Das nachgereichte G3-Lemma grenzt einen behaupteten reduced-QQ-Rootcount=3 ausdrücklich vom exakten 64D Full-C-SC-Satz ab.
- **`PGKC-275`** (FORMAL; `A6_3_SYMBOLIC_IDENTITY_PASS`): Die lokale 2×2-Modalrücksubstitution des G3-Lemmas ist in A6/3 exakt symbolisch nachgerechnet: beide Restkomponenten identisch null.
- **`PGKC-276`** (STATUS_GUARD; `HISTORICAL_CLAIM_NOT_RERUN`): Das G3-Original enthält die behauptete reduced-QQ-Drei-Root-Vollständigkeit, grenzt sie aber selbst vom 64D Full-C-Satz ab; A6/3 hat nur lokale Modalalgebra nachgerechnet.

## Quellenstatus

- `SRC-014`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0021](../forschung/B02.md#integration-find-0021)** · PGK-0.42E / G20R / G20E / G22 · `VERIFIED_DP_PASS / G22-T REPRESENTATION_STOP`
- **[INTEGRATION-FIND-0022](../forschung/B02.md#integration-find-0022)** · PGK-0.43A2YE / BS1–BS3 / FULLC-90330 · `EXACT_PASS / SC_COUNT=3`
- **[INTEGRATION-FIND-0023](../forschung/B02.md#integration-find-0023)** · PGK-0.43A2YE / EventGerm_C · `EVENTGERM_INTERSECTION=1 / EXACT+VERIFIED_DP_IV`
- **[INTEGRATION-FIND-0024](../forschung/B02.md#integration-find-0024)** · PGK-0.43A2YF · `EXACT SCALAR RESPONSE`
- **[INTEGRATION-FIND-0025](../forschung/B02.md#integration-find-0025)** · PGK-0.43A2YG · `EXACT SIGN-ONLY NEGATIVSATZ`
- **[INTEGRATION-FIND-0026](../forschung/B02.md#integration-find-0026)** · PGK-0.43A2YH · `VERIFIED-IV SCALAR / BINDING PASS / MAXIMAL CONTRACTION FAIL`
- **[INTEGRATION-FIND-0027](../forschung/B02.md#integration-find-0027)** · PGK-0.43A2YI · `EXACT SUCCESSOR RANK / SELECTOR EXCLUDED`
- **[INTEGRATION-FIND-0028](../forschung/B02.md#integration-find-0028)** · PGK-0.43A2YJ · `ROBUST-DP PASS / A2YI INTERPRETATION SUPERSEDED`
- **[INTEGRATION-FIND-0029](../forschung/B02.md#integration-find-0029)** · PGK-0.43A2YE-RQ / reduced-QQ · `EXACT_QQ_RESOLVENT / RESET_REGRESSION_PASS; globale Vollständigkeit im RQ-Paket OPEN`
- **[INTEGRATION-FIND-0099](../forschung/B08.md#integration-find-0099)** · PGK-0.43A2YP · `CROSS_ENDPOINT_REPLAY_PASS / SC_NOT_CLAIMED`
