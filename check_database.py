#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft die Datenbank-Properties
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

# Lade Umgebungsvariablen
load_dotenv()

NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

notion = Client(auth=NOTION_TOKEN)

# Hole Datenbank-Info
database = notion.databases.retrieve(database_id=DATABASE_ID)

print("=" * 60)
print("📊 Datenbank-Eigenschaften")
print("=" * 60)
print(f"\nDatenbank-Name: {database['title'][0]['plain_text']}")
print(f"Database-ID: {DATABASE_ID}")

if 'properties' in database:
    print(f"\nProperties:")
    for prop_name, prop_data in database['properties'].items():
        prop_type = prop_data['type']
        print(f"  - {prop_name}: {prop_type}")
else:
    print("\nDebug - Database keys:")
    print(list(database.keys()))
    import json
    print("\nFull database info:")
    print(json.dumps(database, indent=2, ensure_ascii=False))

print("\n" + "=" * 60)
