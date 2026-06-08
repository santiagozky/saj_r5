"""Sensors for the SAJ R5 integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfMass,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SajR5Coordinator


@dataclass(frozen=True, kw_only=True)
class SajR5SensorEntityDescription(SensorEntityDescription):
    """Description for a SAJ R5 sensor."""


SENSOR_DESCRIPTIONS: tuple[SajR5SensorEntityDescription, ...] = (
    SajR5SensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:connection",
    ),
    SajR5SensorEntityDescription(
        key="total_generated_energy",
        translation_key="total_generated_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SajR5SensorEntityDescription(
        key="total_running_time",
        translation_key="total_running_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SajR5SensorEntityDescription(
        key="today_generated_energy",
        translation_key="today_generated_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SajR5SensorEntityDescription(
        key="today_running_time",
        translation_key="today_running_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SajR5SensorEntityDescription(
        key="pv1_voltage",
        translation_key="pv1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv1_current",
        translation_key="pv1_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_voltage",
        translation_key="pv2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_current",
        translation_key="pv2_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_voltage",
        translation_key="pv3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_current",
        translation_key="pv3_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv1_strcurr1",
        translation_key="pv1_strcurr1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv1_strcurr2",
        translation_key="pv1_strcurr2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv1_strcurr3",
        translation_key="pv1_strcurr3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv1_strcurr4",
        translation_key="pv1_strcurr4",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_strcurr1",
        translation_key="pv2_strcurr1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_strcurr2",
        translation_key="pv2_strcurr2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_strcurr3",
        translation_key="pv2_strcurr3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv2_strcurr4",
        translation_key="pv2_strcurr4",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_strcurr1",
        translation_key="pv3_strcurr1",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_strcurr2",
        translation_key="pv3_strcurr2",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_strcurr3",
        translation_key="pv3_strcurr3",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="pv3_strcurr4",
        translation_key="pv3_strcurr4",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="output_power",
        translation_key="output_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="grid_connected_frequency",
        translation_key="grid_connected_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line1_voltage",
        translation_key="line1_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line1_current",
        translation_key="line1_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line2_voltage",
        translation_key="line2_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line2_current",
        translation_key="line2_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line3_voltage",
        translation_key="line3_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="line3_current",
        translation_key="line3_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="bus_voltage",
        translation_key="bus_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SajR5SensorEntityDescription(
        key="co2_reduction",
        translation_key="co2_reduction",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:molecule-co2",
    ),
    SajR5SensorEntityDescription(
        key="running_state",
        translation_key="running_state",
        icon="mdi:state-machine",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SAJ R5 sensors."""

    coordinator: SajR5Coordinator = entry.runtime_data
    async_add_entities(
        SajR5Sensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class SajR5Sensor(CoordinatorEntity[SajR5Coordinator], SensorEntity):
    """SAJ R5 sensor entity."""

    entity_description: SajR5SensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SajR5Coordinator,
        entry: ConfigEntry,
        description: SajR5SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this inverter."""

        device_details = self.coordinator.device_details
        identifiers = {(DOMAIN, self._entry.entry_id)}
        connections = set()

        if device_details.serial_number:
            identifiers.add((DOMAIN, device_details.serial_number))

        if device_details.mac_address:
            connections.add((CONNECTION_NETWORK_MAC, device_details.mac_address))

        configuration_host = device_details.ip_address or self._entry.data[CONF_HOST]

        return DeviceInfo(
            identifiers=identifiers,
            connections=connections,
            manufacturer="SAJ",
            model="R5",
            name=self._entry.data[CONF_NAME],
            serial_number=device_details.serial_number,
            configuration_url=f"http://{configuration_host}",
        )

    @property
    def available(self) -> bool:
        """Return true if the coordinator and this value are available."""

        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get(self.entity_description.key) is not None
        )

    @property
    def native_value(self) -> Any | None:
        """Return the sensor value."""

        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.entity_description.key)
