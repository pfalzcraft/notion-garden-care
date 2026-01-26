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

from homeassistant.helpers import entity_registry as er

from .const import (
    DOMAIN,
    CONF_NOTION_TOKEN,
    CONF_PARENT_PAGE_ID,
    CONF_DATABASE_ID,
    CONF_CREATE_DATABASE,
    CONF_ADD_EXAMPLES,
    CONF_CREATE_PLANT_SENSORS,
    CONF_CONVERSATION_AGENT,
    NOTION_API_VERSION,
    PLANT_TYPES,
    LOCATIONS,
    WATER_AMOUNTS,
    SUN_EXPOSURE,
    TOXICITY,
    LIFECYCLE,
    HARDINESS_ZONES,
    SOIL_TYPES,
    SOIL_PH,
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
        vol.Optional(CONF_CREATE_PLANT_SENSORS, default=True): bool,
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
            lambda: notion.search(page_size=1)
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
            lambda: notion.search(
                filter={"property": "object", "value": "page"},
                page_size=10
            )
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
    import asyncio
    notion = Client(auth=token)

    try:
        # Create database
        database = await hass.async_add_executor_job(
            _create_database_sync,
            notion,
            parent_page_id
        )

        database_id = database["id"]
        _LOGGER.info("Database created with ID: %s", database_id)
        _LOGGER.debug("Database properties: %s", database.get("properties", {}).keys())

        # Add example plants if requested
        if add_examples:
            # Wait a bit for Notion to fully process the database creation
            await asyncio.sleep(2)

            # Verify database exists and has properties before adding examples
            try:
                db_check = await hass.async_add_executor_job(
                    lambda: notion.databases.retrieve(database_id=database_id)
                )
                _LOGGER.info("Database verified. Properties: %s", list(db_check.get("properties", {}).keys()))
            except Exception as verify_err:
                _LOGGER.warning("Could not verify database: %s", verify_err)

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
    _LOGGER.info("Creating database with parent_page_id: %s", parent_page_id)

    result = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Garden Care"}}],
        initial_data_source={
            "properties": {
            "Name": {"type": "title", "title": {}},
            "Type": {
                "type": "select",
                "select": {
                    "options": [{"name": t, "color": c} for t, c in zip(
                        PLANT_TYPES,
                        ["green", "brown", "yellow", "orange", "pink", "green"]
                    )]
                }
            },
            "Location": {
                "type": "select",
                "select": {
                    "options": [{"name": l, "color": c} for l, c in zip(
                        LOCATIONS,
                        ["green", "blue", "purple", "yellow", "gray"]
                    )]
                }
            },
            "Active": {"type": "checkbox", "checkbox": {}},
            "Fertilize Interval (days)": {"type": "number", "number": {"format": "number"}},
            "Last Fertilized": {"type": "date", "date": {}},
            "Next Fertilize": {
                "type": "formula",
                "formula": {
                    "expression": 'dateAdd(prop("Last Fertilized"), prop("Fertilize Interval (days)"), "days")'
                }
            },
            "Fertilizer Type": {"type": "rich_text", "rich_text": {}},
            "Water Interval (days)": {"type": "number", "number": {"format": "number"}},
            "Last Watered": {"type": "date", "date": {}},
            "Next Water": {
                "type": "formula",
                "formula": {
                    "expression": 'dateAdd(prop("Last Watered"), prop("Water Interval (days)"), "days")'
                }
            },
            "Water Amount": {
                "type": "select",
                "select": {
                    "options": [{"name": w, "color": c} for w, c in zip(
                        WATER_AMOUNTS,
                        ["yellow", "blue", "blue"]
                    )]
                }
            },
            "Prune Months": {
                "type": "multi_select",
                "multi_select": {
                    "options": [{"name": m, "color": _get_month_color(i)} for i, m in enumerate(MONTHS)]
                }
            },
            "Prune Instructions": {"type": "rich_text", "rich_text": {}},
            "Last Pruned": {"type": "date", "date": {}},
            # Harvest & Growth
            "Harvest Months": {
                "type": "multi_select",
                "multi_select": {
                    "options": [{"name": m, "color": _get_month_color(i)} for i, m in enumerate(MONTHS)]
                }
            },
            "Harvest Notes": {"type": "rich_text", "rich_text": {}},
            "Last Harvested": {"type": "date", "date": {}},
            "Sun Exposure": {
                "type": "select",
                "select": {
                    "options": [{"name": s, "color": c} for s, c in zip(
                        SUN_EXPOSURE,
                        ["yellow", "yellow", "blue", "gray"]
                    )]
                }
            },
            # Companion Planting & Safety
            "Companion Plants": {"type": "rich_text", "rich_text": {}},
            "Bad Companions": {"type": "rich_text", "rich_text": {}},
            "Bee Friendly": {"type": "checkbox", "checkbox": {}},
            "Toxicity": {
                "type": "select",
                "select": {
                    "options": [{"name": t, "color": c} for t, c in zip(
                        TOXICITY,
                        ["green", "orange", "orange", "red"]
                    )]
                }
            },
            # Plant Characteristics
            "Lifecycle": {
                "type": "select",
                "select": {
                    "options": [{"name": l, "color": c} for l, c in zip(
                        LIFECYCLE,
                        ["green", "yellow", "blue"]
                    )]
                }
            },
            "Hardiness Zone": {
                "type": "select",
                "select": {
                    "options": [{"name": z, "color": "blue"} for z in HARDINESS_ZONES]
                }
            },
            "Soil Type": {
                "type": "select",
                "select": {
                    "options": [{"name": s, "color": c} for s, c in zip(
                        SOIL_TYPES,
                        ["yellow", "brown", "orange", "gray", "brown", "gray", "green"]
                    )]
                }
            },
            "Soil pH": {
                "type": "select",
                "select": {
                    "options": [{"name": p, "color": c} for p, c in zip(
                        SOIL_PH,
                        ["orange", "green", "blue", "gray"]
                    )]
                }
            },
            "Height": {"type": "rich_text", "rich_text": {}},
            "Growth per Year": {"type": "rich_text", "rich_text": {}},
            "Winterize": {"type": "checkbox", "checkbox": {}},
            # Lawn Care (Aeration)
            "Aeration Interval (days)": {"type": "number", "number": {"format": "number"}},
            "Last Aeration": {"type": "date", "date": {}},
            "Next Aeration": {
                "type": "formula",
                "formula": {
                    "expression": 'dateAdd(prop("Last Aeration"), prop("Aeration Interval (days)"), "days")'
                }
            },
            # Lawn Care (Sanding)
            "Sanding Interval (days)": {"type": "number", "number": {"format": "number"}},
            "Last Sanded": {"type": "date", "date": {}},
            "Next Sanding": {
                "type": "formula",
                "formula": {
                    "expression": 'dateAdd(prop("Last Sanded"), prop("Sanding Interval (days)"), "days")'
                }
            },
            # General Care & Notes
            "Care Instructions": {"type": "rich_text", "rich_text": {}},
            "Special Notes": {"type": "rich_text", "rich_text": {}},
            "Notes": {"type": "rich_text", "rich_text": {}}
            }
        }
    )

    _LOGGER.info("Database created successfully. ID: %s", result.get("id"))
    _LOGGER.debug("Database properties created: %s", list(result.get("properties", {}).keys()))

    return result


def _get_month_color(month_index: int) -> str:
    """Get color for month based on season."""
    colors = [
        "gray", "gray", "green", "green", "green", "yellow",
        "yellow", "orange", "orange", "brown", "brown", "gray"
    ]
    return colors[month_index]


def _add_example_plants(notion: Client, database_id: str) -> None:
    """Add example plants to the database."""
    _LOGGER.info("Adding %d example plants to database %s", len(EXAMPLE_PLANTS), database_id)

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

            # Add sanding for lawns
            if "Sanding Interval (days)" in plant_data:
                properties["Sanding Interval (days)"] = {
                    "number": plant_data["Sanding Interval (days)"]
                }
                last_sanded = now - timedelta(days=300)
                properties["Last Sanded"] = {
                    "date": {"start": last_sanded.strftime("%Y-%m-%d")}
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

            # Add lifecycle (perennial/annual)
            if "Lifecycle" in plant_data:
                properties["Lifecycle"] = {"select": {"name": plant_data["Lifecycle"]}}

            # Add hardiness zone
            if "Hardiness Zone" in plant_data:
                properties["Hardiness Zone"] = {"select": {"name": plant_data["Hardiness Zone"]}}

            # Add soil type
            if "Soil Type" in plant_data:
                properties["Soil Type"] = {"select": {"name": plant_data["Soil Type"]}}

            # Add soil pH
            if "Soil pH" in plant_data:
                properties["Soil pH"] = {"select": {"name": plant_data["Soil pH"]}}

            # Add height
            if "Height" in plant_data:
                properties["Height"] = {
                    "rich_text": [{"text": {"content": plant_data["Height"]}}]
                }

            # Add growth per year
            if "Growth per Year" in plant_data:
                properties["Growth per Year"] = {
                    "rich_text": [{"text": {"content": plant_data["Growth per Year"]}}]
                }

            # Add bad companions
            if "Bad Companions" in plant_data:
                properties["Bad Companions"] = {
                    "rich_text": [{"text": {"content": plant_data["Bad Companions"]}}]
                }

            # Add winterize
            if "Winterize" in plant_data:
                properties["Winterize"] = {"checkbox": plant_data["Winterize"]}

            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            _LOGGER.info("Successfully added example plant: %s", plant_data["Name"])
        except Exception as err:
            _LOGGER.error("Failed to add example plant %s: %s", plant_data["Name"], err, exc_info=True)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Notion Garden Care."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

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
                    # URL format: https://www.notion.so/Title-UUID or https://www.notion.so/UUID
                    parts = parent_page_id.split("/")
                    last_part = parts[-1] if parts else parent_page_id

                    # Remove query parameters
                    if "?" in last_part:
                        last_part = last_part.split("?")[0]

                    # If format is Title-UUID, get the UUID part (last 32 chars after removing dashes)
                    if "-" in last_part:
                        # Get all parts after splitting by dash
                        uuid_part = last_part.split("-")[-1]
                        # If the last part is too short, it might be Title-UUID format
                        if len(uuid_part) < 32:
                            # Take the full string, remove all dashes and get last 32 chars
                            clean = last_part.replace("-", "")
                            if len(clean) >= 32:
                                parent_page_id = clean[-32:]
                            else:
                                parent_page_id = uuid_part
                        else:
                            parent_page_id = uuid_part
                    else:
                        parent_page_id = last_part.replace("-", "")[:32]

                self.data[CONF_PARENT_PAGE_ID] = parent_page_id
                self.data[CONF_CREATE_PLANT_SENSORS] = user_input.get(CONF_CREATE_PLANT_SENSORS, True)

                if user_input.get(CONF_CREATE_DATABASE, True):
                    # Create database automatically
                    database_id = await create_database(
                        self.hass,
                        self.data[CONF_NOTION_TOKEN],
                        parent_page_id,
                        user_input.get(CONF_ADD_EXAMPLES, True)
                    )
                    self.data[CONF_DATABASE_ID] = database_id

                    # Go to AI configuration step
                    return await self.async_step_ai_config()
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

                # Go to AI configuration step
                return await self.async_step_ai_config()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="database",
            data_schema=STEP_DATABASE_SCHEMA,
            errors=errors,
        )

    async def async_step_ai_config(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle AI conversation agent configuration."""
        if user_input is not None:
            # Store AI config in options (not data, since it's optional config)
            return self.async_create_entry(
                title="Notion Garden Care",
                data=self.data,
                options={CONF_CONVERSATION_AGENT: user_input.get(CONF_CONVERSATION_AGENT, "")}
            )

        # Get list of conversation agents
        conversation_agents = await self._get_conversation_agents()

        return self.async_show_form(
            step_id="ai_config",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CONVERSATION_AGENT, default=""): vol.In(conversation_agents),
                }
            ),
        )

    async def _get_conversation_agents(self) -> dict[str, str]:
        """Get available conversation agents."""
        agents = {"": "None (disable AI features)"}

        # Get all conversation entities
        entity_reg = er.async_get(self.hass)
        for entity in entity_reg.entities.values():
            if entity.domain == "conversation":
                name = entity.name or entity.original_name or entity.entity_id
                agents[entity.entity_id] = name

        return agents


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Notion Garden Care."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get list of conversation agents
        conversation_agents = await self._get_conversation_agents()

        # Get current value
        current_agent = self._config_entry.options.get(CONF_CONVERSATION_AGENT, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CONVERSATION_AGENT,
                        default=current_agent,
                    ): vol.In(conversation_agents),
                }
            ),
        )

    async def _get_conversation_agents(self) -> dict[str, str]:
        """Get available conversation agents."""
        agents = {"": "None (disable AI features)"}

        # Get all conversation entities
        entity_reg = er.async_get(self.hass)
        for entity in entity_reg.entities.values():
            if entity.domain == "conversation":
                # Use entity_id as key, friendly name or entity_id as value
                name = entity.name or entity.original_name or entity.entity_id
                agents[entity.entity_id] = name

        return agents


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
