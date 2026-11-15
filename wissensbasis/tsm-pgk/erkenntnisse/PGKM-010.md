# PGKM-010 – Konfigurationsprofil, FRE und Äquivalenz

**Forschungsstatus:** `NONCANONICAL_RESEARCH_SYNTHESIS`
**Geltungsbereich:** 0.141, FRE-01, ID-freie Funktionsäquivalenz

## Forschungsfrage und Ausgangspunkt

Validierte Konfigurationserfassung ist kein Beweis von prospektiver Additionality oder abgeschlossener FRE-Verifikation.

## Definition und Prüfgegenstand

0.141, FRE-01, ID-freie Funktionsäquivalenz

## Ergebnisse und Geltung

- **PGKC-020 [RECOVERY_QUALIFIED]** Der wiederhergestellte 0.141-Freeze wurde ausdrücklich neu aus Discovery und Auftrag rekonstruiert; er ist nicht byteidentisch zum verlorenen Originalfreeze. *[ORIGINAL_PROVENIENZ_GELESEN]*
- **PGKC-021 [INCOMPLETE__PAUSED]** FRE-01 wurde in Richtung möglicher ID-freier Äquivalenz begonnen, aber Verification A/B nicht freigegeben. *[QUELLENAUDIT_BERICHT]*

## Gegenbefunde und Grenzen

- **PGKC-019 [OUTCOME_C0__NO_CONFIGURATION_ADDITIONALITY]** PGK-0.141: Die Konfigurationsbeschreibung bleibt sinnvoll, trägt aber keine replicierte vorausschauende Konfigurations-Additionality.
- **Grenze zu PGKC-019:** Configuration fingerprint ≠ unabhängig diskriminierbare Funktion.
- **Grenze zu PGKC-020:** Recovery und Originalbytes separat klassifizieren.
- **Grenze zu PGKC-021:** Keine positive unabhängige vollständige FRE-A/B-Reproduktion.

## Ableitung und Interpretation

Die Beziehungen gelten entsprechend ihrem angegebenen Typ und Geltungsbereich.
**Konfigurationsprofil ≠ Zusatzinformation:** Das 0.141-Original bejaht hinreichende One-step-Coverage, aber keine Variante überschreitet in beiden Held-out-Blöcken die serielle Null-Grenze. `C1` ist negativ; daraus kann `C2` nicht unabhängig als positive neue Regenerationsmechanik gezogen werden. Auch die spätere Freeze-Recovery besitzt eine eigene Provenienz, keine ursprüngliche Byteidentität. Quelle: `SRC-020`, `SRC-021`.
- `E019` → `PGKC-020` **PROVENIENZ_GUARD**: 0.141-Runs und spätere Recovery-Freeze dürfen nicht als bytegleiche Ursprungsinstanz gelten. *(PROVENIENZ)*
- `E020` → `PGKC-021` **MOTIVIERT**: Zu fingerprintnahe Rollenlogik motiviert ID-freie Reachability, ohne vollständiges FRE-Resultat zu liefern. *(HISTORISCHE_ENTWICKLUNG)*
- `E021` → `PGKC-022` **NEUER_PRUEFGEGENSTAND**: FRE-Limits und WR-Typen sind kein identisches Testobjekt. *(GELTUNGSUNTERSCHIED)*
- `E034` → `PGKC-031` **NICHT_IDENTISCH**: Ein noch offenes identitätsfreies Replikationsprogramm ist kein formaler Typvertrag und umgekehrt. *(GELTUNGSUNTERSCHIED)*

## Fachliche Beziehungen

- [PGKM-009 – Vorhersehbarkeit ohne Informationsleck](PGKM-009.md)
- [PGKM-011 – Gewichtete Erreichbarkeit und BRW-Provenienz](PGKM-011.md)
- [PGKM-015 – Geschichtete Funktionsgrammatik und TSM-Konkordanz](PGKM-015.md)

## TSM-Anschluss

- **TSM-149:** Begrifflicher Anschluss (ohne eigenständigen empirischen Nachweis).

## Offene Gegenprüfungen

- Zuerst die jeweils ausgewiesenen historischen Geltungs- und Reproduktionsgrenzen schließen, bevor eine stärkere Wirkung behauptet wird.

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-019`** (NEGATIV; `OUTCOME_C0__NO_CONFIGURATION_ADDITIONALITY`): PGK-0.141: Die Konfigurationsbeschreibung bleibt sinnvoll, trägt aber keine replicierte vorausschauende Konfigurations-Additionality.
- **`PGKC-020`** (PROVENIENZ; `RECOVERY_QUALIFIED`): Der wiederhergestellte 0.141-Freeze wurde ausdrücklich neu aus Discovery und Auftrag rekonstruiert; er ist nicht byteidentisch zum verlorenen Originalfreeze.
- **`PGKC-021`** (OFFEN; `INCOMPLETE__PAUSED`): FRE-01 wurde in Richtung möglicher ID-freier Äquivalenz begonnen, aber Verification A/B nicht freigegeben.
- **`PGKC-279`** (NEGATIV; `HISTORICAL_DECISION_RECONFIRMED`): 0.141 bestätigt den Quellstatus OUTCOME_C0: kein typisiertes Regime besteht den Konfigurations-Additionality-Nullguard repliziert in beiden Held-outs.
- **`PGKC-299`** (GELTUNGSGRENZE; `KANONISCHER_STATUS_ZITIERT`): Eine vollständige v1.39 Schichtgrammatik liegt als formaler Typvertrag vor; die kanonische Instantiierung ist ausdrücklich nicht geschlossen.

## Quellenstatus

- `SRC-015`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-020`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-021`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden
- `SRC-023`: nur Quellenreferenz; Original im öffentlichen Bestand nicht vorhanden

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0001](../forschung/B01.md#integration-find-0001)** · BASE-v1.39 · `FGT_C__COMPANION_CONFIRMED / FORMAL_LAYERED_TYPE_CONTRACT / CANONICAL_INSTANTIATION_NOT_CLOSED`
- **[INTEGRATION-FIND-0038](../forschung/B04.md#integration-find-0038)** · FRE-01 / Recovery-Checkpoint · `RECOVERY_DEFINITIONS_FIXED / ORIGINAL_DEFINITION_LOCK_BYTES_NOT_RECOVERED`
- **[INTEGRATION-FIND-0039](../forschung/B04.md#integration-find-0039)** · FRE-01B / 107300–107301 × tr/eta · `PASS__PERSISTED / DISCOVERY_SINGLE_JOB_ONLY`
- **[INTEGRATION-FIND-0040](../forschung/B04.md#integration-find-0040)** · FRE-01B / BLOCKED-Checkpoint · `FRE_01B_BLOCKED__FRESH_REPLAY_ARTIFACTS_UNAVAILABLE`
- **[INTEGRATION-FIND-0093](../forschung/B07.md#integration-find-0093)** · PGK-0.141 · `OUTCOME_C0__NO_CONFIGURATION_ADDITIONALITY`
