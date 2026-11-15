# PGKM-029 – Exakte Paarverlustbilanz im nativen E/C-Partitionskern

**Forschungsstatus:** `DERIVED_FORMAL_RESULT_NOT_EMPIRICAL`
**Geltungsbereich:** A6N-01-Korollar, festes U0; Merge- und Singleton-Geburt

## Ausgangsfrage und Bezug

A6N-01 beweist: Sind zwei am Anfang benannte Altatome einmal in einer Komponente vereinigt, trennt ein nativer E-/C-Nachfolgeschritt sie nicht wieder. Offen bleibt damit die konkrete Größe dieses Verlustes bei einem C-Schritt. Grundlage: `../beweise/A6N-T1_SRC-078.md` (A6N-T1).

## Formalsatz PGK-029-T1

Sei `U0` die feste Menge der ursprünglichen alten atomaren IDs und `P` eine Partition des aktuellen Atomuniversums. Für jeden Block `B` sei `n_B=|B∩U0|`. Die Anzahl getrennt adressierbarer alter Paare ist:

```text
S_U0(P) = binom(|U0|,2) - SUM_{B in P} binom(n_B,2).
```

Vereinigt ein zulässiger C-Schritt verschiedene Blöcke `B1, ..., Bk`, dann gilt exakt:

```text
S_U0(P_nach) - S_U0(P_vor)
  = - SUM_{1 <= i < j <= k} n_i*n_j.
```

Die Erzeugung eines neuen Singletons mittels E ändert `S_U0` nicht.

**Folgerung:** `S_U0` fällt bei C *genau dann* strikt, wenn wenigstens zwei der zusammengeführten Blöcke Altatome enthalten. Ein C ohne alte Atome auf wenigstens zwei Seiten kann in dieser Metrik verlustfrei bleiben.

## Beweis

Es gibt insgesamt `binom(|U0|,2)` ungeordnete Altatompaare. Jedes Paar liegt entweder in zwei getrennten Partitionsklassen oder vollständig innerhalb *einer* Klasse. Letztere werden ohne Überschneidung durch `sum_B binom(n_B,2)` gezählt. Dies beweist die erste Gleichung.

Bei einer C-Vereinigung wird die Anzahl schon vereinigter Altpaare um

```text
binom(n_1+...+n_k,2) - SUM_i binom(n_i,2)
= SUM_{i<j} n_i*n_j
```

größer. Genau um diese Anzahl nimmt `S_U0` ab. Bei E entsteht ein Block mit `n_B=0`, und alle bisherigen `n_B` bleiben erhalten. Damit ist die Altpaarbilanz invariant. Aus `n_i>=0` folgt das strikte Kriterium. ∎

## Verbindung zur vorhandenen Forschung

Der A6N-01-Bericht nennt für einen ausgewählten POS-C-Schritt `95→93` und für STOP `49→46`. Das bedeutet **unter diesen dokumentierten Voraussetzungen** den Verlust von zwei bzw. drei getrennten Altatom-Paaradressen. Die neue Formel berechnet nicht aus eigenständig nachgeladenen Originalzuständen, *welche* konkreten Blöcke diesen Verlust hervorriefen. Die angeführten historischen Zahlen werden hier nicht als unabhängig nachgerechnet ausgegeben.

Eine E-Geburt kann die Zahl aller unterscheidbaren aktuellen Atompaare erhöhen. Sie erzeugt jedoch kein neues Paar aus zwei *ursprünglich festgelegten* und bereits vereinigten Altatomen. Diese getrennte Buchführung ist sowohl für Funktionsträgerwechsel als auch für Regenrationsansprüche wichtig.

## Gegenrichtungen und Grenzen

- Verlieren alte Portadressen ihre Unterscheidbarkeit, ist damit eine neue, *anders typisierte* Ersatzorganisation nicht ausgeschlossen.
- Zeigt die alte Paarbilanz keinen Verlust, folgt daraus nicht, dass volle Funktion, Antwort oder Zukunftsverhalten erhalten bleiben.
- Die Existenz des Formalsatzes beweist keine native Auswahl, keinen Vorteil einer Funktion und keinen generellen physikalischen Rückholeffekt.
- Die Gleichungen beziehen sich auf Partitionen und die namentlich fixierte Altmenge `U0`; der Übergang zu umfassenderen Träger- oder Rollenmodellen erfordert zusätzliche Zuordnungen.

## Reproduzierbarkeit

Ein ergänzender Formaltest prüft Setpartitionen in kleinen endlichen Größen unabhängig von der hergeleiteten Kombinationsformel mittels Paarzählung. Geprüft werden alle Vereinigungspaare und Mehrfachvereinigungen sowie E-Geburten. Das ist ein formaler Kleinfälle-Test, keine Reproduktion der historischen FSTT-Original-Kernzustände.

## META-01-Anschluss

- `PGKM-013` (A6N-C005): **Vertiefung** – aus der Monotonie wird eine exakte Verlustbilanz.
- `PGKM-026` (A6N-C006): **Komplement** – neue Paaradressen und alte Rollenadressen bleiben typisiert getrennt.
- `PGKM-013` (A6N-C004): **Sekundärbezug** – dokumentierte Verluste sind Spezialfälle der allgemeinen Bilanz.
- **SP-14** (neu): Altpaar-Verlust bei C ↔ Neupaar-Zuwachs bei E. Das ist ein rechnerischer Kontrast, keine bewiesene Dualität zweier Module.

**Weitere offene Forschung:** Lassen sich unter echter vorab fixierter nativer Ereignisauswahl die alten Blockbesetzungen als prädiktiver Verlustreporter verwenden? Dafür wären neue originalgetreue Event- und Heldout-Tests nötig.

## Claim-Register

Alle Aussagen sind mit ihren ursprünglichen Geltungsangaben im maschinenlesbaren Claimregister hinterlegt.

- **`PGKC-315`** (EXAKTER_SATZ; `NEUER_FORMALKOROLLAR_STAND_2026_11_10`): S_U0(P)=C(|U0|,2)-sum_B C(|B∩U0|,2). Werden vorhandene Blöcke B_i durch C vereinigt, ist ΔS_U0=-sum_{i<j}n_i n_j mit n_i=|B_i∩U0|.
- **`PGKC-316`** (FORMALER_KONTRAST; `NEUER_FORMALKOROLLAR_STAND_2026_11_10`): Eine E-Geburt eines neuen Singletons bewahrt S_U0 exakt, kann aber die Anzahl aller aktuell getrennten Atompaare erhöhen. Globale Paarzahl darf nicht als Wiederherstellung alter Rollen gelesen werden.
- **`PGKC-317`** (EXAKTES_KRITERIUM; `NEUER_FORMALKOROLLAR_STAND_2026_11_10`): Ein C-Schritt reduziert S_U0 genau dann strikt, wenn unter den zusammengelegten Blöcken mindestens zwei alte U0-Atome enthalten; andernfalls kann C ohne Verlust alter Adresspaare stattfinden.

## Quellenstatus

- `SRC-078`: veröffentlichbarer Originalvolltext

## Verwandte Forschungsbefunde

Verweise auf ergänzende Forschungsbefunde mit eigenem Ergebnis- und Geltungsstatus.

- **[INTEGRATION-FIND-0044](../forschung/B05.md#integration-find-0044)** · A6N-01 / A6N-T1 / PGKM-029 · `EXAKTER_SATZ_IM_PARTITIONSVERTRAG / BESTAND_VALIDIERT`
- **[INTEGRATION-FIND-0189](../forschung/B12.md#integration-find-0189)** · RΦ-01 / RΦ-02 · `NO_VALID_PHI / EXTERNAL_TASK_ONLY / R_COND_0_N_0_TASK_RELATIVE`
