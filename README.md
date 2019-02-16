# RAK811 Python 3 library for Raspberry Pi
## About
RAK811 Python 3 library for use with the Raspberry Pi LoRa pHAT.

The library exposes the AT commands as described in the [RAK811 Lora AT Command User Guide V1.5](http://docs.rakwireless.com/en/LoRa/RAK811/Software_Development/RAK811%C2%A0LoRa%C2%A0AT%C2%A0Command%C2%A0V1.5.pdf).

Commands currently implemented:
- System commands
- LoRaWan commands

Not implemented yet:
- LoraP2P
- Radio
- Peripheral

## Installation
### Requirements
- A Raspberry Pi!
- A RAK811 LoRa module ([PiSupply IoT LoRa Node pHAT for Raspberry Pi ](https://uk.pi-supply.com/products/iot-lora-node-phat-for-raspberry-pi))
- On the Raspberry Pi the hardware serial port must be enabled and the serial console disabled (use `raspi-config`);
- The user running the application must be in the `dialout` and `gpio` groups.

### Library
#### From PyPI
```
# Create a virtualenv (optional)
python3 -m virtualenv -p python3 venv
source venv/bin/activate
# Install the package -- this will pull the dependencies
pip install rak811
```

#### From GitHub
```
# Clone this repository
git clone https://github.com/AmedeeBulle/pyrak811.git
cd rak811
# Create a virtualenv (optional)
python3 -m virtualenv -p python3 venv
source venv/bin/activate
# Install the package -- this will pull the dependencies
pip install .
```

## Usage
See the [example directory on GitHub](https://github.com/AmedeeBulle/rak811/tree/master/examples):
- `api_demo.py`: demo most of the API calls
- `otaa.py` example
- `abp.py` example

To run the examples, first copy the `ttn_secrets_template.py` to `ttn_secrets.py` and enter your LoRaWan [TheThingsNetwork](https://www.thethingsnetwork.org) keys.

Note: you do not need to `hard_reset` the module each time you run a script.
However you must do it the first time after a (re)boot to activate the module.
