"""TTN secret keys template file.

Copy this template to secrets.py and enter you keys

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

"""OTAA Template."""

"""Application EUI.
This EUI must be in big-endian format, so most-significant-byte
first.
For TTN issued EUIs the first bytes should be 0x70, 0xB3, 0xD5.
"""
APP_EUI = '70B3D50000000000'

"""Application key.
This key should be in big endian format (or, since it is not really a
number but a block of memory, endianness does not really apply). In
practice, a key taken from the TTN console can be copied as-is.
"""
APP_KEY = '00000000000000000000000000000000'

"""ABP Template."""

"""Device address.
The device address must be in big-endian format, so most-significant-byte
first.
For TTN issued addresses the first byte should be 0x26
"""
DEV_ADDR = '26000000'

"""Network Session Key.
The device address must be in big-endian format, so most-significant-byte
first.
"""
NWKS_KEY = '00000000000000000000000000000000'

"""App Session Key.
The device address must be in big-endian format, so most-significant-byte
first.
"""
APPS_KEY = '00000000000000000000000000000000'
