# A6N-01 – Nichtwiedertrennbarkeit benannter alter Rollen

## Definition (RΦ-02, externe Aufgabenfunktion)

Sei `U_0` die Menge der beim Beginn einer ausgewählten nativen Historie bereits vorhandenen atomaren IDs. Für zwei fest gewählte alte IDs `a,b∈U_0` definiere

\[
H_{a,b}(q) := \mathbf{1}\{\operatorname{rep}_{q}(a)\neq\operatorname{rep}_{q}(b)\}.
\]

Dies bedeutet, dass die **native aktuelle Komponentenadressierung** beide alten IDs getrennt erreichen kann. Ein benannter externer Auftraggeber verlangt diese zwei Ports. Der Kern selbst enthält keinen Nutzenoperator, der diesen Auftrag priorisiert.

## Satz A6N-T1 (im unveränderten E/C-Alphabet)

Für jede vollständig native E-/C-Historie und jedes Paar alter, fest bezeichneter IDs `a,b` gilt:

\[
H_{a,b}(q_{n+1})\leq H_{a,b}(q_n).
\]

Gilt irgendwann `H_{a,b}(q_n)=0`, dann ist `H_{a,b}(q_m)=0` für alle folgenden legalen E-/C-Nachfolgezustände `m≥n`.

**Beweis:** `apply_direct` erzeugt bei E ein neues atomisches Singleton und übernimmt sämtliche bisherigen Äquivalenzklassen unverändert. Die Relation der alten Atome wird nicht verfeinert. Bei C führt `merge_partition` ausschließlich Vereinigungen vorhandener Äquivalenzklassen aus. Eine solche Vergröberung kann zuvor getrennte `a,b` vereinigen, aber bereits vereinigte `a,b` nicht trennen. Endliche Kompositionen solcher Operationen können diese Eigenschaft nicht umkehren. ∎

**Zugehöriges Gesamtregister:** Die Anzahl

\[
S_{U_0}(q)=\sum_{\{a,b\}\subseteq U_0}H_{a,b}(q)
\]

ist monoton nichtzunehmend. Diese Aussage betrifft nur die *am Anfang benannten* Atome. Eine E-Geburt kann die Zahl **aller** aktuell unterscheidbaren Atompaare dennoch vergrößern. Deshalb dürfen die beiden Summen nicht gleichgesetzt werden.

## Konkrete Wiederholung am Originalkern

Für `POS_PARENT`: `S_{U_0}` 95 → 93 nach ausgewähltem C1, danach 93 in den Schritten E2, E3, C4, E5. Die benannte Rolle `H_(1,13)` geht in C1 von 1 auf 0 und bleibt 0.

Für `STOP_PARENT`: `S_{U_0}` 49 → 46 nach ausgewähltem C1. `H_(4,5)` geht von 1 auf 0. Der neue native Kandidatenraum enthält keine E- oder C-Kandidaten mehr.

**Negativgrenze:** Der Satz verbietet *keine* Ersatzorganisation mit **neuen** Rollen oder einem anderen Typvertrag. Eine solche Delegation erfordert aber eine eigenständige, native Rollen-/Kontextzuordnung, die im hier unveränderten Kernel nicht vorliegt. Weder Gleichartigkeit noch Gleichfunktion folgen aus bloßer Neubildung eines Atoms.

**Status:** mathematisch exakte Aussage über die implementierte endliche Partitionsoperation; kein empirischer Naturbefund, keine allgemeine Widerlegung von PGK-Regeneration.
