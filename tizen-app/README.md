# TV Home als Samsung-TV-App (Tizen)

Die App ist nur ein Wrapper: Sie öffnet `tv-home.html` von GitHub Pages im Vollbild.
Damit startet der Fernseher beim Einschalten direkt in deinem Startbildschirm, ohne Browser.

## Einmalig am Fernseher
1. Apps öffnen, auf dem Zahlenfeld der Fernbedienung **12345** eingeben, **Developer Mode: On** setzen,
   als **Host PC IP** die IP deines Computers eintragen, Fernseher neu starten.
2. Einstellungen > Allgemein > Smart-Funktionen > **„Zuletzt verwendete App beim Einschalten starten“** (Autorun) aktivieren.
   (Je nach Menüversion heißt der Punkt „Start-Bildschirm“ / „Autorun Smart Hub“.)

## Am Computer
1. [Tizen Studio](https://developer.tizen.org/development/tizen-studio/download) mit **TV Extensions** installieren.
2. Unter *Certificate Manager* ein **Samsung-Zertifikat** anlegen (kostenloses Samsung-Konto, TV-DUID eintragen).
3. Tizen Studio > *Device Manager* > TV per IP verbinden (Remote Device Manager).
4. Dieses Verzeichnis (`tizen-app/`) als Projekt importieren, Rechtsklick > *Run As > Tizen Web Application*.
5. App einmal starten, dann den Fernseher ausschalten und per Fernbedienung wieder einschalten.

Hinweis: Die Entwickler-Installation läuft ab, wenn das Zertifikat abläuft; dann einfach neu installieren.
