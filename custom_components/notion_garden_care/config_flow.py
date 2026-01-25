"""Config flow for Notion Garden Care integration."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta

import voluptuous as vol
from notion_client import Client
from notion_client.errors import APIResponseError

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_NOTION_TOKEN,
    CONF_PARENT_PAGE_ID,
    CONF_DATABASE_ID,
    CONF_CREATE_DATABASE,
    CONF_ADD_EXAMPLES,
    NOTION_API_VERSION,
    PLANT_TYPES,
    LOCATIONS,
    WATER_AMOUNTS,
    SUN_EXPOSURE,
    TOXICITY,
    MONTHS,
    EXAMPLE_PLANTS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NOTION_TOKEN): str,
    }
)

STEP_PARENT_PAGE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PARENT_PAGE_ID): str,
        vol.Optional(CONF_CREATE_DATABASE, default=True): bool,
        vol.Optional(CONF_ADD_EXAMPLES, default=True): bool,
    }
)

STEP_DATABASE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DATABASE_ID): str,
    }
)


async def validate_token(hass: HomeAssistant, token: str) -> dict[str, str]:
    """Validate the Notion API token."""
    try:
        notion = Client(auth=token)
        # Test the token by searching for pages
        await hass.async_add_executor_job(
            notion.search,
            {"page_size": 1}
        )
        return {"title": "Notion Garden Care"}
    except APIResponseError as err:
        if err.status == 401:
            raise InvalidAuth
        raise CannotConnect


async def find_pages(hass: HomeAssistant, token: str) -> list[dict]:
    """Find available pages in Notion workspace."""
    try:
        notion = Client(auth=token)
        response = await hass.async_add_executor_job(
            notion.search,
            {"filter": {"property": "object", "value": "page"}, "page_size": 10}
        )
        return response.get("results", [])
    except APIResponseError:
        return []


async def create_database(
    hass: HomeAssistant,
    token: str,
    parent_page_id: str,
    add_examples: bool = True
) -> str:
    """Create the Garden Care database in Notion."""
    notion = Client(auth=token)

    try:
        # Create database
        database = await hass.async_add_executor_job(
            _create_database_sync,
            notion,
            parent_page_id
        )

        database_id = database["id"]

        # Add example plants if requested
        if add_examples:
            await hass.async_add_executor_job(
                _add_example_plants,
                notion,
                database_id
            )

        return database_id

    except APIResponseError as err:
        _LOGGER.error("Failed to create database: %s", err)
        raise CannotConnect


def _create_database_sync(notion: Client, parent_page_id: str) -> dict:
    """Synchronously create the database."""
    return notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Garden Care"}}],
        properties={
            "Name": {"title": {}},
            "Type": {
                "select": {
                    "options": [{"name": t, "color": c} for t, c in zip(
                        PLANT_TYPES,
                        ["green", "brown", "yellow", "orange", "pink", "green"]
                    )]
                }
            },
            "Location": {
                "select": {
                    "options": [{"name": l, "color": c} for l, c in zip(
                        LOCATIONS,
                        ["green", "blue", "purple", "yellow", "gray"]
                    )]
                }
            },
            "Active": {"checkbox": {}},
            "Fertilize Interval (days)": {"number": {"format": "number"}},
            "Last Fertilized": {"date": {}},
            "Next Fertilize": {
                "formula": {
                    "expression": 'dateAdd(prop("Last Fertilized"), prop("Fertilize Interval (days)"), "days")'
                }
            },
            "Fertilizer Type": {"rich_text": {}},
            "Water Interval (days)": {"number": {"format": "number"}},
            "Last Watered": {"date": {}},
            "Next Water": {
                "formula": {
                    "expression": 'dateAdd(prop("Last Watered"), prop("Water Interval (days)"), "days")'
                }
            },
            "Water Amount": {
                "select": {
                    "options": [{"name": w, "color": c} for w, c in zip(
                        WATER_AMOUNTS,
                        ["yellow", "blue", "blue"]
                    )]
                }
            },
            "Prune Months": {
                "multi_select": {
                    "options": [{"name": m, "color": _get_month_color(i)} for i, m in enumerate(MONTHS)]
                }
            },
            "Prune Instructions": {"rich_text": {}},
            "Last Pruned": {"date": {}},
            # Harvest & Growth
            "Harvest Months": {
                "multi_select": {
                    "options": [{"name": m, "color": _get_month_color(i)} for i, m in enumerate(MONTHS)]
                }
            },
            "Harvest Notes": {"rich_text": {}},
            "Sun Exposure": {
                "select": {
                    "options": [{"name": s, "color": c} for s, c in zip(
                        SUN_EXPOSURE,
                        ["yellow", "yellow", "blue", "gray"]
                    )]
                }
            },
            # Companion Planting & Safety
            "Companion Plants": {"rich_text": {}},
            "Bee Friendly": {"checkbox": {}},
            "Toxicity": {
                "select": {
                    "options": [{"name": t, "color": c} for t, c in zip(
                        TOXICITY,
                        ["green", "orange", "orange", "red"]
                    )]
                }
            },
            # Lawn Care (Aeration)
            "Aeration Interval (days)": {"number": {"format": "number"}},
            "Last Aeration": {"date": {}},
            "Next Aeration": {
                "formula": {
                    "expression": 'dateAdd(prop("Last Aeration"), prop("Aeration Interval (days)"), "days")'
                }
            },
            # General Care & Notes
            "Care Instructions": {"rich_text": {}},
            "Special Notes": {"rich_text": {}},
            "Notes": {"rich_text": {}}
        }
    )


def _get_month_color(month_index: int) -> str:
    """Get color for month based on season."""
    colors = [
        "gray", "gray", "green", "green", "green", "yellow",
        "yellow", "orange", "orange", "brown", "brown", "gray"
    ]
    return colors[month_index]


def _add_example_plants(notion: Client, database_id: str) -> None:
    """Add example plants to the database."""
    for plant_data in EXAMPLE_PLANTS:
        try:
            # Calculate dates
            now = datetime.now()
            last_fertilized = now - timedelta(days=plant_data.get("Fertilize Interval (days)", 30) - 5)
            last_watered = now - timedelta(days=plant_data.get("Water Interval (days)", 7) - 1)

            properties = {
                "Name": {
                    "title": [{"text": {"content": plant_data["Name"]}}]
                },
                "Type": {"select": {"name": plant_data["Type"]}},
                "Location": {"select": {"name": plant_data["Location"]}},
                "Active": {"checkbox": plant_data["Active"]},
                "Fertilize Interval (days)": {"number": plant_data["Fertilize Interval (days)"]},
                "Last Fertilized": {"date": {"start": last_fertilized.strftime("%Y-%m-%d")}},
                "Fertilizer Type": {
                    "rich_text": [{"text": {"content": plant_data["Fertilizer Type"]}}]
                },
                "Water Interval (days)": {"number": plant_data["Water Interval (days)"]},
                "Last Watered": {"date": {"start": last_watered.strftime("%Y-%m-%d")}},
                "Water Amount": {"select": {"name": plant_data["Water Amount"]}},
            }

            # Add prune months if present
            if "Prune Months" in plant_data:
                properties["Prune Months"] = {
                    "multi_select": [{"name": month} for month in plant_data["Prune Months"]]
                }

            # Add prune instructions if present
            if "Prune Instructions" in plant_data:
                properties["Prune Instructions"] = {
                    "rich_text": [{"text": {"content": plant_data["Prune Instructions"]}}]
                }

            # Add sun exposure if present
            if "Sun Exposure" in plant_data:
                properties["Sun Exposure"] = {"select": {"name": plant_data["Sun Exposure"]}}

            # Add harvest months if present
            if "Harvest Months" in plant_data:
                properties["Harvest Months"] = {
                    "multi_select": [{"name": month} for month in plant_data["Harvest Months"]]
                }

            # Add harvest notes if present
            if "Harvest Notes" in plant_data:
                properties["Harvest Notes"] = {
                    "rich_text": [{"text": {"content": plant_data["Harvest Notes"]}}]
                }

            # Add companion plants if present
            if "Companion Plants" in plant_data:
                properties["Companion Plants"] = {
                    "rich_text": [{"text": {"content": plant_data["Companion Plants"]}}]
                }

            # Add bee friendly if present
            if "Bee Friendly" in plant_data:
                properties["Bee Friendly"] = {"checkbox": plant_data["Bee Friendly"]}

            # Add toxicity if present
            if "Toxicity" in plant_data:
                properties["Toxicity"] = {"select": {"name": plant_data["Toxicity"]}}

            # Add aeration for lawns
            if "Aeration Interval (days)" in plant_data:
                properties["Aeration Interval (days)"] = {
                    "number": plant_data["Aeration Interval (days)"]
                }
                last_aeration = now - timedelta(days=300)
                properties["Last Aeration"] = {
                    "date": {"start": last_aeration.strftime("%Y-%m-%d")}
                }

            # Add care instructions
            if "Care Instructions" in plant_data:
                properties["Care Instructions"] = {
                    "rich_text": [{"text": {"content": plant_data["Care Instructions"]}}]
                }

            # Add special notes
            if "Special Notes" in plant_data:
                properties["Special Notes"] = {
                    "rich_text": [{"text": {"content": plant_data["Special Notes"]}}]
                }


            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
        except Exception as err:
            _LOGGER.warning("Failed to add example plant %s: %s", plant_data["Name"], err)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Notion Garden Care."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - Token input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_token(self.hass, user_input[CONF_NOTION_TOKEN])
                self.data[CONF_NOTION_TOKEN] = user_input[CONF_NOTION_TOKEN]
                return await self.async_step_parent_page()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "setup_url": "https://www.notion.so/my-integrations"
            }
        )

    async def async_step_parent_page(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle parent page selection or database creation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                parent_page_id = user_input[CONF_PARENT_PAGE_ID].strip()

                # Extract page ID from URL if provided
                if "notion.so/" in parent_page_id:
                    parts = parent_page_id.split("/")
                    for part in parts:
                        if len(part) >= 32:
                            parent_page_id = part.replace("-", "")[:32]
                            break

                self.data[CONF_PARENT_PAGE_ID] = parent_page_id

                if user_input.get(CONF_CREATE_DATABASE, True):
                    # Create database automatically
                    database_id = await create_database(
                        self.hass,
                        self.data[CONF_NOTION_TOKEN],
                        parent_page_id,
                        user_input.get(CONF_ADD_EXAMPLES, True)
                    )
                    self.data[CONF_DATABASE_ID] = database_id

                    return self.async_create_entry(
                        title="Notion Garden Care",
                        data=self.data
                    )
                else:
                    # Ask for existing database ID
                    return await self.async_step_database()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="parent_page",
            data_schema=STEP_PARENT_PAGE_SCHEMA,
            errors=errors,
            description_placeholders={
                "instruction": "Create a page in Notion, connect the integration, and paste the page URL here"
            }
        )

    async def async_step_database(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle existing database ID input."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                database_id = user_input[CONF_DATABASE_ID].strip()

                # Extract database ID from URL if provided
                if "notion.so/" in database_id:
                    parts = database_id.split("/")
                    for part in parts:
                        if "?" in part:
                            database_id = part.split("?")[0]
                        if len(part) >= 32:
                            database_id = part.replace("-", "")[:32]
                            break

                self.data[CONF_DATABASE_ID] = database_id

                return self.async_create_entry(
                    title="Notion Garden Care",
                    data=self.data
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="database",
            data_schema=STEP_DATABASE_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
