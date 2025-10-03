from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfPressure,
    CONCENTRATION_PARTS_PER_MILLION,
)

from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, PranaSensorType
from .coordinator import PranaCoordinator

class PranaSensor(SensorEntity):
    _attr_has_entity_name = True
    # Виводимо як звичайний сенсор (не в «Налаштування»)
    _attr_entity_category = None
    # Вмикаємо за замовчуванням
    _attr_entity_registry_enabled_default = True

    def __init__(
        self,
        unique_id: str,
        name: str,
        coordinator: PranaCoordinator,
        sensor_key: str,
        device_info,
        sensor_type: PranaSensorType,
    ) -> None:
        self._attr_unique_id = unique_id
        self._attr_name = name
        self.coordinator = coordinator
        self.sensor_key = sensor_key
        self._attr_device_info = device_info
        self.sensor_type = sensor_type

        # Іконка
        self._attr_icon = self.get_icon()

        # Device class та одиниці (щоб UI показував значення одразу)
        if sensor_type in (
            PranaSensorType.INSIDE_TEMPERATURE,
            PranaSensorType.INSIDE_TEMPERATURE_2,
            PranaSensorType.OUTSIDE_TEMPERATURE,
            PranaSensorType.OUTSIDE_TEMPERATURE_2,
        ):
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif sensor_type == PranaSensorType.HUMIDITY:
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_native_unit_of_measurement = PERCENTAGE
        elif sensor_type == PranaSensorType.AIR_PRESSURE:
            self._attr_device_class = SensorDeviceClass.PRESSURE
            self._attr_native_unit_of_measurement = UnitOfPressure.HPA
        elif sensor_type == PranaSensorType.CO2:
            self._attr_device_class = SensorDeviceClass.CO2
            self._attr_native_unit_of_measurement = CONCENTRATION_PARTS_PER_MILLION
        else:
            self._attr_device_class = None  # VOC та інші без класу

    def get_icon(self):
        if self.sensor_type in (
            PranaSensorType.INSIDE_TEMPERATURE,
            PranaSensorType.INSIDE_TEMPERATURE_2,
        ):
            return "mdi:home-thermometer"
        if self.sensor_type in (
            PranaSensorType.OUTSIDE_TEMPERATURE,
            PranaSensorType.OUTSIDE_TEMPERATURE_2,
        ):
            return "mdi:thermometer"
        if self.sensor_type == PranaSensorType.HUMIDITY:
            return "mdi:water-percent"
        if self.sensor_type == PranaSensorType.VOC:
            return "mdi:chemical-weapon"
        if self.sensor_type == PranaSensorType.AIR_PRESSURE:
            return "mdi:gauge"
        if self.sensor_type == PranaSensorType.CO2:
            return "mdi:molecule-co2"
        return "mdi:help"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.sensor_type, None)

    @property
    def available(self) -> bool:
        return self.coordinator.data.get(self.sensor_type, None) is not None

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: PranaCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_info = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.data.get("name", "Prana Device"),
        "manufacturer": "Prana",
        "model": "PRANA RECUPERATOR",
    }
    entities =[
        PranaSensor(unique_id=f"{entry.entry_id}-inside_temperature", name="Inside Temperature", coordinator=coordinator, sensor_key="inside_temperature", device_info=device_info, sensor_type=PranaSensorType.INSIDE_TEMPERATURE) if coordinator.data.get(PranaSensorType.INSIDE_TEMPERATURE) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-outside_temperature", name="Outside Temperature", coordinator=coordinator, sensor_key="outside_temperature", device_info=device_info, sensor_type=PranaSensorType.OUTSIDE_TEMPERATURE) if coordinator.data.get(PranaSensorType.OUTSIDE_TEMPERATURE) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-inside_temperature2", name="Inside Temperature 2", coordinator=coordinator, sensor_key="inside_temperature2", device_info=device_info, sensor_type=PranaSensorType.INSIDE_TEMPERATURE_2) if coordinator.data.get(PranaSensorType.INSIDE_TEMPERATURE_2) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-outside_temperature2", name="Outside Temperature 2", coordinator=coordinator, sensor_key="outside_temperature2", device_info=device_info, sensor_type=PranaSensorType.OUTSIDE_TEMPERATURE_2) if coordinator.data.get(PranaSensorType.OUTSIDE_TEMPERATURE_2) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-humidity", name="Humidity", coordinator=coordinator, sensor_key="humidity", device_info=device_info, sensor_type=PranaSensorType.HUMIDITY) if coordinator.data.get(PranaSensorType.HUMIDITY) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-voc", name="VOC", coordinator=coordinator, sensor_key="voc", device_info=device_info, sensor_type=PranaSensorType.VOC) if coordinator.data.get(PranaSensorType.VOC) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-air_pressure", name="Air Pressure", coordinator=coordinator, sensor_key="air_pressure", device_info=device_info, sensor_type=PranaSensorType.AIR_PRESSURE) if coordinator.data.get(PranaSensorType.AIR_PRESSURE) is not None else None,
        PranaSensor(unique_id=f"{entry.entry_id}-co2", name="CO2", coordinator=coordinator, sensor_key="co2", device_info=device_info, sensor_type=PranaSensorType.CO2) if coordinator.data.get(PranaSensorType.CO2) is not None else None,
    ]
    async_add_entities([e for e in entities if e is not None], update_before_add=True)