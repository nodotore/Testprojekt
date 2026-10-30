# TV Frame als Samsung-TV-App (Kunstmodus wie „The Frame“)

Zeigt `tv-frame.html` (Vollbild-Diashow deiner Galerie mit dunklem Passepartout, Rahmen und OLED-Schutz)
und hält den Bildschirm wach (Privileg `power`). Einrichtung wie in `../tizen-app/README.md`,
nur dieses Verzeichnis (`tizen-app-frame/`) als Projekt importieren.

## Bilder
1. Bilder (JPG/PNG/WebP, am besten 3840×2160) in `tv-frame/` legen.
2. `sh tv-frame/make-list.sh` ausführen (schreibt `tv-frame/images.json`), committen, auf `master` pushen → GitHub Pages aktualisiert sich.

## Am Fernseher, damit er nie in Standby geht
- Einstellungen > Allgemein > Eco-Lösung / Energie- und Energiesparmodus: **Automatische Abschaltung = Aus**,
  **Bildschirm bei Inaktivität ausschalten / Auto-Standby = Aus**, **Umgebungslichtsensor/Helligkeit** moderat (ca. 20–30 %).
- Einstellungen > Allgemein > Systemmanager > Zeit > **Ausschalttimer = Aus**.
- Autorun: „Zuletzt verwendete App beim Einschalten starten“ aktivieren.
- Zur Schonung des OLEDs: URL-Parameter `?interval=60&clock=1` und optional nachts per Timer ausschalten.
