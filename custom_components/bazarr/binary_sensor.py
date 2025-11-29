"""Binary sensor platform for Bazarr integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
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
    """Set up Bazarr binary sensors based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities([BazarrHealthIssuesBinarySensor(coordinator, entry)])


class BazarrHealthIssuesBinarySensor(
    CoordinatorEntity[BazarrDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor for Bazarr health issues."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "health"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BazarrDataUpdateCoordinator,
        entry: BazarrConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_health_issues"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information about this Bazarr instance."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Bazarr",
            "manufacturer": "Bazarr",
            "configuration_url": f"{self._entry.data['url']}",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if there are health issues."""
        if self.coordinator.data:
            health_issues = self.coordinator.data.get("health_issues", [])
            return bool(health_issues)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.coordinator.data:
            health_issues = self.coordinator.data.get("health_issues", [])
            return {"issues": health_issues}
        return None
