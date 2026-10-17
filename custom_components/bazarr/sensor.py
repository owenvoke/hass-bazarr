"""Sensors for Bazarr."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BazarrConfigEntry, BazarrData
from .entity import BazarrEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class BazarrSensorEntityDescription(SensorEntityDescription):
    """Describes a Bazarr sensor."""

    value_fn: Callable[[BazarrData], int]


SENSORS: tuple[BazarrSensorEntityDescription, ...] = (
    BazarrSensorEntityDescription(
        key="wanted_movies",
        translation_key="wanted_movies",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.wanted_movies,
    ),
    BazarrSensorEntityDescription(
        key="wanted_episodes",
        translation_key="wanted_episodes",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.wanted_episodes,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BazarrConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    async_add_entities(
        BazarrSensor(entry.runtime_data, description, description.key)
        for description in SENSORS
    )


class BazarrSensor(BazarrEntity, SensorEntity):
    """A count of wanted subtitles."""

    entity_description: BazarrSensorEntityDescription

    @property
    def native_value(self) -> int:
        """Return the count."""
        return self.entity_description.value_fn(self.coordinator.data)
