# RAK811 Python 3 library for Raspberry Pi

[![Latest Version](https://img.shields.io/pypi/v/rak811.svg)](https://pypi.org/project/rak811/)
[![Build Status](https://travis-ci.org/AmedeeBulle/pyrak811.svg?branch=main)](https://travis-ci.org/AmedeeBulle/pyrak811)
[![codecov](https://codecov.io/gh/AmedeeBulle/pyrak811/branch/main/graph/badge.svg)](https://codecov.io/gh/AmedeeBulle/pyrak811)

## About

RAK811 Python 3 library and command-line interface for use with the Raspberry Pi LoRa pHAT.

The library exposes the RAK811 module AT commands as described in the following documents:

- [RAK811 Lora AT Command User Guide V1.5](https://github.com/AmedeeBulle/pyrak811/blob/main/DOCS/RAK811%C2%A0LoRa%C2%A0AT%C2%A0Command%C2%A0V1.5.pdf) for modules with the V2.0.x firmware.
- [RAK811 AT Command Manual V1.0](https://github.com/AmedeeBulle/pyrak811/blob/main/DOCS/RAK811_AT_Command_Manual_V1.0.pdf) for modules with the V3.0.x firmware.

The command-line interface exposes all API calls to the command line.

## Requirements

- A Raspberry Pi!
- A RAK811 LoRa module ([PiSupply IoT LoRa Node pHAT for Raspberry Pi](https://uk.pi-supply.com/products/iot-lora-node-phat-for-raspberry-pi))
- On the Raspberry Pi the hardware serial port must be enabled and the serial console disabled (use `raspi-config`)
- The user running the application must be in the `dialout` and `gpio` groups (this is the default for the `pi` user)

## Install the rak811 package

The package is installed from PyPI:

```shell
sudo pip3 install rak811
```

The `pip3` command is part of the `python3-pip` package. If it is missing on your system, run:

```shell
sudo apt-get install python3-pip
```

[PiSupply](https://uk.pi-supply.com/) provides [detailed instructions](https://learn.pi-supply.com/make/getting-started-with-the-raspberry-pi-lora-node-phat/) for configuring your Raspberry Pi.

## Usage

### Quick start with The Things Network

#### Identify your device

If you don't know the firmware level of you module run the following commands:

```shell
rak811 hard-reset
rak811 version
```

For V2.0.x firmware use the `rak811` command and python module, for V3.0.X use `rak811v3` command and `rak811_v3` python module.

#### Register your device

Register you device on [TheThingsNetwork](https://www.thethingsnetwork.org) using the unique id of your RAK811 module (Device EUI).  
You can retrieve your Device EUI with the following command (V2.0.x):

```shell
rak811 hard-reset
rak811 get-config dev_eui
```

_Note_: the `rak811 hard-reset` command is only needed once after (re)booting your Raspberry Pi to activate the module.

or (V3.0.x):

```shell
rak811v3 set-config lora:join_mode:0
rak811v3 get-config lora:status | grep DevEui
```

#### Hello World

Send your first LoRaWan message wit the following python code snippet:  
(The App EUI and App Key are copied verbatim from the TTN console)

```python
#!/usr/bin/env python3
# V2.0.x firmware
from rak811.rak811 import Mode, Rak811

lora = Rak811()
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = 'EU868'
lora.set_config(app_eui='70B3D5xxxxxxxxxx',
                app_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
lora.join_otaa()
lora.dr = 5
lora.send('Hello world')
lora.close()
```

```python
#!/usr/bin/env python3
# V3.0.x firmware
from rak811.rak811_v3 import Rak811

lora = Rak811()
lora.set_config('lora:work_mode:0')
lora.set_config('lora:join_mode:0')
lora.set_config('lora:region:EU868')
lora.set_config('lora:app_eui:70B3D5xxxxxxxxxx')
lora.set_config('lora:app_key:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
lora.join()
lora.set_config('lora:dr:5')
lora.send('Hello world')
lora.close()
```

Your first message should appear on the TTN console!

### Next steps

See the [example directory on GitHub](https://github.com/AmedeeBulle/pyrak811/tree/main/examples):

- `api_demo.py`: demo most of the V2.0.x API calls
- `otaa.py` / `otaa_v3.py`: OTAA example
- `abp.py` / `abp_v3.py`: ABP example
- `p2p.py` / `p2p_v3.py`: P2P example
- `p2p.sh` / `p2p_v3.sh`: P2P example based on the command-line interface (see below)

To run the examples, first copy the `ttn_secrets_template.py` to `ttn_secrets.py` and enter your LoRaWan [TheThingsNetwork](https://www.thethingsnetwork.org) keys.

_Note_: you do not need to `hard_reset` the module each time you run a script.
However you must do it the first time after a (re)boot to activate the module.

### balenaCloud

Sample code to use the library with [balenaCloud](https://www.balena.io/): [
Basic RAK811 example with balenaCloud](https://github.com/AmedeeBulle/pyrak811-balena) (V2.0.x firmware).

## Command-line interface

### V2.0.x firmware

The `rak811` command exposes all library calls to the command line:

```console
$ rak811 --help
Usage: rak811 [OPTIONS] COMMAND [ARGS]...

  Command line interface for the RAK811 module.

Options:
  -v, --verbose  Verbose mode
  --help         Show this message and exit.

Commands:
  abp-info            Get ABP info.
  band                Get/Set LoRaWan region.
  clear-radio-status  Clear radio statistics.
  dr                  Get/set next send data rate.
  get-config          Get LoraWan configuration.
  hard-reset          Hardware reset of the module.
  join-abp            Join the configured network in ABP mode.
  join-otaa           Join the configured network in OTAA mode.
  link-cnt            Get up & downlink counters.
  mode                Get/Set mode to LoRaWan or LoRaP2P.
  radio-status        Get radio statistics.
  recv-ex             RSSI & SNR report on receive.
  reload              Set LoRaWan or LoRaP2P configurations to default.
  reset               Reset Module or LoRaWan stack.
  send                Send LoRaWan message and check for downlink.
  set-config          Set LoraWAN configuration.
  signal              Get (RSSI,SNR) from latest received packet.
  sleep               Enter sleep mode.
  version             Get module version.
  wake-up             Wake up.
```

Session example:

```console
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

_Note_: for your first session after boot, you will need to do a `hard-reset` instead of a `reset lora` command to activate the module.

### V3.0.x firmware

The `rak811v3` command exposes the following library calls to the command line:

```console
$ rak811v3 --help
Usage: rak811v3 [OPTIONS] COMMAND [ARGS]...

  Command line interface for the RAK811 module.

Options:
  -v, --verbose  Verbose mode
  -d, --debug    Debug mode
  --version      Show the version and exit.
  --help         Show this message and exit.

Commands:
  get-config   Execute get_config RAK811 command.
  hard-reset   Hardware reset of the module.
  help         Print module help.
  join         Join the configured network.
  receive-p2p  Get LoraP2P message.
  run          Exit boot mode and enter normal mode.
  send         Send LoRaWan message and check for downlink.
  send-p2p     Send LoRa P2P message.
  send-uart    Send data to UART.
  set-config   Execute set_config RAK811 command.
  version      Get module version.
```

Session example:

```console
$ rak811v3 -v set-config lora:work_mode:0
Configuration done
LoRa (R) is a registered trademark or service mark of Semtech Corporation or its affiliates. LoRaWAN (R) is a licensed mark.
RAK811 Version:3.0.0.14.H
UART1 work mode: RUI_UART_NORMAL, 115200, N81
UART3 work mode: RUI_UART_NORMAL, 115200, N81
LoRa work mode:LoRaWAN, join_mode:OTAA, MulticastEnable: false, Class: A
$ # The following is not necessary as in this case the module is already in OTAA mode!
$ rak811v3 -v set-config lora:join_mode:0
Configuration done
$ rak811v3 -v set-config lora:app_eui:70B3D5xxxxxxxxxx
Configuration done
$ rak811v3 -v set-config lora:app_key:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Configuration done
$ rak811v3 -v join
Joined!
$ rak811v3 get-config lora:status | grep 'Current Datarate'
Current Datarate: 4
$ rak811v3 -v set-config lora:dr:5
Configuration done
$ rak811v3 -v send 'Hello'
Message sent.
No downlink available.
$ rak811v3 -v set-config lora:confirm:1
Configuration done
$ rak811v3 -v send --port 4 --binary '01020211'
Message sent.
Send confirmed.
RSSI: -66
SNR: 6
```
