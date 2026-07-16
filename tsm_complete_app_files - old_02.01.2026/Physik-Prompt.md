PHYSIK--PROMPT (HARTER MODUS) -- TSM 136D

Ziel/Nutzen Erzeuge für \[SYSTEMNAME = Kochertalbrücke\] eine
vollständige, nachvollziehbare TSM‑136D‑Analyse mit lückenloser
Rechendokumentation (Formelableitung, Parameter, Normalisierung,
Schwellen, Transformationen), Plots und Kennzahlenbeilage. Keine
Verkürzungen. Keine Verweise. Alles, was gerechnet wird, wird im Text
dokumentiert.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
0) Ausführungspflicht (Contract) 1. Schritt A -- 1:1‑Ausgabe: Gib die
Datei "/mnt/data/Physik-Prompt.docx" exakt 1:1 im Chat aus (ohne
Auslassungen, ohne Paraphrase, keine Kommentare
davor/dazwischen/danach). • Falls die Datei nicht verfügbar ist:
schreibe stattdessen "\[Fehler A1: Datei 'Physik-Prompt' nicht
auffindbar\]" und fahre unmittelbar mit Schritt B fort. 2. Schritt B --
Analyse: Führe danach sofort die vollständige TSM‑136D‑Analyse aus ---
ohne Rückfragen. • Falls Daten fehlen, simuliere nichts, sondern
schreibe für die fehlende Komponente einen klaren Fehlerblock (mit
Überschrift "Fehlende Eingaben") und rechne alle anderen Teile trotzdem
vollständig durch. 3. Keine Verkürzungen / keine Platzhalter: Jede
verwendete Zahl, jede Formel und jeder Zwischenschritt wird explizit im
Text dokumentiert. Keine Phrasen wie "analog", "vgl." oder "siehe oben".
4. Werkzeugnutzung: • Rechnen & Plots mit Python. • Plots: matplotlib
(keine seaborn‑Styles; ein Plot je Figure; keine expliziten Farben). •
Tabellen ggf. mit ace\_tools.display\_dataframe\_to\_user. • Speichere
keine Dateien extern; alles muss im Chat sichtbar sein. 5.
Numerik/Handling (allgemein): • Einheiten konsequent angeben. Rundung in
Tabellen: 6 signifikante Stellen (falls nicht anders angegeben). •
NaN/Inf werden je Schritt protokolliert (Liste im Fehlerblock) und von
Transformationen ausgeschlossen.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
1) Daten & Mapping (Pflichttext + ggf. Fehlerblock) • Messpfade
definieren (inkl. Einheiten): -- Kohärenz: C mit 0 \< C ≤ 1
(einheitslos) -- Phasenstreuung: Δϕ \> 0 (Radiant) -- Resonanzzeit: τ \>
0 (Sekunden) • Dokumentiere Messaufbau/Instrumente (Stichpunkte) und
relevante τ‑Bänder (in‑phase Fenster) mit Bezeichnern. •
Standard‑Dateiquellen (falls vorhanden): --
/mnt/data/TSM-136D\_data\_100x100.csv -- /mnt/data/TSM-136D\_recommended
v2.json -- /mnt/data/TSM-136D\_zonen\_baseline.csv --
/mnt/data/TSM-136D\_zonen\_recommended.csv • Zusätzliche Dateiquellen
(optional, falls vorhanden): --
/mnt/data/TSM-136D\_studienwerte\_v2025-08-30.v6.csv --
/mnt/data/TSM-136D\_R\_estimates.csv --
/mnt/data/TSM-136D\_sensitivity\_top50.csv --
/mnt/data/tsm-online-bundle\_v1.20.json (nur zur Versionsausgabe) •
Falls eine Datei fehlt: Fehlerblock + setze die jeweils betroffenen
Teil‑Outputs auf "nicht berechenbar" --- ohne die übrigen zu kürzen.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
2) Formelherleitung (ausgeschrieben, mit Zwischenschritten) 1.
Resonanzfunktion -- Kurzform (Masterbrücke): F = (R · C) / Δϕ --
136D‑Variante (Arbeitsgröße): R\_eff := τ ⇒ F\_res = (C / Δϕ) · τ --
Einheitenskizze & Randbedingungen: 0 \< C ≤ 1; Δϕ \> 0 rad; τ \> 0 s. 2.
Minimalphase -- ε = 1.0° = ε\_rad = π/180 rad. -- Δϕ\_ε = max(Δϕ,
ε\_rad). 3. Winsorizing (Cap) -- cap\_quantile = 0.99. -- F\_cap =
min(F\_res, Q\_0.99(F\_res)). -- Gib den numerischen Cap‑Wert an. 4.
Transformationen -- Bindestärke: B := Quantilrang(F\_cap) ∈ \[0, 1\]. --
Spannmaß: S := Quantilrang(Δϕ\_ε / (C · τ)) ∈ \[0, 1\]. --
"Quantilrang": QR(x) := (1/n) · \|{x\_i ≤ x}\| über alle endlichen Werte
(exakte Implementierung angeben, z. B. pandas.Series.rank(pct=True,
method="average")). 5. Zonen‑Definition (Pflichtschwellen, keine
Abweichung) -- kohärent: B ≥ 0.80 & S ≤ 0.20 -- fragmentiert: B ≤ 0.20 &
S ≥ 0.80 -- regulativ: sonst 6. Parameter‑Satz (Recommended Defaults) --
Lies Werte aus TSM-136D\_recommended v2.json und drucke sie in einer
Parameter‑Tabelle: eps\_deg, cap\_quantile, B\_hi, S\_lo, B\_lo, S\_hi.
-- Falls JSON fehlt: nutze eps = 1.0°, cap = 0.99, B\_hi = 0.8, S\_lo =
0.2, B\_lo = 0.2, S\_hi = 0.8 und kennzeichne sie als Fallback.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
3) Rechnen (Schritt für Schritt, mit Code‑Snippets und Ergebnistabellen)
• Zeige für jeden Schritt: Formel → Code‑Snippet → Auszug der
Ergebnistabelle (head) → kurze Interpretation (1--2 Sätze). • Führe
keine Zwischenschritte "still" aus; alles muss im Chat dokumentiert
werden.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
4) Outputs (alle Pflicht, soweit Daten vorhanden) 1. Heatmaps F\_cap(C,
Δϕ) je τ‑Band. -- Achsenbeschriftungen, Einheiten, Titel, Farbleiste
(ohne eigene Farbwahl). -- Mindestens ein exemplarisches Band
ausdrücklich benennen. 2. Zonenkarte (Kohärent/Regulativ/Fragmentiert)
mit Schwellmarken. 3. 3D‑Surface von F\_cap (ein τ‑Band). -- Achsen (C,
Δϕ, F\_cap) beschriften. 4. Top‑B‑Fenster (Tabelle): -- Zeige die Top N
(z. B. 10) Konfigurationen mit höchstem B inkl. Spalten: C, Δϕ, τ,
F\_cap, B, S. 5. Robustheit -- Zonenanteile (Anteile in %). -- Jaccard
je Zone (Baseline vs. Recommended), falls beide Dateien vorhanden; sonst
"nicht berechenbar". -- Stability Score falls vorhanden; sonst leer
lassen (kein Fantasiewert). 6. Parameter/Version -- JSON‑Werte und
(falls vorhanden) "created"/"source" Felder als kleine Tabelle ausgeben.
-- Falls tsm-online-bundle\_v1.20.json vorhanden: bundle\_version
zusätzlich ausgeben.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
5) Physik‑Brücke (Interpretation, prägnant, aber konkret) •
Resonanzordnung (gravitationell / EM / stark / schwach) --- nenne die
sichtbare Ordnung und begründe kurz. • τ‑in‑phase‑Bänder: Wie
stabilisieren sie; was bedeuten sie für das System? • Kippkanten: Wo
liegt S hoch und B niedrig; Risiko kurz erläutern. • Skalenkopplung:
Mikro ↔ Makro beim Scrollen über τ.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
6) Reportformat (starre Reihenfolge der Überschriften) 1.
Kurzbeschreibung System + Messpfade 2. Formel‑ und Rechenschritte
(Herleitung vollständig) 3. Parameter & Version (Tabelle) 4. Ergebnisse
(Tabellen & Plots) 5. Robustheit (Zonenanteile, Jaccard, ggf. Stability)
6. Physik‑Brücke (Interpretation) 7. Kennzahlenbeilage: -- Quantile von
B und S (0.1, 0.5, 0.9). -- verwendete Schwellen & Caps (numerisch). 8.
Abgrenzung & Governance (1 Absatz): -- keine Natur‑Konsensbehauptungen;
Modellperspektive TSM‑136D; Daten‑ und Methodengrenzen klar benennen.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
7) Selbst‑Check vor Abgabe (Pflichtliste, als ✅/❌ ausgeben) • ✅ Datei
"Physik-Prompt" 1:1 ausgegeben oder Fehler A1 gesetzt • ✅ Alle Formeln
ausgeschrieben + jede Zahl/Schwelle genannt • ✅ Alle Plots vorhanden,
einzeln, mit Achsen/Einheiten/Titeln • ✅ Heatmap, Zonenkarte,
3D‑Surface, Top‑B‑Fenster • ✅ Zonenanteile + (falls möglich) Jaccard je
Zone • ✅ Parameter‑/Versionstabelle • ✅ Physik‑Brücke (Ordnung,
τ‑Bänder, Kippkanten, Skalenkopplung) • ✅ Kennzahlenbeilage • ✅
Abgrenzung & Governance Absatz • ✅ Keine
Verkürzungen/Verweise/Platzhalter Wenn ein Punkt fehlt: gib "❌
(Begründung + was fehlt genau)" aus und liefere trotzdem alle
erfüllbaren Teile vollständig.
\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
Ende des Prompts.
