"""Base entity for Bazarr."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BazarrDataUpdateCoordinator


class BazarrEntity(CoordinatorEntity[BazarrDataUpdateCoordinator]):
    """A Bazarr entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BazarrDataUpdateCoordinator,
        description: EntityDescription,
        unique_id_suffix: str,
    ) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        # Only used when the device is created; the coordinator keeps the
        # version up to date after that.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Bazarr",
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Bazarr",
            configuration_url=coordinator.url,
            sw_version=coordinator.data.version,
        )
