#!/usr/bin/env python3
"""RAK811 P2P demo.

Send counter messages at random interval and listen the rest of the time.

Start this script on 2 or more nodes an observe the packets flowing.

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
from time import time

from rak811 import Mode, Rak811

# Send packet every P2P_BASE + (0..P2P_RANDOM) seconds
P2P_BASE = 30
P2P_RANDOM = 60

# Magic key to recognize our messages
P2P_MAGIC = b'\xca\xfe'

lora = Rak811()

# Most of the setup should happen only once...
print('Setup')
lora.hard_reset()
lora.mode = Mode.LoRaP2P

# RF configuration
# - Avoid LoRaWan channels (You will get quite a lot of spurious packets!)
# - Respect local regulation (frequency, power, duty cycle)
lora.rf_config = {
    'sf': 7,
    'freq': 869.800,
    'pwr': 16
}

print('Entering send/receive loop')
counter = 0
try:
    while True:
        # Calculate next message send timestamp
        next_send = time() + P2P_BASE + randint(0, P2P_RANDOM)
        # Set module in receive mode
        lora.rxc()
        # Loop until we reach the next send time
        while time() < next_send:
            wait_time = next_send - time()
            print('Waiting on message for {:0.0f} seconds'.format(wait_time))
            # Note that you don't have to listen actively for capturing message
            # Once in receive mode, the library will capure all messages sent.
            lora.rx_get(wait_time)
            while lora.nb_downlinks > 0:
                message = lora.get_downlink()
                data = message['data']
                if data[:len(P2P_MAGIC)] == P2P_MAGIC:
                    print(
                        'Receveid message: {}'.format(
                            int.from_bytes(data[len(P2P_MAGIC):],
                                           byteorder='big')
                        )
                    )
                    print('RSSI: {}, SNR: {}'.format(message['rssi'],
                                                     message['snr']))
                else:
                    print('Foreign message received')
        # Time to send message
        # Exit receive mode
        lora.rx_stop()
        counter += 1
        print('Send message {}'.format(counter))
        lora.txc(P2P_MAGIC + bytes.fromhex('{:08x}'.format(counter)))

except:  # noqa: E722
    pass

print('All done')
exit(0)
