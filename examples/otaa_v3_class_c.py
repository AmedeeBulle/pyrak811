#!/usr/bin/env python3
"""RAK811 OTAA Class C demo.

Minimalistic OTAA demo with Class C device (v3.x firmware).

The module will wait on downlink message, run a task and send an the same data
back as uplink

The module uses receive_p2p to get out-of-band downlinks.

The device must be configured as a Class C device in your LoRaWan Application
Server (TTN/TTS).

Note that delivery of downlinks is not guaranteed:
    - Device might not receive the signal
    - The device is not listening when in send mode

Copyright 2022 Philippe Vanhaesendonck

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""
import logging
from random import randint
from sys import exit
from time import sleep
from timeit import default_timer as timer
from traceback import print_exc

from rak811.rak811_v3 import Rak811, Rak811ResponseError
from ttn_secrets import APP_EUI, APP_KEY

# Set level to logging.DEBUG for a verbose output
logging.basicConfig(level=logging.INFO)

lora = Rak811()

# Most of the setup should happen only once...
print("Setup")
# Ensure we are in LoRaWan mode / Class C
lora.set_config("lora:work_mode:0")
lora.set_config("lora:class:2")
# Select OTAA
lora.set_config("lora:join_mode:0")
# Select region
lora.set_config("lora:region:EU868")
# Set keys
lora.set_config(f"lora:app_eui:{APP_EUI}")
lora.set_config(f"lora:app_key:{APP_KEY}")
# Set data rate
# Note that DR is different from SF and depends on the region
# See: https://docs.exploratory.engineering/lora/dr_sf/
# Set Data Rate to 5 which is SF7/125kHz for EU868
lora.set_config("lora:dr:5")

# Print config
for line in lora.get_config("lora:status"):
    print(f"    {line}")

print("Joining")
start_time = timer()
lora.join()
print("Joined in {:.2f} secs".format(timer() - start_time))

print("Sending initial Hello packet")
start_time = timer()
lora.send("Hello")
print("Packet sent in {:.2f} secs".format(timer() - start_time))
print("Entering wait loop")
print("You can send downlinks from the TTN console")
try:
    while True:
        print("Waiting for downlinks...")
        try:
            lora.receive_p2p(60)
        except Rak811ResponseError as e:
            print("Error while waiting for downlink {}: {}".format(e.errno, e.strerror))
        while lora.nb_downlinks:
            data = lora.get_downlink()["data"]
            if data != b"":
                print("Downlink received", data.hex())
                # simulate some processing time
                sleep(randint(5, 10))
                print("Sending back results")
                start_time = timer()
                try:
                    lora.send(data)
                    print("Packet sent in {:.2f} secs".format(timer() - start_time))
                except Rak811ResponseError as e:
                    print("Error while sendind data {}: {}".format(e.errno, e.strerror))


except KeyboardInterrupt:
    print()
except Exception:
    print_exc()

print("Cleaning up")
lora.close()
exit(0)
