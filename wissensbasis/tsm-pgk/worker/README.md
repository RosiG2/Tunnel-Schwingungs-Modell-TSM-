# TSM–PGK – öffentlicher MCP-Worker

Lesender Cloudflare-Worker für die öffentliche PGK-Forschungswissensbasis unter `wissensbasis/tsm-pgk/`.

## Datenquelle

Der Worker verwendet den freigegebenen GitHub-Commit `94ed62efade5a5514482904464edc8e0dd49cf15` (siehe `PGK_FIXED_REVISION` in `wrangler.toml`). Er lädt nur das öffentliche `mcp/publication/{manifest,bundle}.json` und prüft dessen SHA-256-Konsistenz. Nicht freigegebene Forschungsoriginale gehören nicht in diesen Worker.

## Betrieb

Innerhalb dieses Ordners mit Node.js und Wrangler:

```sh
npm install
npm run check:code
npx wrangler deploy
```

Vor dem ersten produktiven Einsatz sind die Cloudflare-Kontoanmeldung, eine gesonderte Datenschutz-/Betriebsprüfung und Cloudflare-CPU-/Fehlermessung erforderlich. Der Worker bietet `POST /mcp` (Streamable HTTP) und `GET /health` (nur Prozessstatus, kein wissenschaftlicher oder GitHub-Integrationstest). Der tatsächliche Worker-Endpunkt wird erst beim Cloudflare-Deployment bekannt. Keine Zugangsdaten ins Repository aufnehmen.

Cloudflare-Workers-Free hat eine CPU-Grenze von 10 ms pro Request. Ein Kaltstart mit 3,16 MB Publikationsdaten kann diese überschreiten. Vor breiter Nutzung Testaufrufe über `/mcp` und CPU-Dauer/Fehler im Cloudflare-Dashboard prüfen. Bei wiederholten Überschreitungen zuerst die Datenauslieferung optimieren oder passend dimensionierte Laufzeit wählen.

Ein öffentlicher `workers.dev`-Endpunkt ist grundsätzlich von außen erreichbar. `ALLOWED_ORIGINS` ist kein Authentifizierungsmechanismus. Nur öffentliche Daten über diesen Worker anbieten; nicht vertrauliche Forschungsentwürfe über die offene `pgk_validate_draft`-Funktion senden.

Bei einem neuen freigegebenen Forschungsstand den GitHub-Commit prüfen und `PGK_FIXED_REVISION` aktualisieren. Nach der Aktualisierung einen neuen Worker-Release bereitstellen und `/mcp` erneut testen.
