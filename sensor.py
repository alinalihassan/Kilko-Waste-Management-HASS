"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from kilko_waste import KilkoClient

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Kilko Balance sensor from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    coordinator = KilkoBalanceCoordinator(hass, username, password)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([KilkoBalanceSensor(coordinator, username)], True)

class KilkoBalanceCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Kilko data."""

    def __init__(self, hass: HomeAssistant, username: str, password: str):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Kilko Balance",
            update_interval=timedelta(hours=1),
        )
        self.client = KilkoClient()
        self.username = username
        self.password = password

    async def _async_update_data(self):
        """Fetch data from Kilko."""
        await self.hass.async_add_executor_job(self.client.login, self.username, self.password)
        return await self.hass.async_add_executor_job(self.client.balance)

class KilkoBalanceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Kilko Balance sensor."""

    _attr_native_unit_of_measurement = "credits"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator: KilkoBalanceCoordinator, username: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{username}_balance"
        self._attr_name = f"Kilko Balance ({username})"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return round(self.coordinator.data)