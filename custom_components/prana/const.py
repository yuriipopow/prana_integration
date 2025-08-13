"""Constants for the Prana integration."""

DOMAIN = "prana"

CONF_CONFIG = "config"
CONF_MDNS = "mdns"


class PranaFanType:
    """Enumeration of Prana fan types."""
    EXTRACT = "extract"
    SUPPLY = "supply"
    BOUNDED = "bounded"

class PranaSwitchType:
    BOUND = "bound"
    HEATER = "heater"
    NIGHT = "night"
    BOOST = "boost"
    AUTO = "auto"
    AUTO_PLUS = "auto_plus"
    WINTER = "winter"

class PranaSensorType:
    INSIDE_TEMPERATURE = "inside_temperature"
    OUTSIDE_TEMPERATURE = "outside_temperature"
    INSIDE_TEMPERATURE_2 = "inside_temperature_2"
    OUTSIDE_TEMPERATURE_2 = "outside_temperature_2"
    HUMIDITY = "humidity"
    VOC = "voc"
    CO2 = "co2"
    AIR_PRESSURE = "air_pressure"
    VOC = "voc"