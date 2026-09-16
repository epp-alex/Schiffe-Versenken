# 🚢 Multiplayer Schiffe Versenken (2–4 Spieler)

[🇬🇧 English version](README.en.md)

Ein netzwerkfähiges "Schiffe versenken" für 2 bis 4 Spieler im lokalen Netzwerk (LAN), gebaut mit **Python** und **PyQt5**. Ein Spieler hostet die Partie, die anderen treten per IP/Port bei – reines TCP-Socket-Netzwerk, keine externen Server oder Accounts nötig.

Läuft auf **Windows**, **Linux** und **macOS**.

## Features

- **2–4 Spieler** in einer Partie, reihum in fester Reihenfolge

- **Host/Client-Architektur** über TCP-Sockets im lokalen Netzwerk

- **Manuelle oder automatische Schiffsplatzierung** (`🎲 Auto-Platzieren`), inklusive Mindestabstand zwischen Schiffen

- Schiffe per Taste **`R`** oder Button drehen (horizontal/vertikal)

- **Eliminierungs-Modus**: Wer alle Schiffe verliert, scheidet aus – gewonnen hat, wer als Letzter übrig bleibt

- Aufgedeckte Felder ausgeschiedener Spieler bleiben zum Anschauen im Radar-Dropdown sichtbar

- **Automatische IP-Erkennung** (`📍 IP finden`) für den Host

- **Nochmal spielen**, ohne die App neu starten zu müssen

- Robuste Verbindungsbehandlung: Ein getrennter Mitspieler scheidet automatisch aus, das Spiel läuft für die übrigen weiter

- UI-Fix für konsistente Feldgrößen unter macOS

## Download (fertige Binaries)

Für jede Version stehen auf der [Releases-Seite](file:///C:/Users/releases) fertige, lauffähige Programme bereit – kein Python nötig:

| Plattform | Datei |
| - | - |
| Windows | `Schiffe.exe` |
| macOS | `Schiffe.dmg` |
| Linux | `Schiffe` |


> **Hinweis (Windows/macOS):** Da die Programme nicht kommerziell signiert sind, kann beim ersten Start eine Sicherheitswarnung erscheinen ("Windows hat den PC geschützt" / "nicht verifizierter Entwickler"). Einfach über "Weitere Informationen → Trotzdem ausführen" (Windows) bzw. Rechtsklick → "Öffnen" (macOS) bestätigen.

## Voraussetzungen (nur für den Start aus dem Quellcode)

- Python 3.8 oder neuer

- PyQt5

```
pip install PyQt5
```

## Starten (aus dem Quellcode)

```
python Schiffe.py
```

Jeder Mitspieler startet die Datei separat (auf seinem eigenen Rechner im selben Netzwerk).

## Spielen

### Host (Spieler 1)

1. Rolle **„Host (Spieler 1)"** auswählen

2. Anzahl der Spieler wählen (2–4)

3. Optional auf **„📍 IP finden"** klicken, um die eigene lokale Netzwerk-IP automatisch einzutragen

4. Port festlegen (Standard: `5555`)

5. **„Lobby Starten / Beitreten"** klicken – die App wartet nun auf die restlichen Spieler

6. **Die angezeigte IP-Adresse an alle Mitspieler weitergeben** (z. B. per Chat/Zuruf) – diese wird im nächsten Schritt gebraucht

### Mitspieler (Client)

1. Rolle **„Client (Beitreten)"** auswählen

2. **Genau die IP-Adresse eintragen, die beim Host angezeigt wurde** (siehe Schritt 6 oben) – bei Tippfehlern oder einer falschen/veralteten IP kann nicht beigetreten werden

3. Den gleichen Port wie beim Host eintragen

4. **„Lobby Starten / Beitreten"** klicken

> ⚠️ **Der häufigste Grund, warum das Beitreten nicht funktioniert:** Die vom Client eingetragene IP stimmt nicht exakt mit der IP überein, die der Host über „📍 IP finden" ermittelt hat. Am besten die IP beim Host direkt kopieren (nicht abtippen), um Tippfehler zu vermeiden. Falls sich die IP des Hosts zwischenzeitlich ändert (z. B. nach einem WLAN-Neuverbinden), muss sie erneut ermittelt und neu an die Mitspieler weitergegeben werden.

Sobald alle Spieler verbunden sind, platziert jeder seine Schiffe auf dem eigenen Feld (linke Seite). Nach der Platzierung wartet man auf die übrigen Mitspieler – dann beginnt das Spiel automatisch.

Auf dem rechten Feld (**Angriffs-Radar**) wird per Klick auf den aktuellen Gegner geschossen. Über das Dropdown **„Ziel-Spieler"** lassen sich auch bereits aufgedeckte Felder anderer (auch ausgeschiedener) Spieler betrachten – geschossen wird aber immer nur auf das per Spielreihenfolge vorgegebene Pflichtziel.

## Netzwerk-Hinweise

- Alle Spieler müssen sich im **gleichen lokalen Netzwerk** befinden (WLAN/LAN), oder der Host muss den gewählten Port in seiner Firewall/seinem Router für eingehende Verbindungen freigeben (Port-Weiterleitung), falls über das Internet gespielt werden soll.

- Die Kommunikation läuft **unverschlüsselt** über reines JSON-über-TCP – gedacht für private, vertrauenswürdige Netzwerke, nicht für den Einsatz über das offene Internet ohne zusätzliche Absicherung.

- Es gibt keine Authentifizierung: Wer die IP und den Port des Hosts kennt, kann der Lobby beitreten.

- Die lokale IP-Adresse des Hosts kann sich bei jedem Neustart des Routers oder erneuten WLAN-Verbindungsaufbau ändern (typisch bei per DHCP vergebenen Adressen). Falls das Beitreten plötzlich nicht mehr funktioniert, zuerst prüfen, ob sich die IP des Hosts geändert hat.

## Bekannte Einschränkungen

- Kein Wiederverbinden nach Verbindungsabbruch (ein getrennter Spieler scheidet dauerhaft aus der laufenden Partie aus)

- Keine Verschlüsselung/Authentifizierung (siehe oben – nur für vertrauenswürdige LANs gedacht)

- Feste Schiffsgrößen: `[4, 3, 2, 2, 1, 1, 1]` auf einem 10×10-Feld

## Lizenz

MIT License – siehe [LICENSE](LICENSE)

## Beiträge

Pull Requests und Issues sind willkommen!
