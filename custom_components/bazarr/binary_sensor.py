"""Binary sensors for Bazarr."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import BazarrConfigEntry
from .entity import BazarrEntity

PARALLEL_UPDATES = 0

HEALTH = BinarySensorEntityDescription(
    key="health",
    translation_key="health",
    device_class=BinarySensorDeviceClass.PROBLEM,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BazarrConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    async_add_entities(
        [BazarrHealthIssuesBinarySensor(entry.runtime_data, HEALTH, "health_issues")]
    )


class BazarrHealthIssuesBinarySensor(BazarrEntity, BinarySensorEntity):
    """Whether Bazarr reports any health issues."""

    @property
    def is_on(self) -> bool:
        """Return true if there are health issues."""
        return bool(self.coordinator.data.health_issues)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the health issues."""
        return {"issues": self.coordinator.data.health_issues}
