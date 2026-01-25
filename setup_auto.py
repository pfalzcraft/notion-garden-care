#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatisches Notion Gartenpflege Datenbank Setup Script
Läuft ohne Benutzerinteraktion
"""

import os
import sys
import io

# Fix Windows Console Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Lade Umgebungsvariablen
load_dotenv()

NOTION_TOKEN = os.getenv('NOTION_TOKEN')

if not NOTION_TOKEN:
    print("❌ FEHLER: NOTION_TOKEN nicht gefunden!")
    print("Bitte füge dein Token in die .env Datei ein.")
    sys.exit(1)

# Initialisiere Notion Client
notion = Client(auth=NOTION_TOKEN)

def find_or_create_parent_page():
    """Sucht nach einer Page oder erstellt eine neue"""
    print("\n🔍 Suche nach Pages im Workspace...")

    try:
        # Suche nach Pages
        response = notion.search(
            filter={
                "property": "object",
                "value": "page"
            },
            page_size=10
        )

        pages = response.get('results', [])

        if pages:
            # Nutze die erste verfügbare Page
            page_id = pages[0]['id']
            title = "Ohne Titel"

            try:
                if 'properties' in pages[0] and 'title' in pages[0]['properties']:
                    title_prop = pages[0]['properties']['title']
                    if title_prop.get('title') and len(title_prop['title']) > 0:
                        title = title_prop['title'][0]['plain_text']
            except:
                pass

            print(f"✅ Verwende existierende Page: '{title}'")
            print(f"   ID: {page_id}")
            return page_id

    except Exception as e:
        print(f"⚠️  Warnung bei der Suche: {e}")

    # Wenn keine Page gefunden wurde oder Fehler, erstelle eine neue
    print("\n📄 Erstelle neue Parent-Page 'Home Assistant Gartenpflege'...")

    try:
        # Versuche, eine Top-Level Page zu erstellen
        parent_page = notion.pages.create(
            parent={
                "type": "workspace",
                "workspace": True
            },
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Home Assistant Gartenpflege"
                            }
                        }
                    ]
                }
            }
        )

        page_id = parent_page['id']
        print(f"✅ Neue Page erstellt!")
        print(f"   ID: {page_id}")
        return page_id

    except Exception as e:
        print(f"\n❌ Fehler: Konnte keine Page erstellen: {e}")
        print("\n💡 Bitte erstelle manuell eine Page in Notion und führe dann aus:")
        print("   python setup_notion_database.py")
        return None

def create_garden_database(parent_page_id):
    """Erstellt die Gartenpflege-Datenbank mit allen Properties"""
    print("\n🌱 Erstelle Gartenpflege-Datenbank...")

    try:
        database = notion.databases.create(
            parent={
                "type": "page_id",
                "page_id": parent_page_id
            },
            title=[
                {
                    "type": "text",
                    "text": {
                        "content": "Gartenpflege"
                    }
                }
            ],
            properties={
                # Basis-Informationen
                "Name": {
                    "title": {}
                },
                "Typ": {
                    "select": {
                        "options": [
                            {"name": "Pflanze", "color": "green"},
                            {"name": "Baum", "color": "brown"},
                            {"name": "Strauch", "color": "yellow"},
                            {"name": "Gemüse", "color": "orange"},
                            {"name": "Kräuter", "color": "pink"},
                            {"name": "Rasen", "color": "green"}
                        ]
                    }
                },
                "Standort": {
                    "select": {
                        "options": [
                            {"name": "Garten", "color": "green"},
                            {"name": "Balkon", "color": "blue"},
                            {"name": "Terrasse", "color": "purple"},
                            {"name": "Wintergarten", "color": "yellow"},
                            {"name": "Innenraum", "color": "gray"}
                        ]
                    }
                },
                "Aktiv": {
                    "checkbox": {}
                },

                # Düngung
                "Düngung Intervall (Tage)": {
                    "number": {
                        "format": "number"
                    }
                },
                "Letzte Düngung": {
                    "date": {}
                },
                "Nächste Düngung": {
                    "formula": {
                        "expression": 'dateAdd(prop("Letzte Düngung"), prop("Düngung Intervall (Tage)"), "days")'
                    }
                },
                "Dünger-Art": {
                    "rich_text": {}
                },

                # Bewässerung
                "Gießen Intervall (Tage)": {
                    "number": {
                        "format": "number"
                    }
                },
                "Letztes Gießen": {
                    "date": {}
                },
                "Nächstes Gießen": {
                    "formula": {
                        "expression": 'dateAdd(prop("Letztes Gießen"), prop("Gießen Intervall (Tage)"), "days")'
                    }
                },
                "Wassermenge": {
                    "select": {
                        "options": [
                            {"name": "Wenig", "color": "yellow"},
                            {"name": "Mittel", "color": "blue"},
                            {"name": "Viel", "color": "blue"}
                        ]
                    }
                },

                # Rückschnitt
                "Rückschnitt Monate": {
                    "multi_select": {
                        "options": [
                            {"name": "Januar", "color": "gray"},
                            {"name": "Februar", "color": "gray"},
                            {"name": "März", "color": "green"},
                            {"name": "April", "color": "green"},
                            {"name": "Mai", "color": "green"},
                            {"name": "Juni", "color": "yellow"},
                            {"name": "Juli", "color": "yellow"},
                            {"name": "August", "color": "orange"},
                            {"name": "September", "color": "orange"},
                            {"name": "Oktober", "color": "brown"},
                            {"name": "November", "color": "brown"},
                            {"name": "Dezember", "color": "gray"}
                        ]
                    }
                },
                "Rückschnitt Anleitung": {
                    "rich_text": {}
                },
                "Letzter Rückschnitt": {
                    "date": {}
                },

                # Pflege & Notizen
                "Pflegehinweise": {
                    "rich_text": {}
                },
                "Besonderheiten": {
                    "rich_text": {}
                },
                "Notizen": {
                    "rich_text": {}
                }
            }
        )

        database_id = database['id']
        database_url = database['url']

        print(f"\n✅ Datenbank erfolgreich erstellt!")
        print(f"\n📊 Datenbank-Details:")
        print(f"   ID:  {database_id}")
        print(f"   URL: {database_url}")

        # Speichere die Database-ID in .env
        update_env_file(database_id)

        return database_id

    except Exception as e:
        print(f"\n❌ Fehler beim Erstellen der Datenbank: {e}")
        return None

def update_env_file(database_id):
    """Aktualisiert die .env Datei mit der Database-ID"""
    try:
        env_path = '.env'

        # Lese bestehende .env
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Aktualisiere Database-ID
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('NOTION_DATABASE_ID='):
                lines[i] = f'NOTION_DATABASE_ID={database_id}\n'
                updated = True
                break

        if not updated:
            lines.append(f'NOTION_DATABASE_ID={database_id}\n')

        # Schreibe zurück
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"\n✅ .env Datei aktualisiert mit Database-ID")

    except Exception as e:
        print(f"\n⚠️  Warnung: Konnte .env nicht aktualisieren: {e}")
        print(f"   Bitte füge manuell hinzu: NOTION_DATABASE_ID={database_id}")

def add_example_plants(database_id):
    """Fügt Beispielpflanzen zur Datenbank hinzu"""
    print("\n🌱 Füge Beispielpflanzen hinzu...")

    example_plants = [
        {
            "Name": "Tomaten",
            "Typ": "Gemüse",
            "Standort": "Garten",
            "Aktiv": True,
            "Düngung Intervall (Tage)": 14,
            "Letzte Düngung": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "Dünger-Art": "Tomatendünger, NPK 5-6-8",
            "Gießen Intervall (Tage)": 2,
            "Letztes Gießen": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "Wassermenge": "Viel",
            "Rückschnitt Monate": ["März", "September"],
            "Rückschnitt Anleitung": "Geiztriebe regelmäßig entfernen. Nach der Ernte bodennah abschneiden.",
            "Pflegehinweise": "Regelmäßig düngen und ausreichend wässern. Stütze anbringen.",
            "Besonderheiten": "Benötigt sonnigen Standort"
        },
        {
            "Name": "Rosenbusch",
            "Typ": "Pflanze",
            "Standort": "Garten",
            "Aktiv": True,
            "Düngung Intervall (Tage)": 30,
            "Letzte Düngung": (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d"),
            "Dünger-Art": "Rosendünger",
            "Gießen Intervall (Tage)": 7,
            "Letztes Gießen": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "Wassermenge": "Mittel",
            "Rückschnitt Monate": ["Februar", "März"],
            "Rückschnitt Anleitung": "Im Frühjahr auf 3-5 Augen zurückschneiden. Schwache und kranke Triebe entfernen.",
            "Pflegehinweise": "Nach Blüte verblühte Rosen entfernen",
            "Besonderheiten": "Frostempfindlich, im Winter schützen"
        },
        {
            "Name": "Apfelbaum",
            "Typ": "Baum",
            "Standort": "Garten",
            "Aktiv": True,
            "Düngung Intervall (Tage)": 90,
            "Letzte Düngung": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "Dünger-Art": "Obstbaumdünger",
            "Gießen Intervall (Tage)": 14,
            "Letztes Gießen": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
            "Wassermenge": "Viel",
            "Rückschnitt Monate": ["Februar", "März"],
            "Rückschnitt Anleitung": "Auslichtungsschnitt: Kranke, nach innen wachsende und sich kreuzende Äste entfernen.",
            "Pflegehinweise": "Regelmäßig auf Schädlinge kontrollieren",
            "Besonderheiten": "Benötigt Bestäuber in der Nähe"
        },
        {
            "Name": "Basilikum",
            "Typ": "Kräuter",
            "Standort": "Balkon",
            "Aktiv": True,
            "Düngung Intervall (Tage)": 21,
            "Letzte Düngung": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
            "Dünger-Art": "Flüssigdünger für Kräuter",
            "Gießen Intervall (Tage)": 3,
            "Letztes Gießen": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "Wassermenge": "Mittel",
            "Rückschnitt Monate": ["Mai", "Juni", "Juli", "August"],
            "Rückschnitt Anleitung": "Regelmäßig Blätter ernten, um Verzweigung zu fördern. Blüten entfernen.",
            "Pflegehinweise": "Warm und sonnig halten, nicht zu nass",
            "Besonderheiten": "Nicht winterhart, im Herbst ernten"
        }
    ]

    for plant_data in example_plants:
        try:
            properties = {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": plant_data["Name"]
                            }
                        }
                    ]
                },
                "Typ": {
                    "select": {
                        "name": plant_data["Typ"]
                    }
                },
                "Standort": {
                    "select": {
                        "name": plant_data["Standort"]
                    }
                },
                "Aktiv": {
                    "checkbox": plant_data["Aktiv"]
                },
                "Düngung Intervall (Tage)": {
                    "number": plant_data["Düngung Intervall (Tage)"]
                },
                "Letzte Düngung": {
                    "date": {
                        "start": plant_data["Letzte Düngung"]
                    }
                },
                "Dünger-Art": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Dünger-Art"]
                            }
                        }
                    ]
                },
                "Gießen Intervall (Tage)": {
                    "number": plant_data["Gießen Intervall (Tage)"]
                },
                "Letztes Gießen": {
                    "date": {
                        "start": plant_data["Letztes Gießen"]
                    }
                },
                "Wassermenge": {
                    "select": {
                        "name": plant_data["Wassermenge"]
                    }
                },
                "Rückschnitt Monate": {
                    "multi_select": [{"name": month} for month in plant_data["Rückschnitt Monate"]]
                },
                "Rückschnitt Anleitung": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Rückschnitt Anleitung"]
                            }
                        }
                    ]
                },
                "Pflegehinweise": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Pflegehinweise"]
                            }
                        }
                    ]
                },
                "Besonderheiten": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Besonderheiten"]
                            }
                        }
                    ]
                }
            }

            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )

            print(f"   ✅ {plant_data['Name']} hinzugefügt")

        except Exception as e:
            print(f"   ❌ Fehler bei {plant_data['Name']}: {e}")

    print("\n✅ Beispielpflanzen wurden hinzugefügt!")

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("🌱 Notion Gartenpflege Datenbank Setup (Automatisch)")
    print("=" * 60)

    # Finde oder erstelle Parent-Page
    parent_page_id = find_or_create_parent_page()

    if not parent_page_id:
        print("\n❌ Setup abgebrochen.")
        sys.exit(1)

    # Erstelle Datenbank
    database_id = create_garden_database(parent_page_id)

    if not database_id:
        print("\n❌ Setup fehlgeschlagen.")
        sys.exit(1)

    # Füge Beispielpflanzen hinzu
    add_example_plants(database_id)

    print("\n" + "=" * 60)
    print("🎉 Setup erfolgreich abgeschlossen!")
    print("=" * 60)
    print("\n📋 Nächste Schritte:")
    print("   1. Öffne die Datenbank in Notion")
    print("   2. Füge weitere Pflanzen hinzu")
    print("   3. Weiter mit Home Assistant Integration")
    print(f"\n   Database-ID: {database_id}")
    print("\n")

if __name__ == "__main__":
    main()
