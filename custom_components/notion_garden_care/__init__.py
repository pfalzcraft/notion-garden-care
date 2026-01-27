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
    SERVICE_UPDATE_PROPERTY,
    SERVICE_REFRESH_DATA,
    SERVICE_ADD_PLANT,
    ATTR_PAGE_ID,
    ATTR_PLANT_NAME,
    ATTR_PROPERTY_NAME,
    ATTR_PROPERTY_VALUE,
    ATTR_DATE,
    ATTR_ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
URL_BASE = "/notion-garden-care"
FRONTEND_VERSION = "1.3.0"

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

    # List files in frontend directory for debugging
    try:
        files = list(frontend_path.iterdir())
        _LOGGER.info("Frontend files: %s", [f.name for f in files])
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

    # Add JS files to frontend so they load automatically
    card_url = f"{URL_BASE}/plant-care-card.js"
    strategy_url = f"{URL_BASE}/garden-care-strategy.js"

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
    """Create the Garden Care dashboard if it doesn't exist."""
    if hass.data[DOMAIN].get("dashboard_created"):
        return

    try:
        # Use the lovelace/dashboards/create WebSocket API via hass.services
        from homeassistant.components.lovelace import DOMAIN as LOVELACE_DOMAIN
        from homeassistant.components.lovelace.const import MODE_STORAGE

        # Check if dashboard already exists in storage
        lovelace_data = hass.data.get(LOVELACE_DOMAIN, {})
        dashboards = lovelace_data.get("dashboards", {})

        if "garden-care" in dashboards:
            _LOGGER.debug("Garden Care dashboard already exists")
            hass.data[DOMAIN]["dashboard_created"] = True
            return

        # Try to create dashboard via websocket command
        from homeassistant.components.lovelace.dashboard import LovelaceStorage
        from homeassistant.components.lovelace import dashboard

        # Create dashboard config
        config_data = {
            "url_path": "garden-care",
            "mode": MODE_STORAGE,
            "title": "Garden Care",
            "icon": "mdi:flower",
            "show_in_sidebar": True,
            "require_admin": False,
        }

        # Access the dashboards collection
        if hasattr(lovelace_data, "dashboards") and hasattr(lovelace_data.dashboards, "async_create_item"):
            await lovelace_data.dashboards.async_create_item(config_data)
            _LOGGER.info("Created Garden Care dashboard via collection")
        else:
            # Fallback: Write dashboard config to .storage
            storage_path = hass.config.path(".storage/lovelace_dashboards")
            import json
            import os

            # Read existing dashboards
            dashboards_data = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}
            if os.path.exists(storage_path):
                with open(storage_path, "r") as f:
                    dashboards_data = json.load(f)

            # Check if already exists
            items = dashboards_data.get("data", {}).get("items", [])
            if not any(item.get("url_path") == "garden-care" for item in items):
                items.append({
                    "id": "garden_care",
                    "url_path": "garden-care",
                    "mode": "storage",
                    "title": "Garden Care",
                    "icon": "mdi:flower",
                    "show_in_sidebar": True,
                    "require_admin": False,
                })
                dashboards_data["data"]["items"] = items

                with open(storage_path, "w") as f:
                    json.dump(dashboards_data, f, indent=2)
                _LOGGER.info("Created Garden Care dashboard in storage")

                # Also create the dashboard config with strategy
                dashboard_config_path = hass.config.path(".storage/lovelace.garden-care")
                dashboard_config = {
                    "version": 1,
                    "minor_version": 1,
                    "key": "lovelace.garden-care",
                    "data": {
                        "config": {
                            "strategy": {
                                "type": "custom:garden-care"
                            }
                        }
                    }
                }
                with open(dashboard_config_path, "w") as f:
                    json.dump(dashboard_config, f, indent=2)
                _LOGGER.info("Created Garden Care dashboard strategy config")

        hass.data[DOMAIN]["dashboard_created"] = True

    except Exception as err:
        _LOGGER.warning("Could not auto-create dashboard: %s", err)
        _LOGGER.info(
            "To create the Garden Care dashboard manually:\n"
            "1. Go to Settings -> Dashboards -> Add Dashboard\n"
            "2. Edit the dashboard and use Raw Configuration Editor\n"
            "3. Set: strategy:\n         type: custom:garden-care"
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notion Garden Care from a config entry."""
    notion_token = entry.data[CONF_NOTION_TOKEN]
    database_id = entry.data[CONF_DATABASE_ID]

    # Create Notion client
    notion = Client(auth=notion_token)

    # Test connection
    try:
        await hass.async_add_executor_job(
            notion.databases.retrieve,
            database_id
        )
    except APIResponseError as err:
        _LOGGER.error("Failed to connect to Notion: %s", err)
        raise ConfigEntryNotReady from err

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
    "location": "Garden|Balcony|Terrace|Conservatory|Indoor",
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
    "prune_months": ["Month1", "Month2"] (list of month names when pruning is needed),
    "prune_instructions": "text description",
    "harvest_months": ["Month1", "Month2"] (list of month names, or empty if not applicable),
    "harvest_notes": "text description or empty",
    "companion_plants": "text listing good companion plants",
    "bad_companions": "text listing plants to avoid planting nearby",
    "bee_friendly": true|false,
    "toxicity": "Safe|Toxic to Pets|Toxic to Children|Toxic to Both",
    "winterize": true|false (whether plant needs winter protection),
    "care_instructions": "general care tips",
    "special_notes": "any special requirements"
}}
Respond ONLY with the JSON object, nothing else."""

        try:
            # Call the conversation agent
            result = await conversation.async_converse(
                hass=hass,
                text=prompt,
                conversation_id=None,
                context=call.context,
                language="en",
                agent_id=agent_id,
            )

            # Get the response text
            response_text = result.response.speech.get("plain", {}).get("speech", "")
            if not response_text:
                _LOGGER.error("No response from AI agent")
                return

            _LOGGER.debug("AI Response: %s", response_text)

            # Parse JSON from response (handle potential markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                _LOGGER.error("Could not find JSON in AI response: %s", response_text)
                return

            plant_data = json.loads(json_match.group())

            # Create the plant in Notion
            await _create_plant_in_notion(hass, entry.entry_id, plant_data)

            _LOGGER.info("Successfully added plant '%s' using AI", plant_name)

            # Reload the integration to create the new sensor
            await hass.config_entries.async_reload(entry.entry_id)
            _LOGGER.info("Integration reloaded to create sensor for '%s'", plant_name)

        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse AI response as JSON: %s", err)
        except Exception as err:
            _LOGGER.error("Failed to add plant: %s", err)

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
        DOMAIN, SERVICE_UPDATE_PROPERTY, handle_update_property, schema=UPDATE_PROPERTY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_DATA, handle_refresh_data
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_PLANT, handle_add_plant, schema=ADD_PLANT_SCHEMA
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
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PROPERTY)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)
        hass.services.async_remove(DOMAIN, SERVICE_ADD_PLANT)

    return unload_ok


async def _find_page_by_name(hass: HomeAssistant, entry_id: str, plant_name: str) -> str | None:
    """Find page ID by plant name."""
    notion = hass.data[DOMAIN][entry_id]["notion"]
    database_id = hass.data[DOMAIN][entry_id]["database_id"]

    try:
        response = await hass.async_add_executor_job(
            notion.databases.query,
            database_id,
            {
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": plant_name
                    }
                }
            }
        )

        results = response.get("results", [])
        if results:
            return results[0]["id"]

    except APIResponseError as err:
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

    # Location (select)
    if plant_data.get("location"):
        properties["Location"] = {"select": {"name": plant_data["location"]}}

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

    try:
        await hass.async_add_executor_job(
            lambda: notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
        )
        _LOGGER.info("Created plant '%s' in Notion", plant_data.get("name"))

    except APIResponseError as err:
        _LOGGER.error("Failed to create plant in Notion: %s", err)
        raise
