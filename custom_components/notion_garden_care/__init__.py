"""The Notion Garden Care integration."""
from __future__ import annotations

import logging
from datetime import datetime

from notion_client import Client
from notion_client.errors import APIResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_NOTION_TOKEN,
    CONF_DATABASE_ID,
    SERVICE_UPDATE_WATERED,
    SERVICE_UPDATE_FERTILIZED,
    SERVICE_UPDATE_PRUNED,
    SERVICE_UPDATE_AERATED,
    SERVICE_UPDATE_HARVESTED,
    SERVICE_UPDATE_PROPERTY,
    SERVICE_REFRESH_DATA,
    ATTR_PAGE_ID,
    ATTR_PLANT_NAME,
    ATTR_PROPERTY_NAME,
    ATTR_PROPERTY_VALUE,
    ATTR_DATE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

UPDATE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
        vol.Optional(ATTR_DATE): cv.string,
    }
)

UPDATE_PROPERTY_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_PAGE_ID): cv.string,
        vol.Optional(ATTR_PLANT_NAME): cv.string,
        vol.Required(ATTR_PROPERTY_NAME): cv.string,
        vol.Required(ATTR_PROPERTY_VALUE): vol.Any(str, int, float, bool, list),
    }
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

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_update_watered(call: ServiceCall) -> None:
        """Handle mark as watered service."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
            # Find page ID by plant name
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Watered", call.data.get(ATTR_DATE))

    async def handle_update_fertilized(call: ServiceCall) -> None:
        """Handle mark as fertilized service."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Fertilized", call.data.get(ATTR_DATE))

    async def handle_update_pruned(call: ServiceCall) -> None:
        """Handle mark as pruned service."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Pruned", call.data.get(ATTR_DATE))

    async def handle_update_aerated(call: ServiceCall) -> None:
        """Handle mark as aerated service (for lawns)."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Aeration", call.data.get(ATTR_DATE))

    async def handle_update_harvested(call: ServiceCall) -> None:
        """Handle mark as harvested service."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
            page_id = await _find_page_by_name(hass, entry.entry_id, plant_name)
            if not page_id:
                _LOGGER.error("Plant '%s' not found", plant_name)
                return

        await _update_date_property(hass, entry.entry_id, page_id, "Last Harvested", call.data.get(ATTR_DATE))

    async def handle_update_property(call: ServiceCall) -> None:
        """Handle generic property update service."""
        page_id = call.data.get(ATTR_PAGE_ID)
        plant_name = call.data.get(ATTR_PLANT_NAME)
        property_name = call.data.get(ATTR_PROPERTY_NAME)
        property_value = call.data.get(ATTR_PROPERTY_VALUE)

        if not page_id and not plant_name:
            _LOGGER.error("Either page_id or plant_name must be provided")
            return

        if plant_name:
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
        DOMAIN, SERVICE_UPDATE_PROPERTY, handle_update_property, schema=UPDATE_PROPERTY_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH_DATA, handle_refresh_data
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
        hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PROPERTY)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_DATA)

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
            notion.pages.update,
            page_id,
            {
                "properties": {
                    property_name: {
                        "date": {
                            "start": date_to_set
                        }
                    }
                }
            }
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
    elif isinstance(property_value, (int, float)):
        property_data = {"number": property_value}
    elif isinstance(property_value, list):
        # Assume it's a multi-select
        property_data = {"multi_select": [{"name": str(v)} for v in property_value]}
    elif isinstance(property_value, str):
        # Try to detect if it's a date (YYYY-MM-DD format)
        if len(property_value) == 10 and property_value[4] == "-" and property_value[7] == "-":
            property_data = {"date": {"start": property_value}}
        else:
            # Assume it's rich_text
            property_data = {"rich_text": [{"text": {"content": property_value}}]}
    else:
        property_data = {"rich_text": [{"text": {"content": str(property_value)}}]}

    try:
        await hass.async_add_executor_job(
            notion.pages.update,
            page_id,
            {
                "properties": {
                    property_name: property_data
                }
            }
        )
        _LOGGER.info("Updated %s to %s for page %s", property_name, property_value, page_id)

        # Trigger sensor refresh
        coordinator = hass.data[DOMAIN][entry_id].get("coordinator")
        if coordinator:
            await coordinator.async_request_refresh()

    except APIResponseError as err:
        _LOGGER.error("Failed to update property %s: %s", property_name, err)
