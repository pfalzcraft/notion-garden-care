"""The Notion Garden Care integration."""
from __future__ import annotations

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
    "Location": {"type": "rich_text", "rich_text": {}},
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
FRONTEND_VERSION = "1.8.2"

# This integration can only be set up via config entries
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

UPDATE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
        vol.Optional(ATTR_DATE): cv.string,
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

        # ── Step 2: retype properties whose type has changed ─────────────
        # Maps property name → expected config (without "type" key).
        # Only listed here when an existing property needs a type change.
        _PROPERTY_TYPE_CHANGES: dict = {
            "Location": {"rich_text": {}},  # was select, now free text
        }
        to_retype: dict = {
            name: new_spec
            for name, new_spec in _PROPERTY_TYPE_CHANGES.items()
            if name in db_props and db_props[name].get("type") != list(new_spec.keys())[0]
        }
        if to_retype:
            _LOGGER.info(
                "Retyping %d column(s) in Notion database: %s",
                len(to_retype), list(to_retype.keys()),
            )
            resp = httpx.patch(
                base_url,
                headers=headers,
                json={"properties": to_retype},
                timeout=30.0,
            )
            if resp.status_code >= 400:
                _LOGGER.error(
                    "Notion API rejected property type change (HTTP %s): %s. "
                    "Please manually change the 'Location' column type from "
                    "'Select' to 'Text' in your Notion database.",
                    resp.status_code, resp.text,
                )
            else:
                added.extend(to_retype.keys())

        # ── Step 3: compute missing properties ───────────────────────────
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

        # ── Step 4: add simple properties first ──────────────────────────
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

        # ── Step 5: add formula properties (dependencies now exist) ──────
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

    hass.data[DOMAIN]["frontend_loaded"] = True

    # Create the Garden Care dashboard automatically
    await _async_create_dashboard(hass)


async def _async_create_dashboard(hass: HomeAssistant) -> None:
    """Create the Garden Care dashboard automatically using HA's lovelace APIs."""
    if hass.data[DOMAIN].get("dashboard_created"):
        return

    hass.data[DOMAIN]["dashboard_created"] = True

    try:
        import os

        # Create the YAML config file for the dashboard
        yaml_config = """strategy:
  type: custom:garden-care
"""
        yaml_path = hass.config.path("garden-care.yaml")

        # Create or update the YAML file
        yaml_exists = await hass.async_add_executor_job(os.path.exists, yaml_path)
        if not yaml_exists:
            await hass.async_add_executor_job(_write_file, yaml_path, yaml_config)
            _LOGGER.info("Created garden-care.yaml dashboard config")

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


async def _create_dashboard_via_api(hass: HomeAssistant) -> bool:
    """Create the dashboard using Home Assistant's lovelace collection API."""
    import os

    dashboard_id = "garden-care"
    storage_path = hass.config.path(".storage/lovelace_dashboards")

    # First check if dashboard already exists in storage file
    def _check_existing():
        if not os.path.exists(storage_path):
            return False
        try:
            with open(storage_path, "r") as f:
                data = json.load(f)
            items = data.get("data", {}).get("items", [])
            return any(
                item.get("url_path") == dashboard_id or item.get("filename") == "garden-care.yaml"
                for item in items
            )
        except (json.JSONDecodeError, KeyError, IOError):
            return False

    if await hass.async_add_executor_job(_check_existing):
        _LOGGER.debug("Garden Care dashboard already exists in storage")
        return True

    # Try using HA's lovelace API first
    try:
        lovelace_data = hass.data.get("lovelace")
        if lovelace_data:
            # Use attribute access to avoid deprecation warning (HA 2026.2+)
            dashboards = getattr(lovelace_data, "dashboards", None)
            if dashboards is None and hasattr(lovelace_data, "get"):
                dashboards = lovelace_data.get("dashboards")

            if dashboards and hasattr(dashboards, "async_create_item"):
                # Check if already exists in collection
                exists = False
                if hasattr(dashboards, "data"):
                    for item in dashboards.data.values():
                        if item.get("url_path") == dashboard_id or item.get("filename") == "garden-care.yaml":
                            exists = True
                            break

                if not exists:
                    await dashboards.async_create_item({
                        "url_path": dashboard_id,
                        "mode": "yaml",
                        "filename": "garden-care.yaml",
                        "title": "Garden Care",
                        "icon": "mdi:flower",
                        "show_in_sidebar": True,
                        "require_admin": False,
                    })
                    _LOGGER.info("Successfully created Garden Care dashboard via HA API")
                    return True
                else:
                    _LOGGER.debug("Garden Care dashboard already exists in collection")
                    return True

    except Exception as err:
        _LOGGER.debug("Could not create dashboard via HA API: %s", err)

    # Fallback: Create/update the storage file directly
    try:
        def _create_storage_file():
            # Read existing data or create new structure
            if os.path.exists(storage_path):
                with open(storage_path, "r") as f:
                    data = json.load(f)
            else:
                data = {
                    "version": 1,
                    "minor_version": 1,
                    "key": "lovelace_dashboards",
                    "data": {"items": []}
                }

            items = data.get("data", {}).get("items", [])

            # Check if already exists
            for item in items:
                if item.get("url_path") == dashboard_id or item.get("filename") == "garden-care.yaml":
                    return True  # Already exists

            # Add new dashboard entry
            items.append({
                "id": dashboard_id.replace("-", "_"),
                "url_path": dashboard_id,
                "mode": "yaml",
                "filename": "garden-care.yaml",
                "title": "Garden Care",
                "icon": "mdi:flower",
                "show_in_sidebar": True,
                "require_admin": False,
            })

            data["data"]["items"] = items

            with open(storage_path, "w") as f:
                json.dump(data, f, indent=2)

            return True

        result = await hass.async_add_executor_job(_create_storage_file)
        if result:
            _LOGGER.info("Created Garden Care dashboard via storage file")
            return True

    except Exception as err:
        _LOGGER.warning("Could not create dashboard storage file: %s", err)

    return False


def _write_file(path: str, content: str) -> None:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)


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

    # Register frontend resources (custom card and dashboard strategy)
    await _async_register_frontend(hass)

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    # Register services
    async def handle_update_watered(call: ServiceCall) -> None:
        """Handle mark as watered service."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            # Find page ID by plant name
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Watered", call.data.get(ATTR_DATE))

    async def handle_update_fertilized(call: ServiceCall) -> None:
        """Handle mark as fertilized service."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Fertilized", call.data.get(ATTR_DATE))

    async def handle_update_pruned(call: ServiceCall) -> None:
        """Handle mark as pruned service."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Pruned", call.data.get(ATTR_DATE))

    async def handle_update_aerated(call: ServiceCall) -> None:
        """Handle mark as aerated service (for lawns)."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Aeration", call.data.get(ATTR_DATE))

    async def handle_update_harvested(call: ServiceCall) -> None:
        """Handle mark as harvested service."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Harvested", call.data.get(ATTR_DATE))

    async def handle_update_sanded(call: ServiceCall) -> None:
        """Handle mark as sanded service (for lawns)."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Sanded", call.data.get(ATTR_DATE))

    async def handle_update_mowed(call: ServiceCall) -> None:
        """Handle mark as mowed service (for lawns)."""
        page_id = _get_page_id_from_call(call)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either entity_id, page_id, or plant_name must be provided")
            return

        if not page_id and plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Mowed", call.data.get(ATTR_DATE))

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

        # Create prompt for AI
        prompt = f"""I need detailed plant care information for "{plant_name}".
Please respond ONLY with a valid JSON object (no markdown, no explanation) with these exact fields:
{{
    "name": "{plant_name}",
    "type": "Plant|Tree|Shrub|Vegetable|Herb|Lawn",
    "location": "free text description of where the plant is located (e.g. 'Back garden', 'South-facing balcony', 'Kitchen windowsill', 'Greenhouse')",
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
        """Handle delete plant service — archives the Notion page and removes the sensor."""
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

        notion = hass.data[DOMAIN][entry.entry_id]["notion"]

        try:
            await hass.async_add_executor_job(
                lambda: notion.pages.update(page_id=page_id, archived=True)
            )
            _LOGGER.info("Plant page %s archived (deleted) in Notion", page_id)

            # Reload the integration so the corresponding sensor is removed
            await hass.config_entries.async_reload(entry.entry_id)

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

    # Location (rich_text)
    if plant_data.get("location"):
        properties["Location"] = {"rich_text": [{"text": {"content": plant_data["location"]}}]}

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
