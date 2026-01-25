# Notion + Home Assistant Integration für Gartenpflege

Diese Anleitung zeigt dir, wie du eine Notion-Datenbank für Gartenpflege erstellst und diese mit Home Assistant verknüpfst, um automatische Erinnerungen und Tasks zu erstellen.

## Voraussetzungen

- Notion-Account (kostenlos verfügbar)
- Home Assistant Installation (lokal oder über Cloud)
- Home Assistant Community Store (HACS) installiert

---

## Teil 1: Notion-Datenbank erstellen

### Schritt 1: Neue Notion-Integration erstellen

1. Gehe zu [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Klicke auf **"+ Neue Integration"**
3. Gib der Integration einen Namen (z.B. "Home Assistant Garten")
4. Wähle den Workspace aus
5. Klicke auf **"Absenden"**
6. **Kopiere den "Internal Integration Token"** (wird später benötigt)

### Schritt 2: Gartenpflege-Datenbank anlegen

1. Erstelle eine neue Seite in Notion
2. Füge eine **Datenbank (Tabelle)** hinzu
3. Benenne sie z.B. "Gartenpflege"

### Schritt 3: Datenbank-Properties konfigurieren

Füge folgende Properties (Spalten) hinzu:

| Property-Name | Typ | Beschreibung |
|--------------|-----|--------------|
| **Name** | Titel | Name der Pflanze/des Baums |
| **Typ** | Select | Pflanze, Baum, Rasen, Gemüse, etc. |
| **Düngung** | Multi-Select | Zeitpunkte (z.B. "März", "Juni", "September") |
| **Düngung Intervall** | Number | Alle X Tage düngen |
| **Letzte Düngung** | Date | Datum der letzten Düngung |
| **Nächste Düngung** | Formula | `dateAdd(prop("Letzte Düngung"), prop("Düngung Intervall"), "days")` |
| **Rückschnitt Zeitpunkt** | Multi-Select | Monate (z.B. "Februar", "März") |
| **Rückschnitt Anleitung** | Text | Detaillierte Anleitung zum Rückschnitt |
| **Letzter Rückschnitt** | Date | Datum des letzten Rückschnitts |
| **Pflegehinweise** | Text | Allgemeine Pflegetipps |
| **Gießen Intervall** | Number | Alle X Tage gießen |
| **Letztes Gießen** | Date | Datum des letzten Gießens |
| **Nächstes Gießen** | Formula | `dateAdd(prop("Letztes Gießen"), prop("Gießen Intervall"), "days")` |
| **Standort** | Select | Garten, Balkon, Wintergarten, etc. |
| **Aktiv** | Checkbox | Ist die Pflanze noch vorhanden? |

### Schritt 4: Integration mit Datenbank verknüpfen

1. Öffne die erstellte Datenbank in Notion
2. Klicke oben rechts auf **"•••" (Mehr)**
3. Scrolle zu **"Verbindungen"** oder **"Connections"**
4. Wähle deine zuvor erstellte Integration aus (z.B. "Home Assistant Garten")
5. Klicke auf **"Bestätigen"**

### Schritt 5: Datenbank-ID ermitteln

1. Öffne die Datenbank als **Vollständige Seite**
2. Kopiere die URL aus der Adressleiste:
   ```
   https://www.notion.so/[WORKSPACE]/[DATABASE_ID]?v=[VIEW_ID]
   ```
3. Die **DATABASE_ID** ist der 32-stellige Hexadezimal-Code zwischen dem letzten `/` und dem `?`
4. Speichere diese ID

---

## Teil 2: Home Assistant konfigurieren

### Schritt 6: Notion-Integration in Home Assistant installieren

#### Option A: Via HACS (empfohlen)

1. Öffne Home Assistant
2. Gehe zu **HACS** → **Integrationen**
3. Suche nach **"Notion"**
4. Installiere die Integration
5. Starte Home Assistant neu

#### Option B: Manuelle Installation

Falls keine offizielle Notion-Integration verfügbar ist, nutze **RESTful API**:

1. Bearbeite `configuration.yaml`
2. Füge hinzu:

```yaml
rest_command:
  notion_query_database:
    url: "https://api.notion.com/v1/databases/DEINE_DATABASE_ID/query"
    method: POST
    headers:
      Authorization: "Bearer DEIN_NOTION_TOKEN"
      Notion-Version: "2022-06-28"
      Content-Type: "application/json"
    payload: '{{ payload }}'
```

### Schritt 7: Secrets konfigurieren

1. Bearbeite `secrets.yaml`:

```yaml
notion_token: "secret_DEIN_NOTION_INTEGRATION_TOKEN"
notion_database_id: "DEINE_DATABASE_ID"
```

2. Aktualisiere `configuration.yaml`:

```yaml
rest_command:
  notion_query_database:
    url: "https://api.notion.com/v1/databases/{{ states('input_text.notion_db_id') }}/query"
    method: POST
    headers:
      Authorization: "Bearer {{ states('input_text.notion_token') }}"
      Notion-Version: "2022-06-28"
      Content-Type: "application/json"
```

### Schritt 8: Input Helper erstellen

Gehe zu **Einstellungen** → **Geräte & Dienste** → **Helfer** und erstelle:

1. **Text-Helfer** für Notion Token:
   - Name: `notion_token`
   - Wert: Dein Notion Integration Token

2. **Text-Helfer** für Database ID:
   - Name: `notion_db_id`
   - Wert: Deine Database ID

---

## Teil 3: Sensoren und Automatisierung erstellen

### Schritt 9: RESTful Sensor konfigurieren

Füge zu `configuration.yaml` hinzu:

```yaml
sensor:
  - platform: rest
    name: Gartenpflege Notion
    resource: https://api.notion.com/v1/databases/DEINE_DATABASE_ID/query
    method: POST
    headers:
      Authorization: !secret notion_token
      Notion-Version: "2022-06-28"
      Content-Type: "application/json"
    json_attributes_path: "$.results"
    json_attributes:
      - results
    value_template: "{{ value_json.results | length }}"
    scan_interval: 3600  # Aktualisierung alle Stunde
```

### Schritt 10: Template-Sensoren für fällige Aufgaben

Füge zu `configuration.yaml` hinzu:

```yaml
template:
  - sensor:
      - name: "Pflanzen zu düngen"
        state: >
          {% set ns = namespace(count=0) %}
          {% set plants = state_attr('sensor.gartenpflege_notion', 'results') %}
          {% if plants %}
            {% for plant in plants %}
              {% set next_fertilize = plant.properties['Nächste Düngung'].formula.date %}
              {% if next_fertilize and next_fertilize <= now().strftime('%Y-%m-%d') %}
                {% set ns.count = ns.count + 1 %}
              {% endif %}
            {% endfor %}
          {% endif %}
          {{ ns.count }}
        attributes:
          plants: >
            {% set ns = namespace(list=[]) %}
            {% set plants = state_attr('sensor.gartenpflege_notion', 'results') %}
            {% if plants %}
              {% for plant in plants %}
                {% set next_fertilize = plant.properties['Nächste Düngung'].formula.date %}
                {% if next_fertilize and next_fertilize <= now().strftime('%Y-%m-%d') %}
                  {% set ns.list = ns.list + [plant.properties.Name.title[0].plain_text] %}
                {% endif %}
              {% endfor %}
            {% endif %}
            {{ ns.list }}

      - name: "Pflanzen zu gießen"
        state: >
          {% set ns = namespace(count=0) %}
          {% set plants = state_attr('sensor.gartenpflege_notion', 'results') %}
          {% if plants %}
            {% for plant in plants %}
              {% set next_water = plant.properties['Nächstes Gießen'].formula.date %}
              {% if next_water and next_water <= now().strftime('%Y-%m-%d') %}
                {% set ns.count = ns.count + 1 %}
              {% endif %}
            {% endfor %}
          {% endif %}
          {{ ns.count }}
        attributes:
          plants: >
            {% set ns = namespace(list=[]) %}
            {% set plants = state_attr('sensor.gartenpflege_notion', 'results') %}
            {% if plants %}
              {% for plant in plants %}
                {% set next_water = plant.properties['Nächstes Gießen'].formula.date %}
                {% if next_water and next_water <= now().strftime('%Y-%m-%d') %}
                  {% set ns.list = ns.list + [plant.properties.Name.title[0].plain_text] %}
                {% endif %}
              {% endfor %}
            {% endif %}
            {{ ns.list }}

      - name: "Pflanzen zu schneiden"
        state: >
          {% set ns = namespace(count=0) %}
          {% set plants = state_attr('sensor.gartenpflege_notion', 'results') %}
          {% set current_month = now().strftime('%B') | lower %}
          {% set month_map = {
            'january': 'Januar', 'february': 'Februar', 'march': 'März',
            'april': 'April', 'may': 'Mai', 'june': 'Juni',
            'july': 'Juli', 'august': 'August', 'september': 'September',
            'october': 'Oktober', 'november': 'November', 'december': 'Dezember'
          } %}
          {% set german_month = month_map[current_month] %}
          {% if plants %}
            {% for plant in plants %}
              {% set prune_times = plant.properties['Rückschnitt Zeitpunkt'].multi_select %}
              {% if prune_times %}
                {% for time in prune_times %}
                  {% if time.name == german_month %}
                    {% set ns.count = ns.count + 1 %}
                  {% endif %}
                {% endfor %}
              {% endif %}
            {% endfor %}
          {% endif %}
          {{ ns.count }}
```

### Schritt 11: Todo-Liste Integration (optional)

Falls du Home Assistant's **To-Do Listen** nutzen möchtest:

```yaml
# configuration.yaml
todo:
  - platform: local_todo
    name: Gartenpflege Aufgaben
```

### Schritt 12: Automatisierungen erstellen

#### Automatisierung 1: Tägliche Benachrichtigung für Düngung

```yaml
# automations.yaml
- id: notify_fertilize_plants
  alias: "Benachrichtigung: Pflanzen düngen"
  trigger:
    - platform: time
      at: "08:00:00"
  condition:
    - condition: numeric_state
      entity_id: sensor.pflanzen_zu_dungen
      above: 0
  action:
    - service: notify.notify
      data:
        title: "Gartenpflege: Düngung fällig"
        message: >
          Folgende Pflanzen müssen gedüngt werden:
          {{ state_attr('sensor.pflanzen_zu_dungen', 'plants') | join(', ') }}
```

#### Automatisierung 2: Bewässerungswarnung

```yaml
- id: notify_water_plants
  alias: "Benachrichtigung: Pflanzen gießen"
  trigger:
    - platform: time
      at: "07:00:00"
  condition:
    - condition: numeric_state
      entity_id: sensor.pflanzen_zu_giessen
      above: 0
  action:
    - service: notify.notify
      data:
        title: "Gartenpflege: Gießen erforderlich"
        message: >
          Folgende Pflanzen müssen gegossen werden:
          {{ state_attr('sensor.pflanzen_zu_giessen', 'plants') | join(', ') }}
```

#### Automatisierung 3: Monatliche Rückschnitt-Erinnerung

```yaml
- id: notify_prune_plants
  alias: "Benachrichtigung: Pflanzen schneiden"
  trigger:
    - platform: time
      at: "08:00:00"
    - platform: state
      entity_id: sensor.pflanzen_zu_schneiden
  condition:
    - condition: numeric_state
      entity_id: sensor.pflanzen_zu_schneiden
      above: 0
  action:
    - service: notify.notify
      data:
        title: "Gartenpflege: Rückschnitt im {{ now().strftime('%B') }}"
        message: >
          Diesen Monat sollten folgende Pflanzen geschnitten werden.
          Prüfe in Notion für Details zur Anleitung!
```

#### Automatisierung 4: Todo-Tasks automatisch erstellen

```yaml
- id: create_garden_todos
  alias: "Erstelle Gartenpflege To-Dos"
  trigger:
    - platform: time
      at: "06:00:00"
  action:
    # Düngung
    - repeat:
        count: "{{ state_attr('sensor.pflanzen_zu_dungen', 'plants') | length }}"
        sequence:
          - service: todo.add_item
            target:
              entity_id: todo.gartenpflege_aufgaben
            data:
              item: "{{ state_attr('sensor.pflanzen_zu_dungen', 'plants')[repeat.index - 1] }} düngen"
              due_date: "{{ now().strftime('%Y-%m-%d') }}"

    # Gießen
    - repeat:
        count: "{{ state_attr('sensor.pflanzen_zu_giessen', 'plants') | length }}"
        sequence:
          - service: todo.add_item
            target:
              entity_id: todo.gartenpflege_aufgaben
            data:
              item: "{{ state_attr('sensor.pflanzen_zu_giessen', 'plants')[repeat.index - 1] }} gießen"
              due_date: "{{ now().strftime('%Y-%m-%d') }}"
```

---

## Teil 4: Erweiterte Konfiguration

### Schritt 13: Dashboard-Karte erstellen

Erstelle eine übersichtliche Lovelace-Karte:

```yaml
type: vertical-stack
cards:
  - type: entity
    entity: sensor.gartenpflege_notion
    name: Pflanzen in Datenbank
    icon: mdi:flower

  - type: entities
    title: Anstehende Aufgaben
    entities:
      - entity: sensor.pflanzen_zu_dungen
        name: Zu düngen
        icon: mdi:spray-bottle
      - entity: sensor.pflanzen_zu_giessen
        name: Zu gießen
        icon: mdi:watering-can
      - entity: sensor.pflanzen_zu_schneiden
        name: Zu schneiden
        icon: mdi:content-cut

  - type: todo-list
    entity: todo.gartenpflege_aufgaben
    title: Gartenpflege Aufgaben
```

### Schritt 14: Beispieldaten in Notion eintragen

Trage Beispielpflanzen ein:

| Name | Typ | Düngung Intervall | Letzte Düngung | Gießen Intervall | Letztes Gießen | Rückschnitt Zeitpunkt | Rückschnitt Anleitung |
|------|-----|-------------------|----------------|------------------|----------------|-----------------------|-----------------------|
| Tomaten | Gemüse | 14 | 2026-01-10 | 2 | 2026-01-24 | März, September | Geiztriebe entfernen, nach der Ernte bodennah abschneiden |
| Rosenbusch | Pflanze | 30 | 2025-12-20 | 7 | 2026-01-20 | Februar, März | Im Frühjahr auf 3-5 Augen zurückschneiden |
| Apfelbaum | Baum | 90 | 2025-11-01 | 14 | 2026-01-15 | Februar, März | Auslichtungsschnitt, kranke Äste entfernen |

---

## Teil 5: Testen und Optimieren

### Schritt 15: Integration testen

1. Starte Home Assistant neu
2. Prüfe unter **Entwicklerwerkzeuge** → **Zustände**, ob der Sensor `sensor.gartenpflege_notion` erscheint
3. Überprüfe die Werte der Template-Sensoren
4. Teste die Automatisierungen manuell

### Schritt 16: Fehlerbehandlung

Häufige Probleme:

**Problem:** Sensor zeigt "unavailable"
- **Lösung:** Prüfe Token und Database ID, stelle sicher, dass die Integration Zugriff auf die Datenbank hat

**Problem:** Template-Sensoren zeigen falsche Werte
- **Lösung:** Überprüfe die Property-Namen in Notion (Groß-/Kleinschreibung beachten!)

**Problem:** Keine Benachrichtigungen
- **Lösung:** Stelle sicher, dass `notify.notify` konfiguriert ist (z.B. Mobile App oder Telegram)

---

## Teil 6: Erweiterungsmöglichkeiten

### Ideen für weitere Funktionen:

1. **Wetterbasierte Anpassungen:**
   - Gieß-Intervalle bei Regen automatisch verlängern
   - Warnung vor Frost für empfindliche Pflanzen

2. **Bodenfeuchtigkeit-Sensoren:**
   - Integration von Zigbee-Bodensensoren
   - Automatisches Aktualisieren von "Letztes Gießen" in Notion

3. **Foto-Dokumentation:**
   - Automatisches Hochladen von Pflanzenfotos zu Notion
   - Integration mit Home Assistant Kamera

4. **Ernteplanung:**
   - Zusätzliche Property "Erntezeit" für Gemüse
   - Benachrichtigungen zur Erntebereitschaft

5. **Bidirektionale Synchronisation:**
   - Wenn Task in Home Assistant erledigt → Update in Notion
   - Nutze Node-RED oder AppDaemon für komplexe Logik

---

## Zusätzliche Ressourcen

- **Notion API Dokumentation:** [https://developers.notion.com](https://developers.notion.com)
- **Home Assistant RESTful Integration:** [https://www.home-assistant.io/integrations/rest/](https://www.home-assistant.io/integrations/rest/)
- **Home Assistant Templates:** [https://www.home-assistant.io/docs/configuration/templating/](https://www.home-assistant.io/docs/configuration/templating/)

---

## Zusammenfassung

Nach Abschluss dieser Anleitung hast du:

- ✅ Eine strukturierte Notion-Datenbank für Gartenpflege
- ✅ Automatische Erinnerungen für Düngung, Gießen und Rückschnitt
- ✅ Integration in dein Home Assistant Dashboard
- ✅ Optional: Automatisch generierte To-Do-Listen

Die Pflege deines Gartens wird damit deutlich systematischer und du vergisst keine wichtigen Aufgaben mehr!
