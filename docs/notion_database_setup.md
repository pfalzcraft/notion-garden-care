# Notion Datenbank Setup - Schritt für Schritt

## 1. Neue Datenbank erstellen

1. Öffne Notion
2. Erstelle eine neue Seite oder gehe zu einer bestehenden
3. Tippe `/database` oder `/tabelle`
4. Wähle **"Tabelle - Inline"** oder **"Table - Inline"**
5. Benenne die Datenbank: **"Gartenpflege"**

## 2. Properties (Spalten) hinzufügen

Klicke auf das **+** rechts neben der letzten Spalte und füge folgende Properties hinzu:

### Basis-Informationen

| Property Name | Property Typ | Beschreibung |
|--------------|-------------|--------------|
| **Name** | Title | Name der Pflanze (bereits vorhanden) |
| **Typ** | Select | Optionen: Pflanze, Baum, Strauch, Gemüse, Kräuter, Rasen |
| **Standort** | Select | Optionen: Garten, Balkon, Terrasse, Wintergarten, Innenraum |
| **Aktiv** | Checkbox | Ist die Pflanze noch vorhanden? |

### Düngung

| Property Name | Property Typ | Konfiguration |
|--------------|-------------|---------------|
| **Düngung Intervall (Tage)** | Number | Anzahl der Tage zwischen Düngungen |
| **Letzte Düngung** | Date | Datum der letzten Düngung |
| **Nächste Düngung** | Formula | Formel: `dateAdd(prop("Letzte Düngung"), prop("Düngung Intervall (Tage)"), "days")` |
| **Dünger-Art** | Text | z.B. "Kompost", "Blaudünger", etc. |

### Bewässerung

| Property Name | Property Typ | Konfiguration |
|--------------|-------------|---------------|
| **Gießen Intervall (Tage)** | Number | Anzahl der Tage zwischen Gießen |
| **Letztes Gießen** | Date | Datum des letzten Gießens |
| **Nächstes Gießen** | Formula | Formel: `dateAdd(prop("Letztes Gießen"), prop("Gießen Intervall (Tage)"), "days")` |
| **Wassermenge** | Select | Optionen: Wenig, Mittel, Viel |

### Rückschnitt

| Property Name | Property Typ | Beschreibung |
|--------------|-------------|--------------|
| **Rückschnitt Monate** | Multi-Select | Monate: Januar, Februar, März, April, Mai, Juni, Juli, August, September, Oktober, November, Dezember |
| **Rückschnitt Anleitung** | Text | Detaillierte Schnittanleitung |
| **Letzter Rückschnitt** | Date | Datum des letzten Rückschnitts |

### Pflege & Notizen

| Property Name | Property Typ | Beschreibung |
|--------------|-------------|--------------|
| **Pflegehinweise** | Text | Allgemeine Pflegetipps |
| **Besonderheiten** | Text | Spezielle Anforderungen |
| **Notizen** | Text | Freie Notizen |

## 3. Formula-Felder konfigurieren

### Für "Nächste Düngung":

1. Klicke auf die Spalte "Nächste Düngung"
2. Wähle Property Type: **Formula**
3. Füge ein:
```
dateAdd(prop("Letzte Düngung"), prop("Düngung Intervall (Tage)"), "days")
```

### Für "Nächstes Gießen":

1. Klicke auf die Spalte "Nächstes Gießen"
2. Wähle Property Type: **Formula**
3. Füge ein:
```
dateAdd(prop("Letztes Gießen"), prop("Gießen Intervall (Tage)"), "days")
```

## 4. Integration mit Datenbank verbinden

1. Klicke oben rechts in der Datenbank auf **"..."** (drei Punkte)
2. Scrolle zu **"Connections"** oder **"Verbindungen"**
3. Klicke auf **"+ Add connection"**
4. Wähle deine Integration: **"Home Assistant Garten"**
5. Klicke auf **"Confirm"** / **"Bestätigen"**

## 5. Datenbank-ID ermitteln

1. Klicke oben rechts auf **"..."** und dann **"Open as page"** / **"Als Seite öffnen"**
2. Kopiere die URL aus der Adressleiste
3. Die URL sieht so aus:
   ```
   https://www.notion.so/WORKSPACE_NAME/DATABASE_ID?v=VIEW_ID
   ```
4. Die **DATABASE_ID** ist der 32-stellige Code zwischen dem letzten `/` und dem `?`
   - Beispiel: `https://www.notion.so/myworkspace/a1b2c3d4e5f6...?v=...`
   - DATABASE_ID = `a1b2c3d4e5f6...`

5. **Kopiere diese DATABASE_ID** - wir brauchen sie im nächsten Schritt!

## 6. Beispieldaten eintragen (Optional)

Trage ein paar Testpflanzen ein:

### Beispiel 1: Tomaten
- **Name:** Tomaten
- **Typ:** Gemüse
- **Standort:** Garten
- **Aktiv:** ✓
- **Düngung Intervall:** 14 Tage
- **Letzte Düngung:** vor 10 Tagen
- **Gießen Intervall:** 2 Tage
- **Letztes Gießen:** gestern
- **Rückschnitt Monate:** März, September
- **Rückschnitt Anleitung:** "Geiztriebe regelmäßig entfernen"

### Beispiel 2: Rosenbusch
- **Name:** Rosenbusch
- **Typ:** Pflanze
- **Standort:** Garten
- **Aktiv:** ✓
- **Düngung Intervall:** 30 Tage
- **Letzte Düngung:** vor 25 Tagen
- **Gießen Intervall:** 7 Tage
- **Letztes Gießen:** vor 3 Tagen
- **Rückschnitt Monate:** Februar, März
- **Rückschnitt Anleitung:** "Im Frühjahr auf 3-5 Augen zurückschneiden"

---

## Fertig! ✓

Sobald du die DATABASE_ID hast, können wir mit dem nächsten Schritt weitermachen!
