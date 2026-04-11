"""The Notion Garden Care integration."""
from __future__ import annotations

import asyncio
import logging
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import conversation, frontend
from homeassistant.components.http import StaticPathConfig
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_NOTION_TOKEN,
    CONF_DATABASE_ID,
    CONF_CONVERSATION_AGENT,
    SERVICE_UPDATE_WATERED,
    SERVICE_UPDATE_FERTILIZED,
    SERVICE_UPDATE_PRUNED,
    SERVICE_UPDATE_AERATED,
    SERVICE_UPDATE_HARVESTED,
    SERVICE_UPDATE_SANDED,
    SERVICE_UPDATE_MOWED,
    SERVICE_UPDATE_PROPERTY,
    SERVICE_REFRESH_DATA,
    SERVICE_ADD_PLANT,
    SERVICE_DELETE_PLANT,
    ATTR_PAGE_ID,
    ATTR_PLANT_NAME,
    ATTR_PROPERTY_NAME,
    ATTR_PROPERTY_VALUE,
    ATTR_DATE,
    ATTR_ENTITY_ID,
    ATTR_AREA_ID,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# ── Required non-formula database properties ───────────────────────────────
# Used to detect and repair missing columns in existing databases.
_REQUIRED_SIMPLE_PROPERTIES: dict = {
    "Type": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Plant", "color": "green"},
                {"name": "Tree", "color": "brown"},
                {"name": "Shrub", "color": "yellow"},
                {"name": "Vegetable", "color": "orange"},
                {"name": "Herb", "color": "pink"},
                {"name": "Lawn", "color": "green"},
            ]
        },
    },
    "Active": {"type": "checkbox", "checkbox": {}},
    "Lifecycle": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Perennial", "color": "green"},
                {"name": "Annual", "color": "yellow"},
                {"name": "Biennial", "color": "blue"},
            ]
        },
    },
    "Plant Date": {"type": "date", "date": {}},
    "Height": {"type": "rich_text", "rich_text": {}},
    "Growth per Year": {"type": "rich_text", "rich_text": {}},
    "Hardiness Zone": {
        "type": "select",
        "select": {
            "options": [{"name": z, "color": "blue"} for z in
                        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]]
        },
    },
    "Sun Exposure": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Full Sun", "color": "yellow"},
                {"name": "Partial Sun", "color": "yellow"},
                {"name": "Partial Shade", "color": "blue"},
                {"name": "Full Shade", "color": "gray"},
            ]
        },
    },
    "Soil Type": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Sandy", "color": "yellow"},
                {"name": "Loamy", "color": "brown"},
                {"name": "Clay", "color": "orange"},
                {"name": "Silty", "color": "gray"},
                {"name": "Peaty", "color": "brown"},
                {"name": "Chalky", "color": "gray"},
                {"name": "Any", "color": "green"},
            ]
        },
    },
    "Soil pH": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Acidic (pH < 6)", "color": "orange"},
                {"name": "Neutral (pH 6-7)", "color": "green"},
                {"name": "Alkaline (pH > 7)", "color": "blue"},
                {"name": "Any", "color": "gray"},
            ]
        },
    },
    "Water Interval (days)": {"type": "number", "number": {"format": "number"}},
    "Last Watered": {"type": "date", "date": {}},
    "Water Amount": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Low", "color": "yellow"},
                {"name": "Medium", "color": "blue"},
                {"name": "High", "color": "blue"},
            ]
        },
    },
    "Fertilize Interval (days)": {"type": "number", "number": {"format": "number"}},
    "Last Fertilized": {"type": "date", "date": {}},
    "Fertilizer Type": {"type": "rich_text", "rich_text": {}},
    "Prune Months": {
        "type": "multi_select",
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
                {"name": "December", "color": "gray"},
            ]
        },
    },
    "Last Pruned": {"type": "date", "date": {}},
    "Prune Instructions": {"type": "rich_text", "rich_text": {}},
    "Harvest Months": {
        "type": "multi_select",
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
                {"name": "December", "color": "gray"},
            ]
        },
    },
    "Last Harvested": {"type": "date", "date": {}},
    "Harvest Notes": {"type": "rich_text", "rich_text": {}},
    "Aeration Interval (days)": {"type": "number", "number": {"format": "number"}},
    "Last Aeration": {"type": "date", "date": {}},
    "Sanding Interval (days)": {"type": "number", "number": {"format": "number"}},
    "Last Sanded": {"type": "date", "date": {}},
    "Last Mowed": {"type": "date", "date": {}},
    "Companion Plants": {"type": "rich_text", "rich_text": {}},
    "Bad Companions": {"type": "rich_text", "rich_text": {}},
    "Bee Friendly": {"type": "checkbox", "checkbox": {}},
    "Toxicity": {
        "type": "select",
        "select": {
            "options": [
                {"name": "Safe", "color": "green"},
                {"name": "Toxic to Pets", "color": "orange"},
                {"name": "Toxic to Children", "color": "orange"},
                {"name": "Toxic to Both", "color": "red"},
            ]
        },
    },
    "Winterize": {"type": "checkbox", "checkbox": {}},
    "Care Instructions": {"type": "rich_text", "rich_text": {}},
    "Care Instructions URL": {"type": "url", "url": {}},
    "Prune Instructions URL": {"type": "url", "url": {}},
    "Harvest Instructions URL": {"type": "url", "url": {}},
    "Special Notes": {"type": "rich_text", "rich_text": {}},
    "Notes": {"type": "rich_text", "rich_text": {}},
    "Additional Information": {"type": "rich_text", "rich_text": {}},
}

# ── Required formula properties (depend on simple properties existing first) ─
_REQUIRED_FORMULA_PROPERTIES: dict = {
    "Next Water": {
        "type": "formula",
        "formula": {
            "expression": 'dateAdd(prop("Last Watered"), prop("Water Interval (days)"), "days")'
        },
    },
    "Next Fertilize": {
        "type": "formula",
        "formula": {
            "expression": 'dateAdd(prop("Last Fertilized"), prop("Fertilize Interval (days)"), "days")'
        },
    },
    "Next Aeration": {
        "type": "formula",
        "formula": {
            "expression": 'dateAdd(prop("Last Aeration"), prop("Aeration Interval (days)"), "days")'
        },
    },
    "Next Sanding": {
        "type": "formula",
        "formula": {
            "expression": 'dateAdd(prop("Last Sanded"), prop("Sanding Interval (days)"), "days")'
        },
    },
}
URL_BASE = "/notion-garden-care"
_MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text())
FRONTEND_VERSION = _MANIFEST["version"]  # always matches manifest, ensures correct cache-busting

# This integration can only be set up via config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

UPDATE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
        vol.Optional(ATTR_DATE): cv.string,
        vol.Optional(ATTR_AREA_ID): cv.string,
    }
)

UPDATE_PROPERTY_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
        vol.Required(ATTR_PROPERTY_NAME): cv.string,
        vol.Required(ATTR_PROPERTY_VALUE): vol.Any(str, int, float, bool, list),
    }
)

ADD_PLANT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PLANT_NAME): cv.string,
    }
)

DELETE_PLANT_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
    }
)


async def _async_ensure_database_up_to_date(
    hass: HomeAssistant,
    notion_token: str,
    database_id: str,
) -> None:
    """Check the Notion database schema and add any missing columns.

    Uses httpx directly (consistent with the rest of the codebase) to retrieve
    the current database schema and PATCH in any missing properties.
    Simple (non-formula) properties are added first so that formula properties
    can safely reference them.
    """

    def _check_and_update() -> list[str]:
        import httpx

        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        base_url = f"https://api.notion.com/v1/databases/{database_id}"

        # ── Step 1: retrieve current schema ──────────────────────────────
        resp = httpx.get(base_url, headers=headers, timeout=30.0)
        resp.raise_for_status()
        db_props: dict = resp.json().get("properties", {})
        existing: set[str] = set(db_props.keys())
        _LOGGER.debug("Existing Notion database columns: %s", sorted(existing))

        added: list[str] = []

        # ── Step 2: compute missing properties ───────────────────────────
        # Strip the "type" key — the Notion PATCH API infers type from the
        # config key (e.g. "rich_text", "date", "formula", …).
        missing_simple: dict = {
            name: {k: v for k, v in spec.items() if k != "type"}
            for name, spec in _REQUIRED_SIMPLE_PROPERTIES.items()
            if name not in existing
        }
        missing_formula: dict = {
            name: {k: v for k, v in spec.items() if k != "type"}
            for name, spec in _REQUIRED_FORMULA_PROPERTIES.items()
            if name not in existing
        }

        # ── Step 3: add simple properties first ──────────────────────────
        if missing_simple:
            _LOGGER.info(
                "Adding %d missing simple column(s) to Notion database: %s",
                len(missing_simple), list(missing_simple.keys()),
            )
            resp = httpx.patch(
                base_url,
                headers=headers,
                json={"properties": missing_simple},
                timeout=30.0,
            )
            if resp.status_code >= 400:
                _LOGGER.error(
                    "Notion API rejected simple-property update (HTTP %s): %s",
                    resp.status_code, resp.text,
                )
                resp.raise_for_status()
            added.extend(missing_simple.keys())

        # ── Step 4: add formula properties (dependencies now exist) ──────
        if missing_formula:
            _LOGGER.info(
                "Adding %d missing formula column(s) to Notion database: %s",
                len(missing_formula), list(missing_formula.keys()),
            )
            resp = httpx.patch(
                base_url,
                headers=headers,
                json={"properties": missing_formula},
                timeout=30.0,
            )
            if resp.status_code >= 400:
                _LOGGER.error(
                    "Notion API rejected formula-property update (HTTP %s): %s",
                    resp.status_code, resp.text,
                )
                resp.raise_for_status()
            added.extend(missing_formula.keys())

        return added

    try:
        added = await hass.async_add_executor_job(_check_and_update)
        if added:
            _LOGGER.info(
                "Notion database updated — added %d column(s): %s",
                len(added), added,
            )
        else:
            _LOGGER.info("Notion database schema is up to date — no changes needed.")
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error(
            "Could not verify/update Notion database schema: %s",
            err, exc_info=True,
        )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Notion Garden Care integration."""
    hass.data.setdefault(DOMAIN, {"frontend_loaded": False})

    # Register frontend resources early so they're available even before config entry
    await _async_register_frontend(hass)

    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend resources for the custom card and dashboard."""
    # Only register once
    if hass.data[DOMAIN].get("frontend_loaded"):
        _LOGGER.debug("Frontend already loaded, skipping registration")
        return

    frontend_path = Path(__file__).parent / "frontend"
    _LOGGER.info("Frontend path: %s (exists: %s)", frontend_path, frontend_path.exists())

    if not frontend_path.exists():
        _LOGGER.error("Frontend path does not exist: %s", frontend_path)
        return

    # List files in frontend directory for debugging (in executor to avoid blocking)
    try:
        def _list_files():
            return [f.name for f in frontend_path.iterdir()]
        files = await hass.async_add_executor_job(_list_files)
        _LOGGER.info("Frontend files: %s", files)
    except Exception as err:
        _LOGGER.error("Could not list frontend directory: %s", err)

    # Register static path for serving JS files using async method
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                url_path=URL_BASE,
                path=str(frontend_path),
                cache_headers=False
            )
        ])
        _LOGGER.info("Successfully registered static path: %s -> %s", URL_BASE, frontend_path)
    except Exception as err:
        _LOGGER.error("Failed to register static path: %s", err)
        return

    # Add JS files to frontend so they load automatically (with version for cache busting)
    card_url = f"{URL_BASE}/plant-care-card.js?v={FRONTEND_VERSION}"
    strategy_url = f"{URL_BASE}/garden-care-strategy.js?v={FRONTEND_VERSION}"

    try:
        frontend.add_extra_js_url(hass, card_url, es5=False)
        frontend.add_extra_js_url(hass, strategy_url, es5=False)
        _LOGGER.info("Added frontend JS resources: %s, %s", card_url, strategy_url)
    except Exception as err:
        _LOGGER.error("Failed to add extra JS URLs: %s", err)

    # Also register in the global Lovelace resource store so resources load
    # reliably for all dashboards (including the auto-generated one).
    await _async_register_lovelace_resources(hass)

    hass.data[DOMAIN]["frontend_loaded"] = True


async def _async_register_lovelace_resources(hass: HomeAssistant) -> None:
    """Write our JS resources into .storage/lovelace_resources.

    This ensures the card and strategy are loaded globally by Lovelace,
    independent of any resources: block in the dashboard YAML file.
    Old entries pointing at URL_BASE are removed first so the version
    query-string is always up to date.
    """
    import os

    storage_path = hass.config.path(".storage/lovelace_resources")
    card_url = f"{URL_BASE}/plant-care-card.js?v={FRONTEND_VERSION}"
    strategy_url = f"{URL_BASE}/garden-care-strategy.js?v={FRONTEND_VERSION}"

    resources_to_add = {
        "notion_garden_care_card": card_url,
        "notion_garden_care_strategy": strategy_url,
    }

    def _update():
        if os.path.exists(storage_path):
            try:
                with open(storage_path, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = None
        else:
            data = None

        if data is None:
            data = {
                "version": 1,
                "minor_version": 1,
                "key": "lovelace_resources",
                "data": {"items": []},
            }

        items = data.get("data", {}).get("items", [])

        # Remove stale entries for our resources (handles version changes too)
        items = [
            item for item in items
            if item.get("id") not in resources_to_add
            and not item.get("url", "").startswith(URL_BASE + "/")
        ]

        for resource_id, url in resources_to_add.items():
            items.append({"id": resource_id, "url": url, "res_type": "module"})

        data["data"]["items"] = items
        with open(storage_path, "w") as f:
            json.dump(data, f, indent=2)

    try:
        await hass.async_add_executor_job(_update)
        _LOGGER.info("Registered Lovelace resources: %s, %s", card_url, strategy_url)
    except Exception as err:
        _LOGGER.warning("Could not register Lovelace resources: %s", err)


async def _async_generate_dashboard_yaml(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Write (or overwrite) garden-care.yaml with the static root card.

    The custom:garden-care-root-card element discovers all plant sensors at
    runtime from hass.states and groups them by HA area — no dynamic YAML
    generation required. This file only needs to be written once.
    """
    yaml_content = (
        "# Garden Care Dashboard — managed by the Notion Garden Care integration.\n"
        "# The garden-care-root-card auto-discovers plants and groups them by HA area.\n"
        "# Do not add cards here manually; they will be overwritten on the next reload.\n"
        "views:\n"
        "  - title: Plants\n"
        "    path: plants\n"
        "    icon: mdi:flower\n"
        "    panel: true\n"
        "    cards:\n"
        "      - type: custom:garden-care-root-card\n"
    )

    yaml_path = hass.config.path("garden-care.yaml")
    await hass.async_add_executor_job(_write_file, yaml_path, yaml_content)
    _LOGGER.info("Wrote garden-care.yaml (static root card)")


async def _async_create_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register the Garden Care dashboard in Lovelace and write the initial YAML."""
    if hass.data[DOMAIN].get("dashboard_created"):
        return

    hass.data[DOMAIN]["dashboard_created"] = True

    try:
        import os

        # Write the initial YAML (plants will be populated by _async_generate_dashboard_yaml
        # once the coordinator has data)
        await _async_generate_dashboard_yaml(hass, entry)

        # Delete any old storage-mode dashboard config file (from previous versions)
        old_storage_config = hass.config.path(".storage/lovelace.garden-care")
        if await hass.async_add_executor_job(os.path.exists, old_storage_config):
            await hass.async_add_executor_job(os.remove, old_storage_config)
            _LOGGER.info("Removed old storage-mode dashboard config")

        # Also remove old garden-care-dashboard.yaml if it exists
        old_yaml_path = hass.config.path("garden-care-dashboard.yaml")
        if await hass.async_add_executor_job(os.path.exists, old_yaml_path):
            await hass.async_add_executor_job(os.remove, old_yaml_path)
            _LOGGER.info("Removed old garden-care-dashboard.yaml")

        # Try to create dashboard using HA's lovelace APIs
        dashboard_created = await _create_dashboard_via_api(hass)

        if not dashboard_created:
            # Fallback: Show persistent notification to guide user
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "🌱 Garden Care Dashboard Setup",
                    "message": (
                        "To complete setup, please create the Garden Care dashboard:\n\n"
                        "1. Go to **Settings → Dashboards**\n"
                        "2. Click **Add Dashboard**\n"
                        "3. Enter Title: `Garden Care`\n"
                        "4. Enter Icon: `mdi:flower`\n"
                        "5. Select **YAML** mode\n"
                        "6. Enter Filename: `garden-care.yaml`\n"
                        "7. Click **Create**\n\n"
                        "The configuration file has already been created for you."
                    ),
                    "notification_id": "notion_garden_care_setup",
                },
            )
            _LOGGER.info(
                "Please create the Garden Care dashboard manually: "
                "Settings -> Dashboards -> Add Dashboard -> YAML mode -> filename: garden-care.yaml"
            )
        else:
            # Dismiss any existing setup notification
            await hass.services.async_call(
                "persistent_notification",
                "dismiss",
                {"notification_id": "notion_garden_care_setup"},
            )

    except Exception as err:
        _LOGGER.warning("Could not set up dashboard: %s", err)


_DASHBOARD_ENTRY = {
    "id": "garden_care",
    "url_path": "garden-care",
    "mode": "yaml",
    "filename": "garden-care.yaml",
    "title": "Garden Care",
    "icon": "mdi:flower",
    "show_in_sidebar": True,
    "require_admin": False,
}


def _is_correct_dashboard(item: dict) -> bool:
    """Return True only if the item is our YAML-mode dashboard."""
    return (
        item.get("url_path") == "garden-care"
        and item.get("mode") == "yaml"
        and item.get("filename") == "garden-care.yaml"
    )


def _is_conflicting_dashboard(item: dict) -> bool:
    """Return True if the item occupies our url_path but is NOT the correct YAML dashboard."""
    return item.get("url_path") == "garden-care" and not _is_correct_dashboard(item)


async def _create_dashboard_via_api(hass: HomeAssistant) -> bool:
    """Create (or repair) the Garden Care YAML dashboard in Lovelace storage."""
    import os

    storage_path = hass.config.path(".storage/lovelace_dashboards")

    # ------------------------------------------------------------------ #
    # 1. Inspect the on-disk storage file
    # ------------------------------------------------------------------ #
    def _read_storage():
        if not os.path.exists(storage_path):
            return None
        try:
            with open(storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_storage(data):
        with open(storage_path, "w") as f:
            json.dump(data, f, indent=2)

    storage_data = await hass.async_add_executor_job(_read_storage)

    if storage_data is not None:
        items = storage_data.get("data", {}).get("items", [])

        if any(_is_correct_dashboard(item) for item in items):
            _LOGGER.debug("Garden Care YAML dashboard already exists in storage")
            return True

        if any(_is_conflicting_dashboard(item) for item in items):
            _LOGGER.warning(
                "Found a non-YAML 'garden-care' dashboard in storage — replacing with YAML mode"
            )
            # Remove conflicting entry and add the correct one
            items = [i for i in items if not _is_conflicting_dashboard(i)]
            items.append(_DASHBOARD_ENTRY)
            storage_data["data"]["items"] = items
            await hass.async_add_executor_job(_write_storage, storage_data)
            _LOGGER.info("Replaced conflicting dashboard entry in storage file")
            return True

    # ------------------------------------------------------------------ #
    # 2. Try using HA's in-memory lovelace collection API
    # ------------------------------------------------------------------ #
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data:
            dashboards = getattr(lovelace_data, "dashboards", None)
            if dashboards is None and hasattr(lovelace_data, "get"):
                dashboards = lovelace_data.get("dashboards")

            if dashboards and hasattr(dashboards, "async_create_item"):
                if hasattr(dashboards, "data"):
                    correct = any(_is_correct_dashboard(item) for item in dashboards.data.values())
                    conflicting_ids = [
                        k for k, item in dashboards.data.items()
                        if _is_conflicting_dashboard(item)
                    ]
                else:
                    correct = False
                    conflicting_ids = []

                if correct:
                    _LOGGER.debug("Garden Care YAML dashboard already exists in collection")
                    return True

                # Delete any conflicting storage-mode entry first
                if conflicting_ids and hasattr(dashboards, "async_delete_item"):
                    for cid in conflicting_ids:
                        try:
                            await dashboards.async_delete_item(cid)
                            _LOGGER.info("Deleted conflicting dashboard '%s' via HA API", cid)
                        except Exception as del_err:
                            _LOGGER.debug("Could not delete conflicting dashboard: %s", del_err)

                await dashboards.async_create_item(dict(_DASHBOARD_ENTRY))
                _LOGGER.info("Successfully created Garden Care dashboard via HA API")
                return True

    except Exception as err:
        _LOGGER.debug("Could not create dashboard via HA API: %s", err)

    # ------------------------------------------------------------------ #
    # 3. Fallback: write the storage file from scratch
    # ------------------------------------------------------------------ #
    try:
        def _create_storage_file():
            if os.path.exists(storage_path):
                try:
                    with open(storage_path, "r") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    data = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}
            else:
                data = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}

            items = data.get("data", {}).get("items", [])
            # Remove any conflicting entry, then append the correct one
            items = [i for i in items if not _is_conflicting_dashboard(i)]
            if not any(_is_correct_dashboard(i) for i in items):
                items.append(dict(_DASHBOARD_ENTRY))
            data["data"]["items"] = items

            with open(storage_path, "w") as f:
                json.dump(data, f, indent=2)

        await hass.async_add_executor_job(_create_storage_file)
        _LOGGER.info("Created Garden Care dashboard via storage file (fallback)")
        return True

    except Exception as err:
        _LOGGER.warning("Could not create dashboard storage file: %s", err)

    return False


def _write_file(path: str, content: str) -> None:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)


async def _find_pages_by_area(hass: HomeAssistant, area_id: str) -> list[str]:
    """Return page_ids for all plant sensors assigned to the given HA area."""
    from homeassistant.helpers import entity_registry as er
    entity_reg = er.async_get(hass)
    page_ids = []
    for entry in entity_reg.entities.values():
        if entry.area_id == area_id and entry.domain == "sensor" and entry.platform == DOMAIN:
            state = hass.states.get(entry.entity_id)
            if state:
                page_id = state.attributes.get("page_id")
                if page_id:
                    page_ids.append(page_id)
    return page_ids


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notion Garden Care from a config entry."""
    notion_token = entry.data[CONF_NOTION_TOKEN]
    database_id = entry.data[CONF_DATABASE_ID]

    # Create Notion client (in executor to avoid blocking SSL context loading)
    def _create_notion_client():
        return Client(auth=notion_token)

    notion = await hass.async_add_executor_job(_create_notion_client)

    # Test connection
    try:
        await hass.async_add_executor_job(
            notion.databases.retrieve,
            database_id
        )
    except APIResponseError as err:
        _LOGGER.error("Failed to connect to Notion: %s", err)
        raise ConfigEntryNotReady from err

    # Ensure database has all required columns; add any that are missing
    await _async_ensure_database_up_to_date(hass, notion_token, database_id)

    # Store data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "notion": notion,
        "database_id": database_id,
    }

    # Register frontend resources (JS files, static path, lovelace_resources)
    await _async_register_frontend(hass)

    # Setup platforms (creates coordinator and plant sensor entities)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Create / register the Lovelace dashboard and generate the initial YAML.
    # This runs AFTER platforms are set up so the entity registry already
    # contains all plant sensors and area assignments can be read.
    await _async_create_dashboard(hass, entry)

    # The YAML now contains only a static custom:garden-care-root-card element
    # which discovers plants and areas at runtime — no listeners needed.

    # Helper to get page_id from entity, page_id, or plant_name
    def _get_page_id_from_call(call: ServiceCall) -> str | None:
        """Extract page_id from service call data."""
        # Priority: entity_id > page_id > plant_name
        entity_id = call.data.get(ATTR_ENTITY_ID)
        if entity_id:
            state = hass.states.get(entity_id)
            if state and state.attributes.get("page_id"):
                return state.attributes.get("page_id")
            _LOGGER.error("Entity '%s' not found or has no page_id", entity_id)
            return None

        page_id = call.data.get(ATTR_PAGE_ID)
        if page_id:
            return page_id

        return None

    # ── Shared bulk helper ────────────────────────────────────────────────────
    async def _handle_bulk_or_single(
        call: ServiceCall, notion_property: str
    ) -> None:
        """Update a date property for one plant or all plants in a HA area."""
        area_id = call.data.get(ATTR_AREA_ID)
        if area_id:
            page_ids = await _find_pages_by_area(hass, area_id)
            if not page_ids:
                _LOGGER.warning(
                    "No plant sensors found in HA area '%s'", area_id
                )
                return
            await asyncio.gather(*[
                _update_date_property(
                    hass, entry.entry_id, pid, notion_property, call.data.get(ATTR_DATE)
                )
                for pid in page_ids
            ])
            return

        # Single-plant path (entity_id / page_id / plant_name)
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error(
                "Provide entity_id, page_id, plant_name, or area_id"
            )
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(
            hass, entry.entry_id, page_id, notion_property, call.data.get(ATTR_DATE)
        )

    # Register services
    async def handle_update_watered(call: ServiceCall) -> None:
        """Handle mark as watered service."""
        await _handle_bulk_or_single(call, "Last Watered")

    async def handle_update_fertilized(call: ServiceCall) -> None:
        """Handle mark as fertilized service."""
        await _handle_bulk_or_single(call, "Last Fertilized")

    async def handle_update_pruned(call: ServiceCall) -> None:
        """Handle mark as pruned service."""
        await _handle_bulk_or_single(call, "Last Pruned")

    async def handle_update_aerated(call: ServiceCall) -> None:
        """Handle mark as aerated service (for lawns)."""
        await _handle_bulk_or_single(call, "Last Aeration")

    async def handle_update_harvested(call: ServiceCall) -> None:
        """Handle mark as harvested service."""
        await _handle_bulk_or_single(call, "Last Harvested")

    async def handle_update_sanded(call: ServiceCall) -> None:
        """Handle mark as sanded service (for lawns)."""
        await _handle_bulk_or_single(call, "Last Sanded")

    async def handle_update_mowed(call: ServiceCall) -> None:
        """Handle mark as mowed service (for lawns)."""
        await _handle_bulk_or_single(call, "Last Mowed")

    async def handle_update_property(call: ServiceCall) -> None:
        """Handle generic property update service."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)
        property_name = call.data.get(ATTR_PROPERTY_NAME)
        property_value = call.data.get(ATTR_PROPERTY_VALUE)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_generic_property(hass, entry.entry_id, page_id, property_name, property_value)

    async def handle_refresh_data(call: ServiceCall) -> None:
        """Handle refresh database service."""
        # Get the coordinator and trigger a refresh
        coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()
            _LOGGER.info("Database refresh requested")
        else:
            _LOGGER.error("Coordinator not found for refresh")

    async def handle_add_plant(call: ServiceCall) -> None:
        """Handle add plant service using AI."""
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not plant_name:
            _LOGGER.error("Plant name is required")
            return

        # Check for duplicate - see if plant with this name already exists
        existing_page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
        if existing_page_id:
            _LOGGER.warning("Plant '%s' already exists in the database, skipping creation", plant_name)
            return

        # Get the conversation agent from options
        agent_id = entry.options.get(CONF_CONVERSATION_AGENT)
        if not agent_id:
            _LOGGER.error("No conversation agent configured. Please configure one in the integration options.")
            return

        # Build location context from HA system settings
        lat = hass.config.latitude
        lon = hass.config.longitude
        elevation = hass.config.elevation
        country = hass.config.country or ""
        timezone = str(hass.config.time_zone) if hass.config.time_zone else ""
        location_name = hass.config.location_name or ""

        hemisphere = "Southern" if lat < 0 else "Northern"
        lat_str = f"{abs(lat):.4f}°{'S' if lat < 0 else 'N'}"
        lon_str = f"{abs(lon):.4f}°{'W' if lon < 0 else 'E'}"

        location_parts = [f"coordinates {lat_str}, {lon_str}"]
        if elevation is not None:
            location_parts.append(f"elevation {elevation}m")
        if country:
            location_parts.append(f"country {country}")
        if timezone:
            location_parts.append(f"timezone {timezone}")
        if location_name:
            location_parts.append(f"home location name \"{location_name}\"")

        location_detail = ", ".join(location_parts)

        prompt = f"""I need detailed plant care information for "{plant_name}".
The plant will be grown at: {location_detail}.
This location is in the {hemisphere} Hemisphere. Tailor ALL advice to these exact local conditions:
- Use the coordinates to determine the precise USDA hardiness zone
- Prune/harvest months must reflect the correct growing season for the {hemisphere} Hemisphere
- Watering intervals should reflect the local climate (arid, temperate, tropical, etc.)
- Elevation ({elevation}m) affects temperature ranges and growing conditions
- Set winterize=true only if the local climate requires it
Please respond ONLY with a valid JSON object (no markdown, no explanation) with these exact fields:
{{
    "name": "{plant_name}",
    "type": "Plant|Tree|Shrub|Vegetable|Herb|Lawn",
    "lifecycle": "Perennial|Annual|Biennial",
    "hardiness_zone": "1-13 (USDA hardiness zone number as string)",
    "soil_type": "Sandy|Loamy|Clay|Silty|Peaty|Chalky|Any",
    "soil_ph": "Acidic (pH < 6)|Neutral (pH 6-7)|Alkaline (pH > 7)|Any",
    "height": "expected mature height (e.g., '1-2m' or '30-60cm')",
    "growth_per_year": "annual growth rate description",
    "sun_exposure": "Full Sun|Partial Sun|Partial Shade|Full Shade",
    "water_interval_days": number (days between watering),
    "water_amount": "Low|Medium|High",
    "fertilize_interval_days": number (days between fertilizing),
    "fertilizer_type": "text description",
    "prune_months": ["Month1", "Month2"] (list of month names when pruning is needed, or empty array if not applicable),
    "prune_instructions": "text description",
    "prune_instructions_url": "URL to a helpful guide for pruning this plant (from a reputable gardening site)",
    "harvest_months": ["Month1", "Month2"] (list of month names, or empty array if not applicable),
    "harvest_notes": "text description or empty",
    "harvest_instructions_url": "URL to a helpful guide for harvesting this plant (from a reputable gardening site, or empty if not harvestable)",
    "companion_plants": "text listing good companion plants",
    "bad_companions": "text listing plants to avoid planting nearby",
    "bee_friendly": true|false,
    "toxicity": "Safe|Toxic to Pets|Toxic to Children|Toxic to Both",
    "winterize": true|false (whether plant needs winter protection),
    "care_instructions": "general care tips",
    "care_instructions_url": "URL to a comprehensive care guide for this plant (from a reputable gardening site)",
    "special_notes": "any special requirements"
}}
Respond ONLY with the JSON object, nothing else."""

        try:
            # Call the conversation agent
            _LOGGER.info("Calling conversation agent '%s' for plant '%s'", agent_id, plant_name)
            result = await conversation.async_converse(
                hass=hass,
                text=prompt,
                conversation_id=None,
                context=call.context,
                language="en",
                agent_id=agent_id,
            )

            # Get the response text
            _LOGGER.debug("Conversation result type: %s", type(result))
            _LOGGER.debug("Conversation result.response: %s", result.response)

            response_text = result.response.speech.get("plain", {}).get("speech", "")
            if not response_text:
                _LOGGER.error("No response from AI agent. Full result: %s", result)
                return

            _LOGGER.debug("AI Response (first 500 chars): %s", response_text[:500])

            # Parse JSON from response (handle potential markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                _LOGGER.error("Could not find JSON in AI response: %s", response_text)
                return

            _LOGGER.debug("Found JSON in response, parsing...")
            plant_data = json.loads(json_match.group())
            _LOGGER.info("Parsed plant data for '%s': type=%s, location=%s",
                        plant_name, plant_data.get("type"), plant_data.get("location"))

            # Create the plant in Notion
            _LOGGER.info("Creating plant '%s' in Notion database...", plant_name)
            await _create_plant_in_notion(hass, entry.entry_id, plant_data)

            _LOGGER.info("Successfully added plant '%s' using AI", plant_name)

            # Reload the integration to create the new sensor
            _LOGGER.info("Reloading integration to create sensor for '%s'...", plant_name)
            await hass.config_entries.async_reload(entry.entry_id)
            _LOGGER.info("Integration reloaded, sensor for '%s' should now be available", plant_name)

        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse AI response as JSON: %s", err, exc_info=True)
        except Exception as err:
            _LOGGER.error("Failed to add plant '%s': %s", plant_name, err, exc_info=True)

    async def handle_delete_plant(call: ServiceCall) -> None:
        """Handle delete plant service — archives the Notion page and removes the HA sensor."""
        from homeassistant.helpers import entity_registry as er

        # Retain entity_id before resolving page_id (we need both)
        entity_id_from_call = call.data.get(ATTR_ENTITY_ID)
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error(
                "notion_garden_care.delete_plant requires entity_id, page_id, or plant_name"
            )
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found in Notion database", plant_name)
                return

        # Resolve entity_id from page_id if not already known
        entity_id_to_remove = entity_id_from_call
        if not entity_id_to_remove and page_id:
            for eid, state in hass.states.items():
                if (eid.startswith("sensor.garden_care_") and
                        state.attributes.get("page_id") == page_id):
                    entity_id_to_remove = eid
                    break

        notion = hass.data[DOMAIN][entry.entry_id]["notion"]

        try:
            await hass.async_add_executor_job(
                lambda: notion.pages.update(page_id=page_id, archived=True)
            )
            _LOGGER.info("Plant page %s archived in Notion", page_id)

            # Remove the sensor entity from HA immediately
            if entity_id_to_remove:
                registry = er.async_get(hass)
                if registry.async_get(entity_id_to_remove):
                    registry.async_remove(entity_id_to_remove)
                    _LOGGER.info("Removed HA entity %s", entity_id_to_remove)
                else:
                    _LOGGER.warning("Entity %s not found in registry", entity_id_to_remove)
            else:
                _LOGGER.warning("Could not determine entity_id for page %s; entity not removed from HA", page_id)

            # Refresh coordinator so the cache no longer contains this plant
            coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
            if coordinator:
                await coordinator.async_request_refresh()

        except APIResponseError as err:
            _LOGGER.error("Failed to delete plant page %s: %s", page_id, err)

    # Register all services
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_WATERED, handle_update_watered, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_FERTILIZED, handle_update_fertilized, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_PRUNED, handle_update_pruned, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_AERATED, handle_update_aerated, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_HARVESTED, handle_update_harvested, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_SANDED, handle_update_sanded, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_MOWED, handle_update_mowed, schema=UPDATE_SERVICE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_PROPERTY, handle_update_property, schema=UPDATE_PROPERTY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_DATA, handle_refresh_data
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_PLANT, handle_add_plant, schema=ADD_PLANT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_PLANT, handle_delete_plant, schema=DELETE_PLANT_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        # Reset so the dashboard is re-validated on the next setup (e.g. after reload)
        hass.data[DOMAIN].pop("dashboard_created", None)

    # Unregister services if this is the last entry
    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_WATERED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_FERTILIZED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PRUNED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_AERATED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_HARVESTED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SANDED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_MOWED)
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PROPERTY)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)
        hass.services.async_remove(DOMAIN, SERVICE_ADD_PLANT)
        hass.services.async_remove(DOMAIN, SERVICE_DELETE_PLANT)

    return unload_ok


async def _find_page_by_name(hass: HomeAssistant, entry_id: str, plant_name: str) -> str | None:
    """Find page ID by plant name."""
    database_id = hass.data[DOMAIN][entry_id]["database_id"]

    # Get the token from config entry
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id:
            notion_token = entry.data.get("notion_token")
            break
    else:
        _LOGGER.error("Could not find config entry for entry_id: %s", entry_id)
        return None

    def _query_by_name():
        """Query Notion database for plant by name."""
        import httpx
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        payload = {
            "filter": {
                "property": "Name",
                "title": {
                    "equals": plant_name
                }
            }
        }
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()

    try:
        response = await hass.async_add_executor_job(_query_by_name)
        results = response.get("results", [])
        if results:
            return results[0]["id"]

    except Exception as err:
        _LOGGER.error("Failed to find plant: %s", err)

    return None


async def _update_date_property(
    hass: HomeAssistant,
    entry_id: str,
    page_id: str,
    property_name: str,
    date_value: str | None = None
) -> None:
    """Update a date property in Notion."""
    notion = hass.data[DOMAIN][entry_id]["notion"]

    # Use provided date or default to today
    if date_value:
        date_to_set = date_value
    else:
        date_to_set = datetime.now().strftime("%Y-%m-%d")

    try:
        await hass.async_add_executor_job(
            lambda: notion.pages.update(
                page_id=page_id,
                properties={
                    property_name: {
                        "date": {
                            "start": date_to_set
                        }
                    }
                }
            )
        )
        _LOGGER.info("Updated %s to %s for page %s", property_name, date_to_set, page_id)

        # Trigger sensor refresh
        coordinator = hass.data[DOMAIN][entry_id].get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()

    except APIResponseError as err:
        _LOGGER.error("Failed to update property: %s", err)


async def _update_generic_property(
    hass: HomeAssistant,
    entry_id: str,
    page_id: str,
    property_name: str,
    property_value: str | int | float | bool | list
) -> None:
    """Update any property in Notion based on value type."""
    notion = hass.data[DOMAIN][entry_id]["notion"]

    # Determine property format based on value type
    if isinstance(property_value, bool):
        property_data = {"checkbox": property_value}
    elif isinstance(property_value, (int, float)) and not isinstance(property_value, bool):
        property_data = {"number": property_value}
    elif isinstance(property_value, list):
        # Assume it's a multi-select
        property_data = {"multi_select": [{"name": str(v)} for v in property_value]}
    elif isinstance(property_value, str):
        # Check for boolean strings first
        if property_value.lower() in ("true", "false", "yes", "no", "1", "0"):
            bool_val = property_value.lower() in ("true", "yes", "1")
            property_data = {"checkbox": bool_val}
        # Try to detect if it's a number
        elif property_value.replace(".", "", 1).replace("-", "", 1).isdigit():
            if "." in property_value:
                property_data = {"number": float(property_value)}
            else:
                property_data = {"number": int(property_value)}
        # Try to detect if it's a date (YYYY-MM-DD format)
        elif len(property_value) == 10 and property_value[4] == "-" and property_value[7] == "-":
            property_data = {"date": {"start": property_value}}
        else:
            # Assume it's rich_text
            property_data = {"rich_text": [{"text": {"content": property_value}}]}
    else:
        property_data = {"rich_text": [{"text": {"content": str(property_value)}}]}

    try:
        await hass.async_add_executor_job(
            lambda: notion.pages.update(
                page_id=page_id,
                properties={
                    property_name: property_data
                }
            )
        )
        _LOGGER.info("Updated %s to %s for page %s", property_name, property_value, page_id)

        # Trigger sensor refresh
        coordinator = hass.data[DOMAIN][entry_id].get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()

    except APIResponseError as err:
        _LOGGER.error("Failed to update property %s: %s", property_name, err)


async def _create_plant_in_notion(
    hass: HomeAssistant,
    entry_id: str,
    plant_data: dict
) -> None:
    """Create a new plant in Notion from AI-generated data."""
    notion = hass.data[DOMAIN][entry_id]["notion"]
    database_id = hass.data[DOMAIN][entry_id]["database_id"]

    # Build properties dict for Notion
    properties = {
        "Name": {"title": [{"text": {"content": plant_data.get("name", "Unknown Plant")}}]},
        "Active": {"checkbox": True},
    }

    # Type (select)
    if plant_data.get("type"):
        properties["Type"] = {"select": {"name": plant_data["type"]}}

    # Sun Exposure (select)
    if plant_data.get("sun_exposure"):
        properties["Sun Exposure"] = {"select": {"name": plant_data["sun_exposure"]}}

    # Water Interval (number)
    if plant_data.get("water_interval_days"):
        properties["Water Interval (days)"] = {"number": int(plant_data["water_interval_days"])}

    # Water Amount (select)
    if plant_data.get("water_amount"):
        properties["Water Amount"] = {"select": {"name": plant_data["water_amount"]}}

    # Fertilize Interval (number)
    if plant_data.get("fertilize_interval_days"):
        properties["Fertilize Interval (days)"] = {"number": int(plant_data["fertilize_interval_days"])}

    # Fertilizer Type (rich_text)
    if plant_data.get("fertilizer_type"):
        properties["Fertilizer Type"] = {"rich_text": [{"text": {"content": plant_data["fertilizer_type"]}}]}

    # Prune Months (multi_select)
    if plant_data.get("prune_months") and isinstance(plant_data["prune_months"], list):
        properties["Prune Months"] = {"multi_select": [{"name": m} for m in plant_data["prune_months"]]}

    # Prune Instructions (rich_text)
    if plant_data.get("prune_instructions"):
        properties["Prune Instructions"] = {"rich_text": [{"text": {"content": plant_data["prune_instructions"]}}]}

    # Harvest Months (multi_select)
    if plant_data.get("harvest_months") and isinstance(plant_data["harvest_months"], list):
        properties["Harvest Months"] = {"multi_select": [{"name": m} for m in plant_data["harvest_months"]]}

    # Harvest Notes (rich_text)
    if plant_data.get("harvest_notes"):
        properties["Harvest Notes"] = {"rich_text": [{"text": {"content": plant_data["harvest_notes"]}}]}

    # Companion Plants (rich_text)
    if plant_data.get("companion_plants"):
        properties["Companion Plants"] = {"rich_text": [{"text": {"content": plant_data["companion_plants"]}}]}

    # Bee Friendly (checkbox)
    if "bee_friendly" in plant_data:
        properties["Bee Friendly"] = {"checkbox": bool(plant_data["bee_friendly"])}

    # Toxicity (select)
    if plant_data.get("toxicity"):
        properties["Toxicity"] = {"select": {"name": plant_data["toxicity"]}}

    # Care Instructions (rich_text)
    if plant_data.get("care_instructions"):
        properties["Care Instructions"] = {"rich_text": [{"text": {"content": plant_data["care_instructions"]}}]}

    # Special Notes (rich_text)
    if plant_data.get("special_notes"):
        properties["Special Notes"] = {"rich_text": [{"text": {"content": plant_data["special_notes"]}}]}

    # Lifecycle (select)
    if plant_data.get("lifecycle"):
        properties["Lifecycle"] = {"select": {"name": plant_data["lifecycle"]}}

    # Hardiness Zone (select)
    if plant_data.get("hardiness_zone"):
        properties["Hardiness Zone"] = {"select": {"name": str(plant_data["hardiness_zone"])}}

    # Soil Type (select)
    if plant_data.get("soil_type"):
        properties["Soil Type"] = {"select": {"name": plant_data["soil_type"]}}

    # Soil pH (select)
    if plant_data.get("soil_ph"):
        properties["Soil pH"] = {"select": {"name": plant_data["soil_ph"]}}

    # Height (rich_text)
    if plant_data.get("height"):
        properties["Height"] = {"rich_text": [{"text": {"content": plant_data["height"]}}]}

    # Growth per Year (rich_text)
    if plant_data.get("growth_per_year"):
        properties["Growth per Year"] = {"rich_text": [{"text": {"content": plant_data["growth_per_year"]}}]}

    # Bad Companions (rich_text)
    if plant_data.get("bad_companions"):
        properties["Bad Companions"] = {"rich_text": [{"text": {"content": plant_data["bad_companions"]}}]}

    # Winterize (checkbox)
    if "winterize" in plant_data:
        properties["Winterize"] = {"checkbox": bool(plant_data["winterize"])}

    # URL properties - these may not exist in older databases, so we'll add them separately
    url_properties = {}
    if plant_data.get("care_instructions_url"):
        url_properties["Care Instructions URL"] = {"url": plant_data["care_instructions_url"]}
    if plant_data.get("prune_instructions_url"):
        url_properties["Prune Instructions URL"] = {"url": plant_data["prune_instructions_url"]}
    if plant_data.get("harvest_instructions_url"):
        url_properties["Harvest Instructions URL"] = {"url": plant_data["harvest_instructions_url"]}

    # Try to create with all properties including URLs
    all_properties = {**properties, **url_properties}

    try:
        await hass.async_add_executor_job(
            lambda: notion.pages.create(
                parent={"database_id": database_id},
                properties=all_properties
            )
        )
        _LOGGER.info("Created plant '%s' in Notion", plant_data.get("name"))

    except APIResponseError as err:
        # If it failed and we had URL properties, try again without them
        # (older databases may not have URL columns)
        if url_properties and "property" in str(err).lower():
            _LOGGER.warning(
                "Failed to create plant with URL properties, retrying without URLs: %s", err
            )
            try:
                await hass.async_add_executor_job(
                    lambda: notion.pages.create(
                        parent={"database_id": database_id},
                        properties=properties
                    )
                )
                _LOGGER.info(
                    "Created plant '%s' in Notion (without URL properties - "
                    "add URL columns to your database to enable this feature)",
                    plant_data.get("name")
                )
                return
            except APIResponseError as retry_err:
                _LOGGER.error("Failed to create plant in Notion: %s", retry_err)
                raise
        else:
            _LOGGER.error("Failed to create plant in Notion: %s", err)
            raise
