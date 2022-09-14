"""
Listen to RuuviTags and upload to influxdb.
"""

import toml
import logging

from influxdb import InfluxDBClient
from pydantic import BaseModel, Field
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from typing import Dict, List, Optional, Any, MutableMapping
from sys import exit, argv
from pprint import pformat


logging.basicConfig()
logger = logging.getLogger(__name__)

LOG_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


class Config(BaseModel):
    host: str
    port = 8086
    database: str
    measurement: str
    store_fields: List[str]
    ssl = False
    log_level = "WARNING"
    username: Optional[str]
    password: Optional[str]
    mac_filter: Optional[List[str]]
    device_names: Optional[Dict[str, str]] = Field(..., alias="device-names")
    locations: Optional[Dict[str, str]]


def read_config(filename: str) -> Config:
    """Parse Config object from TOML file."""
    with open(filename, "r") as f:
        return Config.parse_obj(toml.loads(f.read()))


def influxdb_client(config: Config) -> InfluxDBClient:
    """Return an InfluxDB client object from given config."""
    client = InfluxDBClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        ssl=config.ssl,
        verify_ssl=config.ssl,
    )
    client.switch_database(config.database)
    return client


def map_mac(config: Config, mac: str) -> Optional[str]:
    """Maybe get a device name based on MAC address."""
    return None if config.device_names is None else config.device_names.get(mac, None)


def get_location(config: Config, name: Optional[str]) -> Optional[str]:
    """Maybe get a named location of a tag from the config."""
    return (
        None
        if (config.locations is None or name is None)
        else config.locations.get(name, None)
    )


def ruuvi_to_point(config: Config, received_data: List) -> Dict[str, Any]:
    """Format measurement JSON from RuuviTag into InfluxDB data point JSON-like."""
    mac: str = received_data[0]
    payload: MutableMapping[str, Any] = received_data[1]
    data_format = payload.get("data_format", None)
    device_name = map_mac(config, mac)

    tags = {
        "mac": mac,
        "format": data_format,
        "device": device_name,
        "location": get_location(config, device_name),
    }

    fields = {}
    for field_name in config.store_fields:
        if field_name in payload:
            fields[field_name] = payload[field_name]

    return {"measurement": config.measurement, "tags": tags, "fields": fields}


def ruuvi_callback(config: Config, client: InfluxDBClient, received_data: List) -> None:
    """Callback for ruuvi get_datas(). Format the JSON and send to Influx."""
    json_body = ruuvi_to_point(config, received_data)
    logger.debug(f"Trying to upload: {pformat(json_body)}")
    client.write_points([json_body])


def main(filename: str):
    config = read_config(filename)

    logger.setLevel(level=LOG_LEVEL[config.log_level])
    logger.debug("Started with the following config:")
    logger.debug(str(config))

    client = influxdb_client(config)

    def callback(data: List) -> None:
        return ruuvi_callback(config, client, data)

    RuuviTagSensor.get_datas(callback, macs=config.mac_filter)


if __name__ == "__main__":
    try:
        main(argv[1])
    except KeyboardInterrupt:
        exit()
