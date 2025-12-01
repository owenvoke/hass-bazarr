"""Sensor platform for Bazarr integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BazarrConfigEntry
from .const import DOMAIN
from .coordinator import BazarrDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BazarrConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bazarr sensors based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        [
            BazarrWantedMoviesSensor(coordinator, entry),
            BazarrWantedEpisodesSensor(coordinator, entry),
        ]
    )


class BazarrSensorBase(CoordinatorEntity[BazarrDataUpdateCoordinator], SensorEntity):
    """Base class for Bazarr sensors."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BazarrDataUpdateCoordinator,
        entry: BazarrConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        """Return device information about this Bazarr instance."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Bazarr",
            "manufacturer": "Bazarr",
            "configuration_url": f"{self._entry.data['url']}",
            "sw_version": self.coordinator.data["bazarr_version"],
        }


class BazarrWantedMoviesSensor(BazarrSensorBase):
    """Sensor for wanted movies count."""

    _attr_icon = "mdi:movie-search"
    _attr_translation_key = "wanted_movies"

    def __init__(
        self,
        coordinator: BazarrDataUpdateCoordinator,
        entry: BazarrConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wanted_movies"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("wanted_movies")
        return None


class BazarrWantedEpisodesSensor(BazarrSensorBase):
    """Sensor for wanted episodes count."""

    _attr_icon = "mdi:television-classic"
    _attr_translation_key = "wanted_episodes"

    def __init__(
        self,
        coordinator: BazarrDataUpdateCoordinator,
        entry: BazarrConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_wanted_episodes"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("wanted_episodes")
        return None
