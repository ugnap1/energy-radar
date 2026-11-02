# Energie-Radar

Sammelt Nachrichten aus Fachquellen zu Energiewirtschaft, Kraftwerkstechnik, Wasserstoff und Erneuerbaren
und baut daraus eine durchsuchbare Webseite (`docs/index.html`).

## Zwei Arten, Inhalte zu finden

1. **Feeds**: feste Fachquellen per RSS (`"feeds"` in `feeds.json`).
2. **Automatische Suche**: Stichwörter (`"searches"`) werden über Google-News-RSS gesucht, aber nur in
   den Domains aus `"trusted_domains"`. So bleiben die Treffer auf glaubwürdige Quellen beschränkt.

## Lokal ausführen

    python3 build.py
    # dann docs/index.html im Browser öffnen

Keine Installation nötig (nur Python 3.9+). Fehlerhafte Feeds werden übersprungen und unten auf der
Seite unter "Quellenstatus" angezeigt.

## Automatisch aktualisieren und veröffentlichen (kostenlos)

1. Ordner als GitHub-Repository hochladen.
2. Settings -> Pages -> Source: "Deploy from a branch", Branch `main`, Ordner `/docs`.
3. Der Workflow `.github/workflows/update.yml` läuft dreimal täglich und aktualisiert die Seite.
   Unter Actions kannst du ihn auch manuell starten.

## Anpassen

- Neue Quelle: Eintrag in `feeds` ergänzen (RSS-URL der Seite, oft `/feed/` oder `/rss`).
- Neue Themen: Stichwörter in `searches` ergänzen.
- Vertrauenswürdige Domains: Liste `trusted_domains` pflegen.
- Zeitraum: `days_back`.
