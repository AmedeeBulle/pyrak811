#!/usr/bin/env python3
"""RAK811 API demo.

Simple demo to illustrate API usage

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
from sys import exit
from time import sleep

from rak811 import Mode, RecvEx, Reset
from rak811 import Rak811, Rak811ResponseError
from ttn_secrets import APP_EUI, APP_KEY

config_keys = ('dev_addr', 'dev_eui', 'app_eui', 'app_key', 'nwks_key',
               'apps_key', 'tx_power', 'pwr_level', 'adr', 'dr', 'public_net',
               'rx_delay1', 'ch_list', 'ch_mask', 'max_chs', 'rx2',
               'join_cnt', 'nbtrans', 'retrans', 'class', 'duty')

print('Instanciate class')
lora = Rak811()

print('Hard reset board')
lora.hard_reset()

# System commands
print('Version', lora.version)

print('Sleeping')
lora.sleep()
sleep(5)
lora.wake_up()
print('Awake')

print('Reset Module')
lora.reset(Reset.Module)

print('Reset LoRa')
lora.reset(Reset.LoRa)

print('Reload')
lora.reload()

for mode in (Mode.LoRaP2P, Mode.LoRaWan):
    lora.mode = mode
    print('Mode', lora.mode)

for band in ('US915', 'EU868'):
    lora.band = band
    print('Band', lora.band)

print("Configure module")
lora.set_config(app_eui=APP_EUI,
                app_key=APP_KEY)
print("Module configuration:")
for config_key in config_keys:
    try:
        print('>>', config_key, lora.get_config(config_key))
    except Rak811ResponseError as e:
        print('>>', config_key, e.errno, e.strerror)

for recv_ex in (RecvEx.Disabled, RecvEx.Enabled):
    lora.recv_ex = recv_ex
    print('Recv ex', lora.recv_ex)

print('Join')
lora.join_otaa()

print('DR', lora.dr)
lora.dr = 5
print('DR', lora.dr)

print('Signal', lora.signal)

print('Send string')
lora.send('Hello')

print('Signal', lora.signal)

print('Link counter', lora.link_cnt)

print('ABP Info', lora.abp_info)

print('Send Confirmed (Cayenne LPP format)')
lora.send(bytes.fromhex('016700F0'), port=11, confirm=True)

print('Check for downlink messages')
while lora.nb_downlinks:
    print('>>', lora.get_downlink())

lora.close()
exit(0)
