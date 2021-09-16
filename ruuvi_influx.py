"""
Listen to RuuviTags and upload to influxdb.
"""

import toml
from influxdb import InfluxDBClient
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from sys import exit, argv
import logging
from pprint import pformat

from typing import Dict, List, Optional, Any, MutableMapping

logger = logging.getLogger(__name__)

LOG_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR
}

JsonObject = MutableMapping[str, Any]


def read_config(filename: str) -> JsonObject:
    """ Read config from TOML file.
    """
    with open(filename, 'r') as f:
        return toml.loads(f.read())


def check_config(config: JsonObject) -> bool:
    """ Check that a config has the required keys.
    """
    return ("host" in config
            and "database" in config
            and "measurement" in config
            and "store_fields" in config)


def connect_influxdb(config: JsonObject) -> InfluxDBClient:
    """ Return an InfluxDB client object from given config.
    """
    client = InfluxDBClient(host=config["host"],
                            port=config.get("port", 8086),
                            username=config.get("username", ""),
                            password=config.get("password", ""),
                            ssl=config.get("ssl", False),
                            verify_ssl=config.get("ssl", False))
    client.switch_database(config["database"])
    return client


def map_mac(config: JsonObject, mac: str) -> Optional[str]:
    """ Map MAC address to device name from config, defaulting to MAC if not given.
    """
    return (config["device-names"].get(mac, None)
            if "device-names" in config else None)


def get_location(config: JsonObject, name: Optional[str]) -> Optional[str]:
    """Get location of a tag from the config, based on its name.
    Returns None if a name isn't found.
    """
    if "locations" not in config.keys() or name is None:
        return None
    return config["locations"].get(name, None)


def ruuvi_to_point(config: JsonObject, received_data: List) -> JsonObject:
    """ Format measurement JSON from RuuviTag into InfluxDB data point JSON.
    """
    mac = received_data[0]
    payload: JsonObject = received_data[1]
    data_format = payload.get("data_format", None)
    device_name = map_mac(config, mac)

    tags = {
        'mac': mac,
        'format': data_format,
        'device': device_name,
        'location': get_location(config, device_name)
    }

    fields = {}
    for field_name in config["store_fields"]:
        if field_name in payload:
            fields[field_name] = payload[field_name]

    return {
        'measurement': config["measurement"],
        'tags': tags,
        'fields': fields
    }


def ruuvi_callback(config: JsonObject,
                   client: InfluxDBClient,
                   received_data: List) -> None:
    """ Callback for ruuvi get_datas(). Format the JSON and send to Influx.
    """
    json_body = ruuvi_to_point(config, received_data)
    logger.info(f"Trying to upload: {pformat(json_body)}")
    client.write_points([json_body])


def main(filename: str):
    config = read_config(filename)
    if not check_config(config):
        logger.critical("Config file failed format check.")
        exit()

    level = config.get("log_level", "WARNING")

    logger.setLevel(level=LOG_LEVEL[level])
    logger.debug("Started with the following config:")
    logger.debug(pformat(config))

    mac_filter = config.get("mac_filter", [])
    client = connect_influxdb(config)

    def callback(data: List):
        return ruuvi_callback(config, client, data)

    RuuviTagSensor.get_datas(callback, macs=mac_filter)


if __name__ == "__main__":
    try:
        main(argv[1])
    except KeyboardInterrupt:
        exit()
