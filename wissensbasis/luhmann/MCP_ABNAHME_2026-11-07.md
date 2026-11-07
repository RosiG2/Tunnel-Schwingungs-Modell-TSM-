# MCP-Wissensbrücke – Abnahmebefund vom 7. November 2026

## Gegenstand und Nachweisart

Geprüft wurde der öffentliche MCP-Endpunkt `https://luhmann-knowledge-mcp.rosig2.workers.dev/mcp`. Die nachstehenden Befunde beruhen auf im MCP Inspector durchgeführten, vom Betreiber übermittelten Werkzeugaufrufen. Sie dokumentieren beobachtete Antworten; sie sind keine fortlaufende Verfügbarkeitszusage oder unabhängige Sicherheitszertifizierung.

## Nachgewiesene Funktionen

| Prüfung | Beobachtetes Ergebnis |
| --- | --- |
| MCP-Initialisierung und `tools/list` | Erfolgreich; die beiden ursprünglichen lesenden Werkzeuge angezeigt |
| `luhmann_wissensindex({})` | Edition `atlas-0.3-redaktion`, 17 registrierte Beiträge, fünf Bibliotheken A–E plus Einstieg |
| `luhmann_wissenseintrag({"id":"system-und-umwelt"})` | Artikelinhalt, Registermetadaten, Quellen-URL und redaktioneller Nachweisstatus ausgegeben |
| `luhmann_themenrecherche({"query":"Schulreform Lernklima"})` | Sechs thematisch passende Treffer; 17 Artikel durchsucht, `incomplete: false`, `unavailable_ids: []` |
| `luhmann_bezugspfad({"start_id":"strukturelle-kopplung","depth":1})` | Drei registrierte Knoten und vier gerichtete redaktionelle Verweis-Kanten |
| Lokale automatisierte Tests vor dem produktiven Update | 11 von 11 bestanden (`npm test`) |
| Lokale Buildprobe vor dem produktiven Update | Wrangler `deploy --dry-run` erfolgreich |

Die beiden neuen Werkzeuge antworteten nach der Cloudflare-Aktualisierung mit Live-Daten aus der GitHub-Wissensbasis. Die beiden ursprünglichen Werkzeuge wurden im Inspector vor dem Update erfolgreich ausgeführt; ein vollständiger erneuter Regressionstest der ursprünglichen Werkzeuge **nach** dem Update wurde im hier dokumentierten Ablauf nicht übermittelt.

## Erkenntniswert und Grenzen

Die Themenrecherche liefert über `matched_fields`, `score`, `excerpt` und `source` eine nachvollziehbare lexikalische Trefferliste; die Werte sind keine semantische Evidenzbewertung. `incomplete: false` bescheinigt für die abgefragte Suche eine vollständige Durchsicht der registrierten Artikel, nicht eine Vollständigkeit der wissenschaftlichen Literatur.

Die Bezugspfadfunktion folgt expliziten `related_ids`. Die Kantenbezeichnung `editorial_related_id` bedeutet redaktionelle Lektürebeziehung; sie behauptet weder eine nachgewiesene theoretische Folgerung noch einen kausalen Zusammenhang.

**Separater Host-Befund:** In getesteten ChatGPT-Work-Sitzungen wurden die MCP-Werkzeuge nicht zuverlässig bereitgestellt, obwohl der Plugin-Skill verfügbar war. Dieser Host-Befund ist weiterhin offen und muss vor einer öffentlichen Freigabe im vorgesehenen Ausführungskontext erneut geprüft werden.

**Datenschutz:** Frei formulierte Themenanfragen werden als MCP-Werkzeugargument an den Cloudflare-Worker übermittelt. Protokollierungs- und Aufbewahrungsregeln des tatsächlichen Cloudflare-Betriebs müssen vor der öffentlichen Einreichung anhand der Konfiguration dokumentiert werden.
