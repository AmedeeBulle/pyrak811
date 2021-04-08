"""Units tests for the Rak811 class (V3 firmware).

Rak811Serial is tested separately and therefore mocked in this suite.

RPi.GPIO is completely ignored as not available on all platforms, and its use
by the Rak811 class very limited.
"""
from mock import Mock, patch
from pytest import fixture, raises
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811.rak811_v3 import EVENT_TIMEOUT, RESPONSE_TIMEOUT  # noqa: E402
from rak811.rak811_v3 import Rak811, Rak811ResponseError  # noqa: E402
from rak811.rak811_v3 import Rak811Serial  # noqa: E402
from rak811.serial import Rak811TimeoutError  # noqa: E402


@fixture
def lora():
    """Instantiate Rak811 class though fixture."""
    with patch('rak811.rak811_v3.Rak811Serial', autospec=True):
        rak811 = Rak811()
        yield rak811
        rak811.close()


@patch('rak811.rak811_v3.Rak811Serial', autospec=True)
def test_instantiate_default(mock_serial):
    """Test that Rak811 can be instantiated.

    Check for basic initialisation and teardown of the RackSerial.
    """
    lora = Rak811()

    assert isinstance(lora._serial, Rak811Serial)
    mock_serial.assert_called_once_with(
        keep_untagged=True,
        read_buffer_timeout=RESPONSE_TIMEOUT
    )
    lora.close()
    mock_serial.return_value.close.assert_called_once()


@patch('rak811.rak811_v3.Rak811Serial', autospec=True)
def test_instantiate_params(mock_serial):
    """Test that Rak811 passes parameters passed to RackSerial."""
    port = '/dev/ttyAMA0'
    timeout = 5
    lora = Rak811(port=port, timeout=timeout)
    mock_serial.assert_called_once_with(
        keep_untagged=True,
        read_buffer_timeout=RESPONSE_TIMEOUT,
        port=port,
        timeout=timeout
    )
    lora.close()


@patch('rak811.rak811_v3.GPIO')
@patch('rak811.rak811_v3.sleep')
def test_hard_reset(mock_sleep, mock_gpio, lora):
    """Test hard_reset().

    Test is a bit pointless, at least ensures it runs...
    """
    lora.hard_reset()
    mock_gpio.setup.assert_called_once()
    mock_gpio.cleanup.assert_not_called()


def test_int(lora):
    """Test _int function."""
    assert lora._int(1) == 1
    assert lora._int('1') == 1
    assert lora._int('Hello') == 'Hello'


def test_send_string(lora):
    """Test _send_string (passthrough to RackSerial)."""
    lora._send_string('Hello')
    lora._serial.send_string.assert_called_with('Hello')


def test_send_command(lora):
    """Test _send_command."""
    # Successful command
    lora._serial.receive.return_value = 'OK V3.0.0.14.H'
    assert lora._send_command('version') == 'V3.0.0.14.H'
    lora._serial.send_command.assert_called_with('version')

    # Error
    lora._serial.receive.return_value = 'ERROR: 2'
    with raises(Rak811ResponseError,
                match='2'):
        lora._send_command('set_config=lora:work_mode:5')

    # Unexpected data  response queue
    lora._serial.receive.side_effect = [
        'Unexpected',
        'OK V3.0.0.14.H',
    ]
    assert lora._send_command('version') == 'V3.0.0.14.H'

    # Multi-line response with "Initialization OK "
    lora._serial.receive.side_effect = [
        'RAK811 Version:3.0.0.14.H',
        'LoRa work mode:LoRaWAN, join_mode:OTAA, MulticastEnable: false, Class: A',
        'Initialization OK '
    ]
    assert lora._send_command('set_config=device:restart') == ' '


def test_send_command_list(lora):
    """Test _send_command_list."""
    # OK message
    lora._serial.receive.return_value = [
        'OK Device AT commands:',
        '  at+version',
        '  at+send=lorap2p:XXX'
    ]
    assert lora._send_command_list('help') == [
        'Device AT commands:',
        '  at+version',
        '  at+send=lorap2p:XXX'
    ]

    # "Initialization OK "
    lora._serial.receive.return_value = [
        'RAK811 Version:3.0.0.14.H',
        'LoRa work mode:LoRaWAN, join_mode:OTAA, MulticastEnable: false, Class: A',
        'Initialization OK '
    ]
    assert lora._send_command_list('set_config=device:restart') == [
        'RAK811 Version:3.0.0.14.H',
        'LoRa work mode:LoRaWAN, join_mode:OTAA, MulticastEnable: false, Class: A',
        ' '
    ]

    # Error
    lora._serial.receive.return_value = ['ERROR: 1']
    with raises(Rak811ResponseError,
                match='1'):
        lora._send_command_list('set_config=device:status')


def test_get_events(lora):
    """Test _get_events."""
    # Successful command
    lora._serial.receive.return_value = [
        'at+recv=0,-68,7,0',
        'at+recv=1,-65,6,2:4865',
    ]
    events = lora._get_events()
    assert events.pop() == '1,-65,6,2:4865'
    assert events.pop() == '0,-68,7,0'


"""AT command API.

For the sake of simplicity we mock Rak811._send_command,
Rak811._send_command_list and Rack811._get_events, as these have already been
tested.
"""


@patch.object(Rak811, '_send_command_list', return_value=[' '])
def test_set_config_simple(mock_send, lora):
    """Test set_config command (simple case)."""
    assert lora.set_config('lora:region:EU868') == [' ']
    mock_send.assert_called_once_with('set_config=lora:region:EU868')


@patch.object(Rak811, '_send_command_list', return_value=[' ', ' <BOOT MODE>'])
def test_set_config_boot(mock_send, lora):
    """Test set_config command (Boot case)."""
    assert lora.set_config('device:boot') == [' ', ' <BOOT MODE>']
    mock_send.assert_called_once_with('set_config=device:boot')


@patch.object(Rak811, '_send_command_list', return_value=['LoRa work mode:LoRaWAN', ' '])
def test_set_config_init(mock_send, lora):
    """Test set_config command (Initialization OK case)."""
    assert lora.set_config('lora:work_mode:0') == ['LoRa work mode:LoRaWAN', ' ']
    mock_send.assert_called_once_with('set_config=lora:work_mode:0')


@patch.object(Rak811, '_send_command_list', return_value=['1'])
def test_get_config_simple(mock_send, lora):
    """Test get_config command (simple case)."""
    assert lora.get_config('device:gpio:2') == ['1']
    mock_send.assert_called_once_with('get_config=device:gpio:2')


@patch.object(Rak811, '_send_command_list', return_value=['Work Mode: LoRaWAN', 'DownLinkCounter: 0'])
def test_get_config_multi(mock_send, lora):
    """Test get_config command (Multiple lines)."""
    assert lora.get_config('lora:status') == ['Work Mode: LoRaWAN', 'DownLinkCounter: 0']
    mock_send.assert_called_once_with('get_config=lora:status')


@patch.object(Rak811, '_send_command', return_value='V3.0.0.14.H')
def test_version(mock_send, lora):
    """Test version command."""
    assert lora.version == 'V3.0.0.14.H'
    mock_send.assert_called_once_with('version')


@patch.object(Rak811, '_send_command_list', return_value=['Device AT commands:', '  at+send=lorap2p:XXX'])
def test_help(mock_send, lora):
    """Test help command."""
    assert lora.help == ['Device AT commands:', '  at+send=lorap2p:XXX']
    mock_send.assert_called_once_with('help')


@patch.object(Rak811, '_send_command')
def test_run(mock_send, lora):
    """Test run command."""
    lora.run()
    mock_send.assert_called_once_with('run')


@patch.object(Rak811, '_send_command')
def test_join(mock_send, lora):
    """Test join command."""
    lora.join()
    mock_send.assert_called_once_with('join', timeout=EVENT_TIMEOUT)


@patch.object(Rak811, '_get_events')
@patch.object(Rak811, '_send_command')
def test_get_send_unconfirmed(mock_send, mock_events, lora):
    """Test send, unconfirmed."""
    mock_events.side_effect = Rak811TimeoutError()
    lora.send('Hello')
    mock_send.assert_called_once_with('send=lora:1:48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 0


@patch.object(Rak811, '_get_events', return_value=['0,-68,7,0'])
@patch.object(Rak811, '_send_command')
def test_get_send_confirmed(mock_send, mock_events, lora):
    """Test send, unconfirmed."""
    lora.send('Hello')
    mock_send.assert_called_once_with('send=lora:1:48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 1
    assert lora.get_downlink() == {
        'port': 0,
        'rssi': -68,
        'snr': 7,
        'len': 0,
        'data': '',
    }


@patch.object(Rak811, '_get_events', return_value=['1,-67,8,3:313233'])
@patch.object(Rak811, '_send_command')
def test_get_send_downlink(mock_send, mock_events, lora):
    """Test send, unconfirmed."""
    lora.send('Hello')
    mock_send.assert_called_once_with('send=lora:1:48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 1
    assert lora.get_downlink() == {
        'port': 1,
        'rssi': -67,
        'snr': 8,
        'len': 3,
        'data': bytes.fromhex('313233'),
    }
