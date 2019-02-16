#!/usr/bin/env python3
"""RAK811 OTAA demo.

Minimalistic OTAA demo

Copyright 2019 Philippe Vanhaesendonck

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

from rak811 import Mode, Rak811
from ttn_secrets import APPS_KEY, DEV_ADDR, NWKS_KEY

lora = Rak811()

# Most of the setup should happen only once...
print('Setup')
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = 'EU868'
lora.set_config(dev_addr=DEV_ADDR,
                apps_key=APPS_KEY,
                nwks_key=NWKS_KEY)

print('Joining')
lora.join_abp()
lora.dr = 5

print('Sending packets every minute - Interrupt to cancel loop')
print('You can send downlinks from the TTN console')
try:
    while True:
        print('Send packet')
        # Cayenne lpp random value as analog
        lora.send(bytes.fromhex('0102{:04x}'.format(randint(0, 0x7FFF))))

        while lora.nb_downlinks:
            print('Received', lora.get_downlink()['data'])

        sleep(60)
except:  # noqa
    pass

print('Cleaning up')
lora.close()
exit(0)
