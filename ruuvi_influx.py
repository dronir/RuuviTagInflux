"""
Listen to RuuviTags and upload to influxdb.
"""

import toml
from influxdb import InfluxDBClient
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from sys import exit, argv
import logging


def read_config(filename):
    """ Read config from TOML file.
    """
    with open(filename, 'r') as f:
        return toml.loads(f.read())

def check_config(config):
    """ Check that a config has the required keys.
    """
    return ("host" in config
    and "database" in config
    and "measurement" in config
    and "store_fields" in config)

def connect_influxdb(config):
    """ Return an InfluxDB client object from given config.
    """
    client = InfluxDBClient(host = config["host"],
                            port = config.get("port", 8086),
                            username = config.get("username", ""),
                            password = config.get("password",""),
                            ssl = config.get("ssl", False),
                            verify_ssl = config.get("ssl", False))
    client.switch_database(config["database"])
    return client

def map_mac(config, mac):
    """ Map MAC address to device name from config, defaulting to MAC if not given.
    """
    return config["device-names"].get(mac, mac) if "device-names" in config else mac


def get_location(config, name):
    if not "locations" in config:
        return "unknown"
    return config["locations"].get(name, "unknown")

def ruuvi_to_point(config, received_data):
    """ Format measurement JSON from RuuviTag into InfluxDB data point JSON.
    """
    mac = received_data[0]
    deviceName = map_mac(config, mac)
    
    payload = received_data[1]
    dataFormat = payload.get("data_format", None)
    
    location = get_location(config, deviceName)

    fields = {}
    for fieldName in config["store_fields"]:
        if fieldName in payload:
            fields[fieldName] = payload[fieldName]

    return {
        'measurement' : config["measurement"],
        'tags' : {
            'mac' : mac,
            'device' : deviceName,
            'format' : dataFormat,
            'location' : location
        },
        'fields' : fields
    }



def ruuvi_callback(config, client, received_data):
    """ Callback for ruuvi get_datas(). Format the JSON and send to Influx.
    """
    json_body = ruuvi_to_point(config, received_data)
    client.write_points([json_body])



def main(filename):
    # Read and check config
    config = read_config(filename)
    try:
        assert check_config(config)
    except AssertionError:
        logging.error("Config file failed format check.")
        exit()
    
    # Make InfluxDB client object
    client = connect_influxdb(config)

    # Make actual callback function
    def callback(data):
        return ruuvi_callback(config, client, data)

    # Start listening
    RuuviTagSensor.get_datas(callback)


if __name__ == "__main__":
    try:
        main(argv[1])
    except KeyboardInterrupt:
        exit()
