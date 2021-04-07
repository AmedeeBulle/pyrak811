#!/usr/bin/env python3
"""RAK811 OTAA demo.

Minimalistic OTAA demo

Copyright 2019, 2021 Philippe Vanhaesendonck

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
from random import randint
from sys import exit
from time import sleep

from rak811.rak811 import Mode, Rak811
from ttn_secrets import APP_EUI, APP_KEY

lora = Rak811()

# Most of the setup should happen only once...
print('Setup')
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = 'EU868'
lora.set_config(app_eui=APP_EUI,
                app_key=APP_KEY)

print('Joining')
lora.join_otaa()
# Note that DR is different from SF and depends on the region
# See: https://docs.exploratory.engineering/lora/dr_sf/
# Set Data Rate to 5 which is SF7/125kHz for EU868
lora.dr = 5

print('Sending packets every minute - Interrupt to cancel loop')
print('You can send downlinks from the TTN console')
try:
    while True:
        print('Send packet')
        # Cayenne lpp random value as analog
        lora.send(bytes.fromhex('0102{:04x}'.format(randint(0, 0x7FFF))))

        while lora.nb_downlinks:
            print('Received', lora.get_downlink()['data'].hex())

        sleep(60)
except:  # noqa: E722
    pass

print('Cleaning up')
lora.close()
exit(0)
