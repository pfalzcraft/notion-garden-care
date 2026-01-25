# Schnellstart: Automatisches Datenbank-Setup

## Schritt 1: Python-Abhängigkeiten installieren

Öffne ein Terminal in diesem Verzeichnis und führe aus:

```bash
pip install -r requirements.txt
```

## Schritt 2: Notion Page vorbereiten

**Option A: Neue Page erstellen (empfohlen)**
1. Öffne Notion
2. Erstelle eine neue leere Page (z.B. mit dem Titel "Garten" oder "Home Assistant")
3. Das Setup-Script wird diese Page finden und verwenden

**Option B: Bestehende Page verwenden**
- Du kannst auch eine bestehende Page verwenden, in der die Datenbank erstellt werden soll

## Schritt 3: Setup-Script ausführen

```bash
python setup_notion_database.py
```

### Was das Script tut:

1. ✅ Verbindet sich mit deinem Notion-Account
2. ✅ Zeigt dir verfügbare Pages an
3. ✅ Erstellt automatisch die "Gartenpflege" Datenbank mit allen Properties:
   - Name, Typ, Standort, Aktiv
   - Düngung Intervall, Letzte Düngung, Nächste Düngung (Formula)
   - Gießen Intervall, Letztes Gießen, Nächstes Gießen (Formula)
   - Rückschnitt Monate, Rückschnitt Anleitung
   - Pflegehinweise, Besonderheiten, Notizen
4. ✅ Speichert die Database-ID automatisch in `.env`
5. ✅ Bietet an, Beispielpflanzen hinzuzufügen (Tomaten, Rosenbusch, Apfelbaum, Basilikum)

### Erwartete Ausgabe:

```
============================================================
🌱 Notion Gartenpflege Datenbank Setup
============================================================

🔍 Suche nach verfügbaren Pages in deinem Workspace...

✅ 3 Page(s) gefunden:

  1. Mein Garten
     ID: a1b2c3d4e5f6...

  2. Home Assistant
     ID: x9y8z7w6v5u4...

Wähle eine Page (Nummer) oder gib 'n' für eine neue Page ein: 1

🌱 Erstelle Gartenpflege-Datenbank...

✅ Datenbank erfolgreich erstellt!

📊 Datenbank-Details:
   ID:  abc123def456...
   URL: https://www.notion.so/...

✅ .env Datei aktualisiert mit Database-ID

🌿 Möchtest du Beispielpflanzen hinzufügen? (j/n): j

🌱 Füge Beispielpflanzen hinzu...
   ✅ Tomaten hinzugefügt
   ✅ Rosenbusch hinzugefügt
   ✅ Apfelbaum hinzugefügt
   ✅ Basilikum hinzugefügt

✅ Beispielpflanzen wurden hinzugefügt!

============================================================
🎉 Setup erfolgreich abgeschlossen!
============================================================

📋 Nächste Schritte:
   1. Öffne die Datenbank in Notion
   2. Füge weitere Pflanzen hinzu
   3. Konfiguriere Home Assistant mit der Database-ID

   Database-ID: abc123def456...
```

## Fehlerbehebung

### Fehler: "NOTION_TOKEN nicht gefunden"
- Stelle sicher, dass die `.env` Datei existiert und dein Token enthält
- Format: `NOTION_TOKEN=ntn_...`

### Fehler: "Keine Pages gefunden"
- Erstelle manuell eine neue Page in Notion
- Kopiere die URL oder Page-ID und gib sie im Script ein

### Fehler beim Erstellen der Datenbank
- Stelle sicher, dass die Integration mit der Parent-Page verbunden ist
- Gehe zur Page → "..." → "Connections" → Wähle "Home Assistant Garten"

## Was als Nächstes?

Nach erfolgreichem Setup:
1. ✅ Datenbank ist erstellt und einsatzbereit
2. ➡️ Fahre mit der Home Assistant Integration fort
3. ➡️ Konfiguriere Sensoren und Automatisierungen
