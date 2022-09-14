# Ruuvitag InfluxDB uploader

## Description

My personal take on a simple Python program that listens to a bunch of RuuviTag devices 
and uploads the data to an InfluxDB database. It does minimally what I need it to do.

## Installation on a Raspberry Pi

### Prerequisites

Assuming you've taken a bluetooth-capable Raspberry Pi with the latest command line only version of Raspbian, 
configured it enough that it's safely connected to your network, 
and ran `sudo apt-get update && sudo apt-get -y upgrade`.

First install some stuff: `sudo apt-get -y install git pi-bluetooth bluez python3-dev python3-pip`.

You need a recent version of Python (3.8 probably works, but I have only tested on 3.9).
On older versions of Raspbian you need to compile it yourself, since the version in the `apt` repository is too old. 
Google "raspberry pi python 3.9 install" for instructions. It's not hard, but it takes a few minutes.

After installing Python, upgrade Pip with `sudo python3 -m pip install --upgrade pip`.

Then install Poetry with `sudo python3 -m pip install poetry`.


### Installing and running this program

Clone this git repository.

Install this package and its requirements with `poetry install --only main` in the repo directory.


## Configuration

I suggest you copy the example file `test_config.toml` into `actual_config.toml` and then edit that.

The minimum required config keys are the following four, but there are other important options
that you should also check out (see _Additional configuration_ below).

- `host`, the hostname of your InfluxDB server. The port defaults to 8086.
- `database`, the name of the database on your InfluxDB server.
- `measurement`, the name of the measurement into which the data is saved.
- `store_fields`, a list of variables that are stored.

Variables from the RuuviTag will be stored in the database only if they appear in `store_fields`.

The possible variable names are: `temperature`, `pressure`, `humidity`, `battery`, `tx_power`, `movement_counter`,
`tagID`, `measurement_sequence_number`, `acceleration_x`, `acceleration_y`, `acceleration_z`.


## Check to see if it works

To run the code, use `poetry run python ruuvi_influx.py actual_config.toml`.
It should "just work", running forever, uploading data as it finds it. 
Press `ctrl-c` (possibly twice) to quit.

You may need to set the environmental variable `RUUVI_BLE_ADAPTER="bleson"` first.

If the program exits itself soon after starting, your bluetooth stuff is probably broken.


## Set it running as a systemd service

Edit the file `~/.config/systemd/user/ruuvi-influx.service` and add the following contents
(add the path to where you cloned this repo as the working directory):

```
[Unit]
Description=RuuviTag uploader

[Service]
WorkingDirectory=/PATH/TO/WHERE/YOU/CLONED/THIS/REPO 
ExecStart=/usr/local/bin/poetry run python ruuvi_influx.py actual_config.toml
Environment=PYTHONUNBUFFERED=1
Restart=on-failure

[Install]
WantedBy=default.target
```

Make sure the service file is executable, then run: 

- `systemctl --user start ruuvi-influx` 
- `systemctl --user --enable ruuvi-influx`


## Additional configuration

Here are some non-obligatory but important configuration options that you should also do:

### Filter Ruuvi devices based on their MAC

You can give an array called `mac_filter`, containing MAC addresses of RuuviTags. 
If it is non-empty, only the devices  whose addresses are in the list are listened to. 
If it's empty, every RuuviTag in range gets stored.

### Additional InfluxDB config

If your InfluxDB server is on a port different to the default 8086, 
you can change that by setting `port` to some integer value.

If your InfluxDB server has SSL enabled, set `ssl = true` in the config.

If your database has user authentication (as it should), set the username and password in the config file. 
I suggest you create a new user with write-only access only to the database you want to use with this script.

### InfluxDB tags

In InfluxDB, the data points from each RuuviTag will get a tag named `mac` 
with the device's MAC address as the tag value. That's not very legible, so 
additionally, you can define two mappings for more practical tags:

Under `[device-names]`, you can associate a name for each MAC address. 
If the MAC of a RuuviTag matches this list, its data gets the tag `device`, with the given value. 
You can find out the MAC addresses of your devices e.g. from the RuuviTag mobile app.

Under `[locations]`, you can define a map from the device names given above, to location names. 
If a device name matches  this list, its data will get the tag `location`, with the given value. 
This allows you to either swap a different device to a given location, or move a device to a new location. 
The `location` tag is my preferred way to arrange the data e.g. when displaying with Grafana.
