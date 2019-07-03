"""Interface with the RAK811 module.

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
from binascii import hexlify
from enum import IntEnum
from time import sleep

from RPi import GPIO

from .exception import Rak811Error
from .serial import Rak811Serial, Rak811TimeoutError

RESET_BCM_PORT = 17
RESET_DELAY = 0.01
RESET_POST = 2
RESPONSE_OK = 'OK'
RESPONSE_ERROR = 'ERROR'
RESPONSE_EVENT = 'at+recv='


# RAK811 error codes and associated messages
class ErrorCode(IntEnum):
    """AT commands error codes."""

    ARG_ERR = -1
    ARG_NOT_FIND = -2
    JOIN_ABP_ERR = -3
    JOIN_OTAA_ERR = -4
    NOT_JOIN = -5
    MAC_BUSY_ERR = -6
    TX_ERR = -7
    INTER_ERR = -8
    WR_CFG_ERR = -11
    RD_CFG_ERR = -12
    TX_LEN_LIMITE_ERR = -13
    UNKNOWN_ERR = -20


ERROR_MESSAGE = {
    ErrorCode.ARG_ERR: 'Invalid argument',
    ErrorCode.ARG_NOT_FIND: 'Argument not found',
    ErrorCode.JOIN_ABP_ERR: 'ABP join error',
    ErrorCode.JOIN_OTAA_ERR: 'OTAA join error',
    ErrorCode.NOT_JOIN: 'Not joined',
    ErrorCode.MAC_BUSY_ERR: 'MAC busy',
    ErrorCode.TX_ERR: 'Transmit error',
    ErrorCode.INTER_ERR: 'Inter error',
    ErrorCode.WR_CFG_ERR: 'Write configuration error',
    ErrorCode.RD_CFG_ERR: 'Read configuration Error',
    ErrorCode.TX_LEN_LIMITE_ERR: 'Transmit len limit error',
    ErrorCode.UNKNOWN_ERR: 'Unknown error',
}


class EventCode(IntEnum):
    """AT commands event codes."""

    RECV_DATA = 0
    TX_COMFIRMED = 1
    TX_UNCOMFIRMED = 2
    JOINED_SUCCESS = 3
    JOINED_FAILED = 4
    TX_TIMEOUT = 5
    RX2_TIMEOUT = 6
    DOWNLINK_REPEATED = 7
    WAKE_UP = 8
    P2PTX_COMPLETE = 9
    UNKNOWN = 100


EVENT_MESSAGE = {
    EventCode.RECV_DATA: 'Received data',
    EventCode.TX_COMFIRMED: 'Tx confirmed',
    EventCode.TX_UNCOMFIRMED: 'Tx unconfirmed',
    EventCode.JOINED_SUCCESS: 'Join succeded',
    EventCode.JOINED_FAILED: 'Join failed',
    EventCode.TX_TIMEOUT: 'Tx timeout',
    EventCode.RX2_TIMEOUT: 'Rx2 timeout',
    EventCode.DOWNLINK_REPEATED: 'Downlink repeated',
    EventCode.WAKE_UP: 'Wake up',
    EventCode.P2PTX_COMPLETE: 'P2P tx complete',
    EventCode.UNKNOWN: 'Unknown',
}


class Mode(IntEnum):
    """Module operation mode (LoRaWan or Peer to Peer)."""

    LoRaWan = 0
    LoRaP2P = 1


class Reset(IntEnum):
    """Module reset type."""

    Module = 0
    LoRa = 1


class RecvEx(IntEnum):
    """Receive RSSI/SNR data with downlink packets."""

    Enabled = 0
    Disabled = 1


class Rak811ResponseError(Rak811Error):
    """Exception raised by response from the module.

    Attributes:
        errno -- as returned by the module
        strerror -- textual representation

    """

    def __init__(self, code):
        """Just assign return codes."""
        try:
            self.errno = int(code)
        except ValueError:
            self.errno = code

        if self.errno in ERROR_MESSAGE:
            self.strerror = ERROR_MESSAGE[self.errno]
        else:
            self.strerror = ERROR_MESSAGE[ErrorCode.UNKNOWN_ERR]
        super().__init__(('[Errno {}] {}').format(self.errno, self.strerror))


class Rak811EventError(Rak811Error):
    """Exception raised by module events.

    Attributes:
        errno  -- as returned by the module
        strerror -- textual representation

    """

    def __init__(self, status):
        """Just assign return status."""
        try:
            self.errno = int(status)
        except ValueError:
            self.errno = status

        if self.errno in EVENT_MESSAGE:
            self.strerror = EVENT_MESSAGE[self.errno]
        else:
            self.strerror = EVENT_MESSAGE[EventCode.UNKNOWN]
        super().__init__(('[Errno {}] {}').format(self.errno, self.strerror))


class Rak811(object):
    """Main class."""

    def __init__(self, **kwargs):
        """Initialise class.

        The serial port is immediately opened and flushed.
        All parameters are optional and passed to RackSerial.
        """
        self._serial = Rak811Serial(**kwargs)
        self._downlink = []

    def close(self):
        """Terminates session.

        Terminates read thread and close serial port.
        """
        self._serial.close()

    def hard_reset(self):
        """Hard reset of the RAK811 module.

        Hard reset should not be required in normal operation. It needs to be
        issued once after host boot, or module restart.
        Note that we do not cleanup() as the reset port should stay high (it is
        configured that way at boot time).
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RESET_BCM_PORT, GPIO.OUT)
        GPIO.output(RESET_BCM_PORT, GPIO.LOW)
        sleep(RESET_DELAY)
        GPIO.output(RESET_BCM_PORT, GPIO.HIGH)
        sleep(RESET_POST)

    def _int(self, i):
        """Attempt int conversion."""
        try:
            i = int(i)
        except ValueError:
            pass
        return i

    def _send_string(self, string):
        """Send string to the RAK811 module."""
        self._serial.send_string(string)

    def _send_command(self, command):
        """Send AT command to the RAK811 module and return the response.

        Rak811ResponseError exception is raised if the command returns an
        error.
        This is a "blocking" call: if the module does not respond
        Rack811TimeoutError will be raised.
        """
        self._serial.send_command(command)
        response = self._serial.get_response()

        # Ignore events received while waiting on command feedback
        while response.startswith(RESPONSE_EVENT):
            response = self._serial.get_response()

        if response.startswith(RESPONSE_OK):
            response = response[len(RESPONSE_OK):]
        elif response.startswith(RESPONSE_ERROR):
            raise Rak811ResponseError(response[len(RESPONSE_ERROR):])
        else:
            raise Rak811ResponseError(response)

        return response

    def _get_events(self, timeout=None):
        """Get events from the RAK811 module.

        This is a "blocking" call: it will either return a list of events or
        raise a Rack811TimeoutError.
        """
        return [i[len(RESPONSE_EVENT):] for i in
                self._serial.get_events(timeout)]

    """System commands."""

    @property
    def version(self):
        """Get module version."""
        return(self._send_command('version'))

    def sleep(self):
        """Enter sleep mode."""
        self._send_command('sleep')

    def wake_up(self):
        """Wake up the RAK811 module.

        We just send a character and wait for an event as response
        """
        self._send_string('*')
        self._get_events()

    def reset(self, mode):
        """Reset Module or LoRaWan stack.

        Note that reset(Reset.Module) will restart the module which will wait
        for an hardware reset to start.
        """
        self._send_command('reset={0}'.format(mode))
        if mode == Reset.Module:
            self.hard_reset()

    def reload(self):
        """Set LoraWan or LoraP2P configurations to default."""
        self._send_command('reload')

    @property
    def mode(self):
        """Get module Mode (LoRaWan or LoRaP2P)."""
        return(self._int(self._send_command('mode')))

    @mode.setter
    def mode(self, value):
        """Set module in LoRaWan or LoRaP2P Mode."""
        self._send_command('mode={0}'.format(value))

    @property
    def recv_ex(self):
        """Get RSSI & SNR report on receive flag (Enabled/Disabled)."""
        return(self._int(self._send_command('recv_ex')))

    @recv_ex.setter
    def recv_ex(self, value):
        """Set RSSI & SNR report on receive flag (Enabled/Disabled)."""
        self._send_command('recv_ex={0}'.format(value))

    """ LoRaWan commands."""

    def set_config(self, **kwargs):
        """Set LoraWan configuration.

        Parameters are specified a key/value pairs, and are passed directly to
        the module.

        E.g.: set_config(app_eui='0000000000000000',
                         app_key='00000000000000000000000000000000',
                         adr='on')

        The module saves relevant data in EEPROM, it is not necessary to set
        values for each session.

        The following parameters are accepted by the module:
            dev_addr: device address (4 bytes hex number)
            dev_eui: device EUI (8 bytes hex number, default derived from the
                MCU's UUID
            app_eui: app EUI (8 bytes hex number)
            app_key: app key (16 bytes hex number)
            apps_key: application session key (16 bytes hex number)
            nwks_key: network session key (16 bytes hex number)
            tx_power: transmit power (in dBm -- deprecated, use pwr_level)
            pwr_level: transmit power (0-7 for EU868, region specific)
            adr: adr flag (on/off)
            dr: data rate (0-7 for EU868, region specific)
            public_net: public_net flag (on/off)
            rx_delay1: rx1 delay (0-65535 milliseconds)
            ch_list: channel list, see RAK documentation
            ch_mask: channel mask, see RAK documentation
            max_chs: max channels used in the region (read-only)
            rx2: rx2 data rate and frequency
            join_cnt: join count for OTAA joins (number, region specific)
            nbtrans: number of transmissions for unconfirmed uplink message
                (1-15, default 1)
            retrans: number of retransmissions for confirmed uplink message
                (1-255, default 8)
            class: LoRa class (0: A, 2: C)
            duty: respect duty cycle flag (on/off)
        """
        self._send_command('set_config='
                           + '&'.join([':'.join(str(val) for val in kv)
                                       for kv in kwargs.items()]))

    def get_config(self, key):
        """Get LoraWan configuration from EEPROM.

        The parameter must be a key from the above list.

        Note: get_config returns always strings, no integer do avoid unwanted
        conversion for keys.
        """
        return self._send_command('get_config={0}'.format(key))

    @property
    def band(self):
        """Get LoRaWan region.

        Region is one of: EU868, US915, AU915, KR920, AS923, IN865.
        """
        return(self._send_command('band'))

    @band.setter
    def band(self, region):
        """Set LoRaWan region.

        Region must be one of: EU868, US915, AU915, KR920, AS923, IN865.
        """
        self._send_command('band={0}'.format(region))

    def join_abp(self):
        """Join the configured network in ABP mode.

        ABP requires the following parameters to be set prior join:
            - dev_addr
            - nwks_key
            - apps_key
        """
        self._send_command('join=abp')

    def join_otaa(self):
        """Join the configured network in OTAA mode.

        OTAA requires the following parameters to be set prior join:
            - dev_eui
            - app_eui
            - app_key

        This call is "blocking", it will return only after the join completes.
        The following exceptions can be raised:
            - Rak811TimeoutError: join didn't succeed in time
            - Rak811EventError: join failed
        """
        self._send_command('join=otaa')
        # Waiting join completion
        for event in self._get_events():
            status = event.split(',')[0]
            status = self._int(status)
            if status != EventCode.JOINED_SUCCESS:
                raise Rak811EventError(status)

    @property
    def signal(self):
        """Get (RSSI,SNR) from latest received packet."""
        return(tuple(self._int(i)
                     for i in self._send_command('signal').split(',')))

    @property
    def dr(self):
        """Get next send data rate."""
        return(self._int(self._send_command('dr')))

    @dr.setter
    def dr(self, value):
        """Set next send data rate."""
        self._send_command('dr={0}'.format(value))

    @property
    def link_cnt(self):
        """Get up & downlink counters.

        Counters are 32 bits integers in decimal format.
        """
        return(tuple(self._int(i)
               for i in self._send_command('link_cnt').split(',')))

    @link_cnt.setter
    def link_cnt(self, value):
        """Set up & downlink counters.

        Counters are 32 bits integers in decimal format.
        """
        self._send_command('link_cnt=' + ','.join(str(val) for val in value))

    @property
    def abp_info(self):
        """Get ABP info.

        When using OTAA, returns the necessary info to re-join in ABP mode. The
        following tuple is returned:
            (NetworkID, DevAddr, Nwkskey, Appskey)
        """
        return(tuple(self._send_command('abp_info').split(',')))

    def _add_downlink(self, event):
        """Add message to the downlink list.

        Event is a list: (<port>[,<rssi>][,<snr>],<len>[,<data>])
        """
        r_port = self._int(event.pop(0))
        if len(event) > 2:
            r_rssi = self._int(event.pop(0))
            r_snr = self._int(event.pop(0))
        else:
            r_rssi = 0
            r_snr = 0
        r_len = self._int(event.pop(0))
        if r_len > 0:
            try:
                r_data = bytes.fromhex(event[0])
            except ValueError:
                r_data = ''
        else:
            r_data = ''
        self._downlink.append(
            {
                'port': r_port,
                'rssi': r_rssi,
                'snr': r_snr,
                'len': r_len,
                'data': r_data,
            }
        )

    def _process_events(self, timeout=None):
        """Process module event queue.

        Process event queue looking for incoming (downlink) messages. Raise
        errors when unexpected events are encountered.

        Parameter:
            timeout: maximum time to wait for event

        """
        events = self._get_events(timeout)
        # Check for downlink
        for event in events:
            # Format: <status >,<port>[,<rssi>][,<snr>],<len>[,<data>]
            event_items = event.split(',')
            status = event_items.pop(0)
            status = self._int(status)
            if status == EventCode.RECV_DATA:
                self._add_downlink(event_items)
        # Check for errors
        for event in events:
            status = event.split(',')[0]
            status = self._int(status)
            if status not in (EventCode.RECV_DATA,
                              EventCode.TX_COMFIRMED,
                              EventCode.TX_UNCOMFIRMED):
                raise Rak811EventError(status)

    def send(self, data, confirm=False, port=1):
        """Send LoRaWan message.

        Parameters:
            data: data to be sent. If the datatype is bytes it will be send
                as such. Strings will be converted to bytes.
            confirm: regular or confirmed send.
            port: port number to use (1-223)

        """
        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        self._send_command('send=' + ','.join((
            ('1' if confirm else '0'),
            str(port),
            data
        )))

        # Process events
        self._process_events()

    @property
    def nb_downlinks(self):
        """Get the number of downlink messages in the receive buffer."""
        return len(self._downlink)

    def get_downlink(self):
        """Get a downlink message from the receive buffer.

        Returns a dictionary with the following keys:
            port: port number
            rssi: RSSI (0 if recv_ex was disabled)
            snr: SNR (0 if recv_ex was disabled)
            len: data length
            data: data itself
        """
        if len(self._downlink) == 0:
            return None
        else:
            return self._downlink.pop(0)

    """ LoraP2P commands."""

    def _get_rf_config(self):
        """Get LoraP2P configuration.

        Return a dictionary.
        """
        config = tuple(self._int(i)
                       for i in self._send_command('rf_config').split(','))
        return {
            'freq': config[0] / 1000 / 1000,
            'sf': config[1],
            'bw': config[2],
            'cr': config[3],
            'prlen': config[4],
            'pwr': config[5]
        }

    @property
    def rf_config(self):
        """Get LoraP2P configuration.

        Return a dictionary.
        """
        return self._get_rf_config()

    @rf_config.setter
    def rf_config(self, config):
        """Set LoraWan P2P RF configuration parameters.

        Parameters are specified a key/value pairs, default are used for
        missing parameters.

        E.g.:
            rf_config = {
                'freq': 868.700,
                'sf': 7,
                'bw': 0
            }

        The module saves parameters to flash, it is not necessary to set
        values for each session.

        The following parameters can be set; only specified parameters are
        changed, others are kept to their previous value. Values between
        parentheses are RAK defaults.
            freq: frequency in Mhz, range 860.000-929.900 Mhz (868.100)
            sf: spread factor, range 6-12 (12)
            bw: band width, values 0:125KHz, 1:250KHz, 2:500KHz (0)
            cr: coding rate, values 1:4/5, 2:4/6, 3:4/7, 4:4/8 (1)
            prlen: preamble len, range 8-65536 (8)
            pwr: transmit power, range 5,20 (20)
        """
        base_config = self._get_rf_config()
        base_config.update(config)
        self._send_command(
            'rf_config={0},{1},{2},{3},{4},{5}'.format(
                int(base_config['freq'] * 1000 * 1000),
                base_config['sf'],
                base_config['bw'],
                base_config['cr'],
                base_config['prlen'],
                base_config['pwr']
            )
        )

    def txc(self, data, cnt=1, interval=60):
        """Send LoraP2P message.

        Send data using the pre-set RF parameters.
        For RF testing cnt can be specified to send data multiple time.
        The module will stop sending messages after cnt messages or whent it
        receives a tx_stop command.
        The method returns after all messages have been sent.

        Parameters:
            data: data to be sent. If the datatype is bytes it will be send
                as such. Strings will be converted to bytes.
            cnt: send message cnt times
            interval: when sending multiple times, interval in seconds
            beween each message.

        """
        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        self._send_command('txc=' + ','.join((
            str(cnt),
            str(interval * 1000),
            data
        )))

        # Process events
        events = self._get_events((cnt * (interval + 10)) - interval)
        # Check for errors
        for event in events:
            status = event.split(',')[0]
            status = self._int(status)
            if status != EventCode.P2PTX_COMPLETE:
                raise Rak811EventError(status)

    def rxc(self, report_en=1):
        """Set module in LoraP2P receive mode.

        Module is put in receive mode until an rx_stop command is issued.
        Method will return immediately after the command is acknowledged (it
        does not wait for data)

        Parameter:
            report_en: set to 1 by default. Can be set to 0 for RF testing
            (documentation is not clear about this)
        """
        self._send_command('rxc=' + str(report_en))

    def tx_stop(self):
        """Stop LoraP2P TX.

        Stop LoraP2P transmission; radio will switch to sleep mode.
        """
        self._send_command('tx_stop')

    def rx_stop(self):
        """Stop LoraP2P RX.

        Stop LoraP2P reception; radio will switch to sleep mode.
        """
        self._send_command('rx_stop')

    def rx_get(self, timeout):
        """Get LoraP2P message.

        This is a blocking call: wait until we receive a message or we reach a
        timeout.

        The downlink receive buffer is populated, actual data is retrieved with
        get_downlink().
        """
        try:
            self._process_events(timeout)
        except Rak811TimeoutError:
            pass

    """Radio commands."""

    @property
    def radio_status(self):
        """Get radio statistics.

        Return a tuple: (TxSuccessCnt, TxErrCnt, RxSuccessCnt, RxTimeOutCnt,
                         RxErrCnt, Rssi, Snr)
        """
        return(tuple(self._int(i)
               for i in self._send_command('status').split(',')))

    def clear_radio_status(self):
        """Clear radio statistics."""
        self._send_command('status=0')
