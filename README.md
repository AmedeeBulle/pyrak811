# RAK811 Python 3 library for Raspberry Pi
## About
RAK811 Python 3 library and command-line interface for use with the Raspberry Pi LoRa pHAT.

The library exposes the AT commands as described in the [RAK811 Lora AT Command User Guide V1.5](http://docs.rakwireless.com/en/LoRa/RAK811/Software_Development/RAK811%C2%A0LoRa%C2%A0AT%C2%A0Command%C2%A0V1.5.pdf).  
The command-line interface exposes all API calls to the command line.

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

## Command-line interface
The `rak811` command exposes all library calls to the command line:

```
$ rak811 --help
Usage: rak811 [OPTIONS] COMMAND [ARGS]...

  Command line interface for the RAK811 module.

Options:
  -v, --verbose  Verbose mode
  --help         Show this message and exit.

Commands:
  abp-info    Get ABP info.
  band        Get/Set LoRaWan region.
  dr          Get/set next send data rate.
  get-config  Get LoraWan configuration.
  hard-reset  Hardware reset of the module.
  join-abp    Join the configured network in ABP mode.
  join-otaa   Join the configured network in OTAA mode.
  link-cnt    Get up & downlink counters.
  mode        Get/Set mode to LoRaWan or LoRaP2P.
  recv-ex     RSSI & SNR report on receive.
  reload      Set LoRaWan or LoRaP2P configurations to default.
  reset       Reset Module or LoRaWan stack.
  send        Send LoRaWan message and check for downlink.
  set-config  Set LoraWAN configuration.
  signal      Get (RSSI,SNR) from latest received packet.
  sleep       Enter sleep mode.
  version     Get module version.
  wake-up     Enter sleep mode.
```

Session example:
```
$ rak811 -v reset lora
LoRa reset complete.
$ rak811 -v set-config app_eui=70B3D5xxxxxxxxxx app_key=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LoRaWan parameters set
$ rak811 -v join-otaa
Joined in OTAA mode
$ rak811 -v dr
5
$ rak811 -v dr 4
Data rate set to 4.
$ rak811 -v send Hello
Message sent.
No downlink available.
$ rak811 -v send --port 4 --binary '01020211'
Message sent.
Downlink received:
Port: 1
RSSI: -56
SNR: 31
Data: 123456
```
