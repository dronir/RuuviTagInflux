# Ruuvitag InfluxDB uploader

## Description

My personal take on a simple Python program that listens to a bunch of RuuviTag devices and uploads the data to an
InfluxDB database. It does minimally what I need it to do.

## Installation on a Raspberry Pi

### Prerequisites

Assuming you've taken a bluetooth-capable Raspberry Pi with the latest command line only version of Raspbian, configured
it enough that it's safely connected to your network, and ran `sudo apt-get update && sudo apt-get -y upgrade`.

First install some stuff: `sudo apt-get -y install git pi-bluetooth bluez blueman`.

[TODO: check exactly which of those bluetooth libraries are needed and remove rest.]

You need a recent version of Python (3.8 probably works, but I have only tested on 3.9). Unfortunately on Raspbian
you need to compile it yourself, since the version in the `apt` repository is too old. Google "raspberry pi python 3.9
install" for instructions. It's not hard, but it takes a few minutes.

### This script and required Python libraries

Clone this git repository.

Install Pipenv with `python -m pip install pipenv`

Install the other requirements with `pipenv install`.


## Configuration

I suggest you copy the example file `test_config.toml` into `actual_config.toml` and then edit that.

### Minimum configuration

The absolutely required config keys are:

- `host`, the hostname of your InfluxDB server. The port defaults to 8086.
- `database`, the name of the database on your InfluxDB server.
- `measurement`, the name of the measurement into which the data is saved.
- `store_fields`, a list of variables that are stored.

Variables read from the RuuviTag will be stored in the database only if they appear in `store_fields`.

The possible variable names are: `temperature`, `pressure`, `humidity`, `battery`, `tx_power`, `movement_counter`,
`tagID`, `measurement_sequence_number`, `acceleration_x`, `acceleration_y`, `acceleration_z`.

### Additional configuration

You can give and array called `mac_filter`, containing MAC addresses of RuuviTags. If it is non-empty, only the devices
whose addresses are in the list are listened to. Otherwise every RuuviTag in the range gets stored.

If your InfluxDB server is on a port different to the default 8086, you can change that by setting `port` to some
integer value.

If your InfluxDB server has SSL enabled, set `ssl = true` in the config.

If your database has user authentication, set the username and password in the config file. I suggest you create a new
user with write-only access to the specific database you want to use with this script.

In InfluxDB, the data points from each RuuviTag will get a tag named `mac` with the device's MAC address as the tag
value. Additionally, you can define two mappings for more practical tags:

Under `[device-names]`, you can associate a name for each MAC address. If the MAC of a RuuviTag matches this list,
its data gets the tag `device`, with the given value. You can find out the MAC addresses of your devices e.g. from the
RuuviTag mobile app.

Under `[locations]`, you can define a map from the device names given above, to location names. If a device name matches
this list, its data will get the tag `location`, with the given value. This allows you to either swap a different device
to a given location, or move a device to a new location. The `location` tag is my preferred way to arrange the data e.g.
when displaying with Grafana.

## Usage

To run the code, use `pipenv run python ruuvi_influx.py actual_config.toml`.
It should "just work", running forever, uploading data as it finds it. Press `ctrl-c` (possibly twice) to quit.

Outside of the Pipenv environment, you may need to set the environmental variable `RUUVI_BLE_ADAPTER="bleson"`.

If the program exits itself soon after starting, your bluetooth stuff is probably broken.

Making this run as a system service probably makes sense.

## TODO

- Add logging level to config.
