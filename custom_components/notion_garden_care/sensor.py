"""Sensor platform for Notion Garden Care."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Notion Garden Care sensors based on a config entry."""
    notion = hass.data[DOMAIN][config_entry.entry_id]["notion"]
    database_id = hass.data[DOMAIN][config_entry.entry_id]["database_id"]

    async def async_update_data():
        """Fetch data from Notion API."""
        try:
            return await hass.async_add_executor_job(
                _fetch_database_data,
                notion,
                database_id
            )
        except APIResponseError as err:
            raise UpdateFailed(f"Error communicating with Notion API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="notion_garden_care",
        update_method=async_update_data,
        update_interval=timedelta(seconds=SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create sensors
    sensors = [
        NotionGardenCareDatabaseSensor(coordinator),
        PlantsToWaterSensor(coordinator),
        PlantsToFertilizeSensor(coordinator),
        PlantsToPruneSensor(coordinator),
        ActivePlantsCountSensor(coordinator),
    ]

    async_add_entities(sensors)


def _fetch_database_data(notion: Client, database_id: str) -> dict[str, Any]:
    """Fetch data from Notion database."""
    response = notion.databases.query(database_id=database_id)
    return response


class NotionGardenCareDatabaseSensor(CoordinatorEntity, SensorEntity):
    """Sensor for the raw Notion database data."""

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
        """Return the state attributes."""
        if self.coordinator.data:
            return {
                "results": self.coordinator.data.get("results", []),
                "has_more": self.coordinator.data.get("has_more", False),
            }
        return {}


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
                    next_water_date = next_water_prop["formula"].get("date")
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
                    next_fertilize_date = next_fertilize_prop["formula"].get("date")
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
