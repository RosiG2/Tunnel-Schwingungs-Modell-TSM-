# Datenschutzrichtlinie

*Hinweis: Diese Vorlage dient der Information und muss auf Ihren konkreten Einsatz, Verträge und Systeme angepasst werden. Sie stellt **keine Rechtsberatung** dar.*

**Version:** v1.1  
**Stand:** 2025-09-17

---

## 1) Verantwortlicher (Art. 4 Nr. 7 DSGVO)
**Rosi Hach**  
**Adresse:** Sindelfingen, Deutschland  
**E‑Mail:** rosig2@web.de

### (Optional) Datenschutzbeauftragte:r
Derzeit **nicht bestellt**; Erforderlichkeit wird fortlaufend geprüft (Art. 37 DSGVO). Bei Bestellung werden Angaben hier ergänzt.

---

## 2) Zweck und Funktionsweise des Systems
Dieser Assistent („**TSM‑GPT**“) unterstützt die Arbeit mit dem **Tunnel‑Schwingungs‑Modell (TSM)** und dessen Abbildung zur **Positive Geometry (PG)**.

Der Betrieb kann in zwei Varianten erfolgen:
- **Online‑Modus:** Das System ruft inhaltsbezogene Dateien **lesend** von GitHub‑Raw ab (z. B. `…/tsm-online-bundle_v1.25.json`, Crosswalk, Overlay).  
- **Offline‑Modus:** Die gleichen Inhalte werden als lokale Wissensdateien („Knowledge“) im System hinterlegt; kein Abruf aus dem Internet.

In beiden Varianten verarbeitet das System Benutzeranfragen (Chat/Prompts) und erzeugt Antworten anhand der TSM/PG‑Inhalte. Eine eigenständige Profilbildung findet nicht statt (siehe § 10).

---

## 3) Kategorien verarbeiteter Daten
**3.1 Kommunikations-/Inhaltsdaten**  
Vom Nutzer eingegebene Texte, Anhänge, Metadaten (Zeitstempel, ggf. Referenzen auf Zonen/Facetten).

**3.2 Technische Nutzungsdaten**  
Log‑Daten der Anwendung (Zeitpunkt, Dauer, Fehlermeldungen), ggf. Browser/Client‑Informationen, pseudonyme Sitzungskennungen.

**3.3 Inhaltsquellen (nicht‑personenbezogen)**  
TSM/PG‑Fachinhalte aus GitHub‑Raw (öffentliche Repository‑Dateien) **ohne** Personenbezug; alternativ lokal eingebundene Wissensdateien.

> **Grundsatz:** Geben Sie **keine** sensiblen personenbezogenen Daten (Art. 9 DSGVO) in Freitext ein. Das System ist nicht für die Verarbeitung besonderer Kategorien ausgelegt.

---

## 4) Zwecke der Verarbeitung
- Bereitstellung der TSM/PG‑Funktionen (Beantwortung von Fragen, Aggregation, Tabellen).  
- Qualitätssicherung und Fehlersuche (Protokollierung technischer Ereignisse).  
- (Optional) Verbesserung des Assistenten innerhalb der eigenen Organisation (z. B. Prompt‑Bibliothek, Auswertung häufig gestellter Fragen).  
- (Optional) Rechtskonforme Bereitstellung eines Chat‑Widgets auf einer Website (nur wenn verwendet; siehe § 11).

---

## 5) Rechtsgrundlagen (Art. 6 DSGVO)
- **Art. 6 Abs. 1 lit. f DSGVO** (berechtigte Interessen) – effiziente Fachassistenz zum TSM/PG bei minimalem Datenaufwand; **Interessenabwägung** dokumentiert.  
- **Art. 6 Abs. 1 lit. b DSGVO** (sofern vertraglich erforderlich).  
- **Art. 6 Abs. 1 lit. a DSGVO** (Einwilligung), falls optionale Auswertungen/Betas eingesetzt werden.

> Für besondere Kategorien (Art. 9 DSGVO) ist **keine Verarbeitung vorgesehen**.

---

## 6) Empfänger / Kategorien von Empfängern
- **Plattformanbieter KI‑Assistent** (z. B. OpenAI ChatGPT / Enterprise / API): Verarbeitung von Chat‑Inhalten und Metadaten zur Antwortgenerierung; Verantwortlichkeit siehe § 7.  
- **GitHub (raw.githubusercontent.com)**: **Nur lesender Abruf** fachlicher Inhalte im Online‑Modus; es werden **keine personenbezogenen Daten übermittelt**.  
- **Infrastruktur‑/Hosting‑Dienstleister**: Betrieb, Logging, Sicherheit.  
- **Interne Empfänger**: Administrierende, TSM‑Fachteam, IT‑Sicherheit (RBAC, Need‑to‑know).

---

## 7) Rollenmodell & Auftragsverarbeitung

**Variante C – Eigenständige Verantwortlichkeit des Anbieters (gewählt):**  
Rosi Hach nutzt einen externen KI‑Dienst (z. B. ChatGPT) zur Beantwortung von Anfragen; der Anbieter verarbeitet Daten als **eigener Verantwortlicher**. Es gelten die Datenschutzinformationen des jeweiligen Anbieters. Rosi Hach übermittelt nur das **erforderliche Minimum** an Daten.  
*Varianten A/B sind nicht einschlägig.*

---

## 8) Drittlandübermittlungen (Art. 44 ff. DSGVO)
Sofern Dienste in Drittländern (insb. **USA**) eingesetzt werden, stützen wir Übermittlungen auf **SCC (Art. 46 Abs. 2 lit. c DSGVO)** und – falls verfügbar – zusätzliche technische und organisatorische Maßnahmen (z. B. Verschlüsselung im Transit und at rest). Etwaige Risiken werden bewertet und dokumentiert.

---

## 9) Speicherdauer
- **Chats/Inhalte:** **gesetzliches Minimum** – Speicherung nur solange zur Zweckerfüllung erforderlich; anschließende Löschung. Keine darüber hinausgehende Aufbewahrung durch Rosi Hach.  
- **Technische Logs:** **gesetzliches Minimum** / kurzzeitige Speicherung zur Sicherstellung von Betrieb und Sicherheit; anschließend Löschung oder Anonymisierung.  
- **Wissensdateien (Offline‑Modus):** nur relevant, falls der Offline‑Modus genutzt wird; dann gemäß internem Löschkonzept.  
- **GitHub‑Abrufe (Online‑Modus):** keine Speicherung personenbezogener Daten; lediglich flüchtige Caches/Protokolle der Infrastruktur.

---

## 10) Automatisierte Entscheidungen/Profiling
Es finden **keine** Entscheidungen mit **rechtlicher Wirkung** oder ähnlich erheblichen Auswirkungen ausschließlich automatisiert statt (Art. 22 DSGVO). **Profiling** zu Marketing‑/Trackingzwecken ist deaktiviert.

---

## 11) Web‑Einbindung, Cookies & Tracking
**Nicht eingesetzt.** Es besteht aktuell **keine** Einbindung als Website‑Widget; damit sind keine Widget‑Cookies oder Consent‑Flows erforderlich. Allgemeine Website‑Regelungen bleiben unberührt.

---

## 12) Sicherheit (Art. 32 DSGVO)
Wir setzen geeignete technische und organisatorische Maßnahmen (TOM) ein, u. a.: Transportverschlüsselung (TLS), rollenbasierte Zugriffe (RBAC), Least‑Privilege, Protokollierung/SIEM, Härtung der Actions/Webhooks, Geheimnisschutz (API‑Keys), regelmäßige Updates, Berechtigungskonzepte und Schulungen.

---

## 13) Betroffenenrechte (Art. 12–21 DSGVO)
Sie haben – unter den gesetzlichen Voraussetzungen – folgende Rechte: **Auskunft**, **Berichtigung**, **Löschung**, **Einschränkung**, **Datenübertragbarkeit**, **Widerspruch** gegen Verarbeitungen auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO, sowie **Widerruf** erteilter Einwilligungen mit Wirkung für die Zukunft.

**Kontakt:** Bitte richten Sie Anfragen an die oben genannten Kontaktdaten. Zusätzlich besteht ein **Beschwerderecht** bei einer Datenschutzaufsichtsbehörde (Art. 77 DSGVO).

---

## 14) Spezifika Online‑Modus
- Abruf ausschließlich **öffentlicher** TSM/PG‑Dateien von GitHub‑Raw; **keine** Übermittlung personenbezogener Daten an GitHub erforderlich.  
- Der Assistent verarbeitet Chat‑Eingaben **nur** zur Antwortgenerierung. Bitte vermeiden Sie die Eingabe personenbezogener Daten.  
- Versionen/Zeitstempel der genutzten Bundles werden in Antworten transparent benannt.

## 15) Spezifika Offline‑Modus
- TSM/PG‑Inhalte sind lokal/organisationsintern abgelegt („Knowledge“).  
- Zugriff und Änderungen werden rollenbasiert gesteuert; Versionierung und Freigabeprozesse sind dokumentiert.  
- Keine externe Datenübertragung für Wissensinhalte.

---

## 16) Transparenzhinweis zum KI‑Einsatz
Dieser Dienst nutzt KI‑Modelle zur **inhaltlichen Assistenz** (TSM↔PG). Antworten können Fehler enthalten; maßgeblich sind die **Originalquellen** (TSM‑Dokumente/Bundle). Das System kennzeichnet Datenstand (Version/Zeitstempel) in inhaltlichen Ausgaben.

---

## 17) Pflicht zur Bereitstellung / Folgen der Nichtbereitstellung
Die Bereitstellung von Eingabedaten ist **freiwillig**. Ohne Eingabe kann keine Antwort erzeugt werden.

---

## 18) Änderungen dieser Datenschutzrichtlinie
Wir passen diese Informationen bei Bedarf an. Die jeweils gültige Fassung ist über [URL/Ort der Veröffentlichung] abrufbar. Wesentliche Änderungen werden aktiv mitgeteilt.

---

## 19) Kontakt & Verantwortlichkeiten
- Operativer Kontakt: **Rosi Hach** – rosig2@web.de  
- Technische Ansprechstelle (z. B. Prompt/Actions): **Rosi Hach**  
- Datenschutz: **Rosi Hach** (Kontakt gem. § 1)

---

### Anlage A – Konfigurationsmatrix (ausgefüllt)
| Bereich | Einstellung | Notizen |
|---|---|---|
| Modus | Online | GitHub‑Raw nur lesend, keine PII |
| Anbieter‑Rolle | Eigenverantwortung (Variante C) | Verträge/DPA/SCC referenzieren |
| Speicherdauer Chats | gesetzliches Minimum | Löschkonzept referenzieren |
| Log‑Retention | gesetzliches Minimum | Zweck: Sicherheit/Fehleranalyse |
| Consent nötig? | Nein | Nur für nicht essenzielle Funktionen |
| Datenminimierung | Aktiv | Keine sensiblen Daten eingeben |

### Anlage B – Mustertext für Website/Widget (Kurzfassung)
> **KI‑Hinweis & Datenschutz:** Dieser Assistent nutzt KI zur Unterstützung bei TSM/PG‑Fragen. Ihre Eingaben werden verarbeitet, um Antworten zu erzeugen. Bitte geben Sie **keine** personenbezogenen oder sensiblen Daten ein. Weitere Informationen finden Sie in unserer [Datenschutzrichtlinie]([Link]).

