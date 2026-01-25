#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Creates the Garden Care database in English in the specified page
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

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
# Page-ID from URL: https://www.notion.so/Gardening-23bd91ab65f980168a04d071ba597442
PARENT_PAGE_ID = "23bd91ab65f980168a04d071ba597442"

if not NOTION_TOKEN:
    print("❌ ERROR: NOTION_TOKEN not found!")
    sys.exit(1)

# Initialize Notion Client
notion = Client(auth=NOTION_TOKEN)

def create_garden_database(parent_page_id):
    """Creates the Garden Care database with all properties"""
    print("\n🌱 Creating Garden Care Database...")

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
                        "content": "Garden Care"
                    }
                }
            ],
            properties={
                # Basic Information
                "Name": {
                    "title": {}
                },
                "Type": {
                    "select": {
                        "options": [
                            {"name": "Plant", "color": "green"},
                            {"name": "Tree", "color": "brown"},
                            {"name": "Shrub", "color": "yellow"},
                            {"name": "Vegetable", "color": "orange"},
                            {"name": "Herb", "color": "pink"},
                            {"name": "Lawn", "color": "green"}
                        ]
                    }
                },
                "Location": {
                    "select": {
                        "options": [
                            {"name": "Garden", "color": "green"},
                            {"name": "Balcony", "color": "blue"},
                            {"name": "Terrace", "color": "purple"},
                            {"name": "Conservatory", "color": "yellow"},
                            {"name": "Indoor", "color": "gray"}
                        ]
                    }
                },
                "Active": {
                    "checkbox": {}
                },

                # Fertilizing
                "Fertilize Interval (days)": {
                    "number": {
                        "format": "number"
                    }
                },
                "Last Fertilized": {
                    "date": {}
                },
                "Next Fertilize": {
                    "formula": {
                        "expression": 'dateAdd(prop("Last Fertilized"), prop("Fertilize Interval (days)"), "days")'
                    }
                },
                "Fertilizer Type": {
                    "rich_text": {}
                },

                # Watering
                "Water Interval (days)": {
                    "number": {
                        "format": "number"
                    }
                },
                "Last Watered": {
                    "date": {}
                },
                "Next Water": {
                    "formula": {
                        "expression": 'dateAdd(prop("Last Watered"), prop("Water Interval (days)"), "days")'
                    }
                },
                "Water Amount": {
                    "select": {
                        "options": [
                            {"name": "Low", "color": "yellow"},
                            {"name": "Medium", "color": "blue"},
                            {"name": "High", "color": "blue"}
                        ]
                    }
                },

                # Pruning
                "Prune Months": {
                    "multi_select": {
                        "options": [
                            {"name": "January", "color": "gray"},
                            {"name": "February", "color": "gray"},
                            {"name": "March", "color": "green"},
                            {"name": "April", "color": "green"},
                            {"name": "May", "color": "green"},
                            {"name": "June", "color": "yellow"},
                            {"name": "July", "color": "yellow"},
                            {"name": "August", "color": "orange"},
                            {"name": "September", "color": "orange"},
                            {"name": "October", "color": "brown"},
                            {"name": "November", "color": "brown"},
                            {"name": "December", "color": "gray"}
                        ]
                    }
                },
                "Prune Instructions": {
                    "rich_text": {}
                },
                "Last Pruned": {
                    "date": {}
                },

                # Care & Notes
                "Care Instructions": {
                    "rich_text": {}
                },
                "Special Notes": {
                    "rich_text": {}
                },
                "Notes": {
                    "rich_text": {}
                }
            }
        )

        database_id = database['id']
        database_url = database['url']

        print(f"\n✅ Database successfully created!")
        print(f"\n📊 Database Details:")
        print(f"   ID:  {database_id}")
        print(f"   URL: {database_url}")

        # Save the Database-ID in .env
        update_env_file(database_id)

        return database_id

    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_env_file(database_id):
    """Updates the .env file with the Database-ID"""
    try:
        env_path = '.env'

        # Read existing .env
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Update Database-ID
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('NOTION_DATABASE_ID='):
                lines[i] = f'NOTION_DATABASE_ID={database_id}\n'
                updated = True
                break

        if not updated:
            lines.append(f'NOTION_DATABASE_ID={database_id}\n')

        # Write back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"\n✅ .env file updated with Database-ID")

    except Exception as e:
        print(f"\n⚠️  Warning: Could not update .env: {e}")
        print(f"   Please add manually: NOTION_DATABASE_ID={database_id}")

def add_example_plants(database_id):
    """Adds example plants to the database"""
    print("\n🌱 Adding example plants...")

    example_plants = [
        {
            "Name": "Tomatoes",
            "Type": "Vegetable",
            "Location": "Garden",
            "Active": True,
            "Fertilize Interval (days)": 14,
            "Last Fertilized": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "Fertilizer Type": "Tomato fertilizer, NPK 5-6-8",
            "Water Interval (days)": 2,
            "Last Watered": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "Water Amount": "High",
            "Prune Months": ["March", "September"],
            "Prune Instructions": "Remove suckers regularly. Cut back to ground level after harvest.",
            "Care Instructions": "Fertilize regularly and water sufficiently. Provide support.",
            "Special Notes": "Requires sunny location"
        },
        {
            "Name": "Rose Bush",
            "Type": "Plant",
            "Location": "Garden",
            "Active": True,
            "Fertilize Interval (days)": 30,
            "Last Fertilized": (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d"),
            "Fertilizer Type": "Rose fertilizer",
            "Water Interval (days)": 7,
            "Last Watered": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "Water Amount": "Medium",
            "Prune Months": ["February", "March"],
            "Prune Instructions": "Cut back to 3-5 buds in spring. Remove weak and diseased shoots.",
            "Care Instructions": "Remove spent blooms after flowering",
            "Special Notes": "Frost-sensitive, protect in winter"
        },
        {
            "Name": "Apple Tree",
            "Type": "Tree",
            "Location": "Garden",
            "Active": True,
            "Fertilize Interval (days)": 90,
            "Last Fertilized": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "Fertilizer Type": "Fruit tree fertilizer",
            "Water Interval (days)": 14,
            "Last Watered": (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d"),
            "Water Amount": "High",
            "Prune Months": ["February", "March"],
            "Prune Instructions": "Thinning cut: Remove diseased, inward-growing and crossing branches.",
            "Care Instructions": "Check regularly for pests",
            "Special Notes": "Needs pollinator nearby"
        },
        {
            "Name": "Basil",
            "Type": "Herb",
            "Location": "Balcony",
            "Active": True,
            "Fertilize Interval (days)": 21,
            "Last Fertilized": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
            "Fertilizer Type": "Liquid fertilizer for herbs",
            "Water Interval (days)": 3,
            "Last Watered": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "Water Amount": "Medium",
            "Prune Months": ["May", "June", "July", "August"],
            "Prune Instructions": "Harvest leaves regularly to encourage branching. Remove flowers.",
            "Care Instructions": "Keep warm and sunny, not too wet",
            "Special Notes": "Not winter-hardy, harvest in autumn"
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
                "Type": {
                    "select": {
                        "name": plant_data["Type"]
                    }
                },
                "Location": {
                    "select": {
                        "name": plant_data["Location"]
                    }
                },
                "Active": {
                    "checkbox": plant_data["Active"]
                },
                "Fertilize Interval (days)": {
                    "number": plant_data["Fertilize Interval (days)"]
                },
                "Last Fertilized": {
                    "date": {
                        "start": plant_data["Last Fertilized"]
                    }
                },
                "Fertilizer Type": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Fertilizer Type"]
                            }
                        }
                    ]
                },
                "Water Interval (days)": {
                    "number": plant_data["Water Interval (days)"]
                },
                "Last Watered": {
                    "date": {
                        "start": plant_data["Last Watered"]
                    }
                },
                "Water Amount": {
                    "select": {
                        "name": plant_data["Water Amount"]
                    }
                },
                "Prune Months": {
                    "multi_select": [{"name": month} for month in plant_data["Prune Months"]]
                },
                "Prune Instructions": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Prune Instructions"]
                            }
                        }
                    ]
                },
                "Care Instructions": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Care Instructions"]
                            }
                        }
                    ]
                },
                "Special Notes": {
                    "rich_text": [
                        {
                            "text": {
                                "content": plant_data["Special Notes"]
                            }
                        }
                    ]
                }
            }

            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )

            print(f"   ✅ {plant_data['Name']} added")

        except Exception as e:
            print(f"   ❌ Error adding {plant_data['Name']}: {e}")

    print("\n✅ Example plants added!")

def main():
    """Main function"""
    print("=" * 60)
    print("🌱 Notion Garden Care Database Setup (English)")
    print("=" * 60)
    print(f"\nUsing Page-ID: {PARENT_PAGE_ID}")

    # Create database
    database_id = create_garden_database(PARENT_PAGE_ID)

    if not database_id:
        print("\n❌ Setup failed.")
        sys.exit(1)

    # Add example plants
    add_example_plants(database_id)

    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Open the database in Notion")
    print("   2. Check the example plants")
    print("   3. Continue with Home Assistant integration")
    print(f"\n   Database-ID: {database_id}")
    print("\n")

if __name__ == "__main__":
    main()
