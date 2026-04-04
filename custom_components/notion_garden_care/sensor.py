"""Sensor platform for Notion Garden Care."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import httpx
from notion_client import Client
from notion_client.errors import APIResponseError

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, CONF_CREATE_PLANT_SENSORS

_LOGGER = logging.getLogger(__name__)

# Scan interval in seconds - convert to timedelta
SCAN_INTERVAL = timedelta(seconds=3600)

STORAGE_KEY = "notion_garden_care"
STORAGE_VERSION = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Notion Garden Care sensors based on a config entry."""
    notion = hass.data[DOMAIN][config_entry.entry_id]["notion"]
    database_id = hass.data[DOMAIN][config_entry.entry_id]["database_id"]
    notion_token = config_entry.data["notion_token"]

    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{config_entry.entry_id}")

    async def async_update_data():
        """Fetch data from Notion API and persist to local cache."""
        try:
            _LOGGER.debug("Fetching data from Notion database: %s", database_id)
            data = await hass.async_add_executor_job(
                _fetch_database_data,
                notion_token,
                database_id
            )
            _LOGGER.info("Successfully fetched %d plants from Notion", len(data.get("results", [])))
            await store.async_save(data)
            return data
        except APIResponseError as err:
            _LOGGER.error("Notion API error: %s", err)
            raise UpdateFailed(f"Error communicating with Notion API: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error fetching data: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="notion_garden_care",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Seed coordinator from local cache so sensors are available immediately
    # even when Notion is unreachable on startup.
    cached = await store.async_load()
    if cached:
        coordinator.data = cached
        _LOGGER.info("Loaded %d plants from local cache", len(cached.get("results", [])))
        # Refresh in the background so setup isn't blocked by a slow/unreachable Notion API.
        hass.async_create_task(coordinator.async_refresh())
    else:
        # No cache — must wait for first successful data fetch before adding entities.
        await coordinator.async_config_entry_first_refresh()

    # Store coordinator for service access
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator

    # Create aggregate sensors (always created)
    sensors = [
        NotionGardenCareDatabaseSensor(coordinator),
        PlantsToWaterSensor(coordinator),
        PlantsToFertilizeSensor(coordinator),
        PlantsToPruneSensor(coordinator),
        ActivePlantsCountSensor(coordinator),
    ]

    # Create individual plant sensors if enabled
    create_plant_sensors = config_entry.data.get(CONF_CREATE_PLANT_SENSORS, True)
    if create_plant_sensors and coordinator.data:
        for plant_data in coordinator.data.get("results", []):
            plant_sensor = PlantSensor(coordinator, plant_data)
            if plant_sensor.name:  # Only add if plant has a valid name
                sensors.append(plant_sensor)
        _LOGGER.info("Created %d individual plant sensors", len(sensors) - 5)

    async_add_entities(sensors)


def _fetch_database_data(notion_token: str, database_id: str) -> dict[str, Any]:
    """Fetch data from Notion database using direct API call."""
    _LOGGER.debug("Querying Notion database: %s", database_id)
    try:
        # Use httpx to make direct API call
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        response = httpx.post(url, headers=headers, json={}, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        _LOGGER.debug("Query response keys: %s", data.keys() if data else "None")
        _LOGGER.info("Successfully fetched %d results", len(data.get("results", [])))
        return data
    except httpx.HTTPError as err:
        _LOGGER.error("Error in _fetch_database_data: %s", err, exc_info=True)
        raise Exception(f"Notion API error: {err}") from err
    except Exception as err:
        _LOGGER.error("Unexpected error in _fetch_database_data: %s", err, exc_info=True)
        raise


class NotionGardenCareDatabaseSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the Notion database summary."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Notion Garden Care Database"
        self._attr_unique_id = "notion_garden_care_database"
        self._attr_icon = "mdi:database"

    @property
    def native_value(self) -> int:
        """Return the number of plants in database."""
        if self.coordinator.data:
            return len(self.coordinator.data.get("results", []))
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return summary attributes (not full raw data to avoid exceeding 16KB limit)."""
        if not self.coordinator.data:
            return {}

        results = self.coordinator.data.get("results", [])

        # Extract plant names and basic info only
        plants_summary = []
        for plant in results:
            try:
                name_prop = plant.get("properties", {}).get("Name", {})
                name = None
                if name_prop.get("title") and len(name_prop["title"]) > 0:
                    name = name_prop["title"][0].get("plain_text")

                type_prop = plant.get("properties", {}).get("Type", {})
                plant_type = None
                if type_prop.get("select"):
                    plant_type = type_prop["select"].get("name")

                active_prop = plant.get("properties", {}).get("Active", {})
                active = active_prop.get("checkbox", False)

                if name:
                    plants_summary.append({
                        "name": name,
                        "type": plant_type,
                        "active": active,
                        "page_id": plant.get("id"),
                    })
            except (KeyError, TypeError, IndexError):
                continue

        return {
            "plant_count": len(results),
            "plants": [p["name"] for p in plants_summary],
            "plants_summary": plants_summary,
            "has_more": self.coordinator.data.get("has_more", False),
        }


class PlantsToWaterSensor(CoordinatorEntity, SensorEntity):
    """Sensor for plants that need watering."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Plants to Water"
        self._attr_unique_id = "plants_to_water"
        self._attr_icon = "mdi:watering-can"

    @property
    def native_value(self) -> int:
        """Return the number of plants that need watering."""
        return len(self._get_plants_to_water())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        plants_to_water = self._get_plants_to_water()
        return {
            "plants": [p["name"] for p in plants_to_water],
            "plant_details": plants_to_water,
        }

    def _get_plants_to_water(self) -> list[dict[str, Any]]:
        """Get list of plants that need watering."""
        if not self.coordinator.data:
            return []

        plants = []
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        for plant in self.coordinator.data.get("results", []):
            try:
                next_water_prop = plant.get("properties", {}).get("Next Water", {})
                if next_water_prop.get("formula"):
                    formula_data = next_water_prop["formula"]
                    # Check if formula type is date
                    if formula_data.get("type") == "date":
                        date_obj = formula_data.get("date")
                        if date_obj:
                            # Extract the start date from the date object
                            next_water_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                            if next_water_date and next_water_date <= today:
                                name = self._get_plant_name(plant)
                                if name:
                                    plants.append({
                                        "name": name,
                                        "page_id": plant["id"],
                                        "due_date": next_water_date,
                                    })
            except (KeyError, TypeError):
                continue

        return plants

    def _get_plant_name(self, plant: dict) -> str | None:
        """Extract plant name from Notion page."""
        try:
            name_prop = plant.get("properties", {}).get("Name", {})
            if name_prop.get("title") and len(name_prop["title"]) > 0:
                return name_prop["title"][0].get("plain_text")
        except (KeyError, TypeError, IndexError):
            pass
        return None


class PlantsToFertilizeSensor(CoordinatorEntity, SensorEntity):
    """Sensor for plants that need fertilizing."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Plants to Fertilize"
        self._attr_unique_id = "plants_to_fertilize"
        self._attr_icon = "mdi:spray-bottle"

    @property
    def native_value(self) -> int:
        """Return the number of plants that need fertilizing."""
        return len(self._get_plants_to_fertilize())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        plants_to_fertilize = self._get_plants_to_fertilize()
        return {
            "plants": [p["name"] for p in plants_to_fertilize],
            "plant_details": plants_to_fertilize,
        }

    def _get_plants_to_fertilize(self) -> list[dict[str, Any]]:
        """Get list of plants that need fertilizing."""
        if not self.coordinator.data:
            return []

        plants = []
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        for plant in self.coordinator.data.get("results", []):
            try:
                next_fertilize_prop = plant.get("properties", {}).get("Next Fertilize", {})
                if next_fertilize_prop.get("formula"):
                    formula_data = next_fertilize_prop["formula"]
                    # Check if formula type is date
                    if formula_data.get("type") == "date":
                        date_obj = formula_data.get("date")
                        if date_obj:
                            # Extract the start date from the date object
                            next_fertilize_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                            if next_fertilize_date and next_fertilize_date <= today:
                                name = self._get_plant_name(plant)
                                if name:
                                    plants.append({
                                        "name": name,
                                        "page_id": plant["id"],
                                        "due_date": next_fertilize_date,
                                    })
            except (KeyError, TypeError):
                continue

        return plants

    def _get_plant_name(self, plant: dict) -> str | None:
        """Extract plant name from Notion page."""
        try:
            name_prop = plant.get("properties", {}).get("Name", {})
            if name_prop.get("title") and len(name_prop["title"]) > 0:
                return name_prop["title"][0].get("plain_text")
        except (KeyError, TypeError, IndexError):
            pass
        return None


class PlantsToPruneSensor(CoordinatorEntity, SensorEntity):
    """Sensor for plants that need pruning this month."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Plants to Prune"
        self._attr_unique_id = "plants_to_prune"
        self._attr_icon = "mdi:content-cut"

    @property
    def native_value(self) -> int:
        """Return the number of plants that need pruning."""
        return len(self._get_plants_to_prune())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        plants_to_prune = self._get_plants_to_prune()
        return {
            "plants": [p["name"] for p in plants_to_prune],
            "plant_details": plants_to_prune,
        }

    def _get_plants_to_prune(self) -> list[dict[str, Any]]:
        """Get list of plants that need pruning this month."""
        if not self.coordinator.data:
            return []

        plants = []
        from datetime import datetime

        month_map = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        current_month = month_map[datetime.now().month]

        for plant in self.coordinator.data.get("results", []):
            try:
                prune_months_prop = plant.get("properties", {}).get("Prune Months", {})
                if prune_months_prop.get("multi_select"):
                    prune_months = [m["name"] for m in prune_months_prop["multi_select"]]
                    if current_month in prune_months:
                        name = self._get_plant_name(plant)
                        if name:
                            plants.append({
                                "name": name,
                                "page_id": plant["id"],
                                "months": prune_months,
                            })
            except (KeyError, TypeError):
                continue

        return plants

    def _get_plant_name(self, plant: dict) -> str | None:
        """Extract plant name from Notion page."""
        try:
            name_prop = plant.get("properties", {}).get("Name", {})
            if name_prop.get("title") and len(name_prop["title"]) > 0:
                return name_prop["title"][0].get("plain_text")
        except (KeyError, TypeError, IndexError):
            pass
        return None


class ActivePlantsCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the number of active plants."""

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Active Plants Count"
        self._attr_unique_id = "active_plants_count"
        self._attr_icon = "mdi:flower"

    @property
    def native_value(self) -> int:
        """Return the number of active plants."""
        if not self.coordinator.data:
            return 0

        count = 0
        for plant in self.coordinator.data.get("results", []):
            try:
                active_prop = plant.get("properties", {}).get("Active", {})
                if active_prop.get("checkbox"):
                    count += 1
            except (KeyError, TypeError):
                continue

        return count


class PlantSensor(CoordinatorEntity, SensorEntity):
    """Individual sensor for a specific plant."""

    def __init__(self, coordinator: DataUpdateCoordinator, plant_data: dict) -> None:
        """Initialize the plant sensor."""
        self._page_id = plant_data.get("id", "")
        self._plant_name = self._extract_plant_name(plant_data)

        # Create safe name for entity_id - must be done BEFORE super().__init__
        if self._plant_name:
            # Remove special characters and normalize
            import re
            safe = self._plant_name.lower()
            safe = re.sub(r'[^a-z0-9_]', '_', safe)  # Replace non-alphanumeric with underscore
            safe = re.sub(r'_+', '_', safe)  # Replace multiple underscores with single
            safe = safe.strip('_')  # Remove leading/trailing underscores
            self._safe_name = safe
        else:
            self._safe_name = self._page_id[:8]

        # Set entity_id BEFORE calling super().__init__()
        # This ensures the entity registry uses our specified entity_id
        self.entity_id = f"sensor.garden_care_{self._safe_name}"

        # Now call parent init
        super().__init__(coordinator)

        # Set unique_id and name after super init
        self._attr_unique_id = f"garden_care_{self._safe_name}"
        if self._plant_name:
            self._attr_name = self._plant_name  # Friendly name is just the plant name
        else:
            self._attr_name = f"Plant {self._page_id[:8]}"

        self._attr_icon = "mdi:flower"

        _LOGGER.debug(
            "Created PlantSensor: name=%s, entity_id=%s, unique_id=%s",
            self._attr_name, self.entity_id, self._attr_unique_id
        )

    @property
    def suggested_object_id(self) -> str:
        """Return the suggested object ID (used when entity_id not set)."""
        return f"garden_care_{self._safe_name}"

    def _extract_plant_name(self, plant_data: dict) -> str | None:
        """Extract plant name from Notion page data."""
        try:
            name_prop = plant_data.get("properties", {}).get("Name", {})
            if name_prop.get("title") and len(name_prop["title"]) > 0:
                return name_prop["title"][0].get("plain_text")
        except (KeyError, TypeError, IndexError):
            pass
        return None

    def _get_current_plant_data(self) -> dict | None:
        """Get current plant data from coordinator."""
        if not self.coordinator.data:
            return None

        for plant in self.coordinator.data.get("results", []):
            if plant.get("id") == self._page_id:
                return plant
        return None

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return self._attr_name if self._plant_name else None

    @property
    def native_value(self) -> str:
        """Return the status of the plant."""
        plant_data = self._get_current_plant_data()
        if not plant_data:
            return "Unknown"

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        current_month = datetime.now().strftime("%B")  # Full month name

        statuses = []

        # Check if needs watering
        try:
            next_water_prop = plant_data.get("properties", {}).get("Next Water", {})
            if next_water_prop.get("formula") and next_water_prop["formula"].get("type") == "date":
                date_obj = next_water_prop["formula"].get("date")
                if date_obj:
                    next_water_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                    if next_water_date and next_water_date <= today:
                        statuses.append("Needs Water")
        except (KeyError, TypeError):
            pass

        # Check if needs fertilizing
        try:
            next_fert_prop = plant_data.get("properties", {}).get("Next Fertilize", {})
            if next_fert_prop.get("formula") and next_fert_prop["formula"].get("type") == "date":
                date_obj = next_fert_prop["formula"].get("date")
                if date_obj:
                    next_fert_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                    if next_fert_date and next_fert_date <= today:
                        statuses.append("Needs Fertilizer")
        except (KeyError, TypeError):
            pass

        # Check if needs pruning this month
        try:
            prune_months_prop = plant_data.get("properties", {}).get("Prune Months", {})
            if prune_months_prop.get("multi_select"):
                prune_months = [m["name"] for m in prune_months_prop["multi_select"]]
                if current_month in prune_months:
                    statuses.append("Needs Pruning")
        except (KeyError, TypeError):
            pass

        # Check if needs harvesting this month
        try:
            harvest_months_prop = plant_data.get("properties", {}).get("Harvest Months", {})
            if harvest_months_prop.get("multi_select"):
                harvest_months = [m["name"] for m in harvest_months_prop["multi_select"]]
                if current_month in harvest_months:
                    statuses.append("Ready to Harvest")
        except (KeyError, TypeError):
            pass

        # Check if needs aeration (for lawns)
        try:
            next_aeration_prop = plant_data.get("properties", {}).get("Next Aeration", {})
            if next_aeration_prop.get("formula") and next_aeration_prop["formula"].get("type") == "date":
                date_obj = next_aeration_prop["formula"].get("date")
                if date_obj:
                    next_aeration_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                    if next_aeration_date and next_aeration_date <= today:
                        statuses.append("Needs Aeration")
        except (KeyError, TypeError):
            pass

        # Check if needs sanding (for lawns)
        try:
            next_sanding_prop = plant_data.get("properties", {}).get("Next Sanding", {})
            if next_sanding_prop.get("formula") and next_sanding_prop["formula"].get("type") == "date":
                date_obj = next_sanding_prop["formula"].get("date")
                if date_obj:
                    next_sanding_date = date_obj.get("start") if isinstance(date_obj, dict) else date_obj
                    if next_sanding_date and next_sanding_date <= today:
                        statuses.append("Needs Sanding")
        except (KeyError, TypeError):
            pass

        if statuses:
            return ", ".join(statuses)
        return "OK"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes with all plant details in organized order."""
        plant_data = self._get_current_plant_data()
        if not plant_data:
            return {}

        properties = plant_data.get("properties", {})

        # Define the ordered list of properties by category
        ordered_properties = [
            # ── Basic Info ──
            "Name",
            "Type",
            "Location",
            "Active",
            "Lifecycle",
            "Plant Date",
            # ── Plant Characteristics ──
            "Height",
            "Growth per Year",
            "Hardiness Zone",
            # ── Environment ──
            "Sun Exposure",
            "Soil Type",
            "Soil pH",
            # ── Watering ──
            "Water Interval (days)",
            "Last Watered",
            "Next Water",
            "Water Amount",
            # ── Fertilizing ──
            "Fertilize Interval (days)",
            "Last Fertilized",
            "Next Fertilize",
            "Fertilizer Type",
            # ── Pruning ──
            "Prune Months",
            "Last Pruned",
            "Prune Instructions",
            # ── Harvest ──
            "Harvest Months",
            "Last Harvested",
            "Harvest Notes",
            # ── Lawn Care ──
            "Aeration Interval (days)",
            "Last Aeration",
            "Next Aeration",
            "Sanding Interval (days)",
            "Last Sanded",
            "Next Sanding",
            # ── Companions & Safety ──
            "Companion Plants",
            "Bad Companions",
            "Bee Friendly",
            "Toxicity",
            "Winterize",
            # ── Notes ──
            "Care Instructions",
            "Special Notes",
            "Notes",
            "Additional Information",
        ]

        # Start with page_id and plant_name
        attributes = {
            "page_id": self._page_id,
            "plant_name": self._plant_name,
        }

        # Extract properties in the defined order
        for prop_name in ordered_properties:
            if prop_name not in properties:
                continue

            prop_value = properties[prop_name]
            attr_name = prop_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

            try:
                extracted_value = self._extract_property_value(prop_value)
                if extracted_value is not None:
                    attributes[attr_name] = extracted_value
            except (KeyError, TypeError, IndexError):
                continue

        # Add any remaining properties not in our ordered list (at the end)
        for prop_name, prop_value in properties.items():
            if prop_name in ordered_properties:
                continue

            attr_name = prop_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            if attr_name in attributes:
                continue

            try:
                extracted_value = self._extract_property_value(prop_value)
                if extracted_value is not None:
                    attributes[attr_name] = extracted_value
            except (KeyError, TypeError, IndexError):
                continue

        return attributes

    def _extract_property_value(self, prop_value: dict) -> Any:
        """Extract the value from a Notion property based on its type."""
        prop_type = prop_value.get("type")

        if prop_type == "title":
            if prop_value.get("title") and len(prop_value["title"]) > 0:
                return prop_value["title"][0].get("plain_text")

        elif prop_type == "rich_text":
            if prop_value.get("rich_text") and len(prop_value["rich_text"]) > 0:
                return prop_value["rich_text"][0].get("plain_text")

        elif prop_type == "number":
            return prop_value.get("number")

        elif prop_type == "select":
            if prop_value.get("select"):
                return prop_value["select"].get("name")

        elif prop_type == "multi_select":
            if prop_value.get("multi_select"):
                return [m["name"] for m in prop_value["multi_select"]]

        elif prop_type == "checkbox":
            return prop_value.get("checkbox", False)

        elif prop_type == "date":
            if prop_value.get("date"):
                date_obj = prop_value["date"]
                return date_obj.get("start") if isinstance(date_obj, dict) else date_obj

        elif prop_type == "formula":
            formula_data = prop_value.get("formula", {})
            formula_type = formula_data.get("type")
            if formula_type == "date":
                date_obj = formula_data.get("date")
                if date_obj:
                    return date_obj.get("start") if isinstance(date_obj, dict) else date_obj
            elif formula_type == "string":
                return formula_data.get("string")
            elif formula_type == "number":
                return formula_data.get("number")
            elif formula_type == "boolean":
                return formula_data.get("boolean")

        return None

    @property
    def icon(self) -> str:
        """Return the icon based on plant type."""
        plant_data = self._get_current_plant_data()
        if not plant_data:
            return "mdi:flower"

        try:
            type_prop = plant_data.get("properties", {}).get("Type", {})
            if type_prop.get("select"):
                plant_type = type_prop["select"].get("name", "").lower()
                icon_map = {
                    "tree": "mdi:tree",
                    "shrub": "mdi:tree-outline",
                    "vegetable": "mdi:carrot",
                    "herb": "mdi:leaf",
                    "lawn": "mdi:grass",
                    "plant": "mdi:flower",
                }
                return icon_map.get(plant_type, "mdi:flower")
        except (KeyError, TypeError):
            pass

        return "mdi:flower"
