"""Units tests for the Rak811 class.

Rak811Serial is tested separately and therefore mocked in this suite.

RPi.GPIO is completely ignored as not available on all platforms, and its use
by the Rak811 class very limited.
"""
from mock import Mock, patch
from pytest import raises
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811 import Rak811, Rak811EventError, Rak811ResponseError # noqa
from rak811.rak811 import Rak811Serial # noqa
from rak811.rak811 import Mode, RecvEx, Reset # noqa


@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_instantiate_default(mock_serial):
    """Test that Rak811 can be instantiated.

    Check for basic initialisation and teardown of the RackSerial.
    """
    lora = Rak811()

    assert isinstance(lora._serial, Rak811Serial)
    mock_serial.assert_called_once_with()
    lora.close()
    mock_serial.return_value.close.assert_called_once()


@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_instantiate_params(mock_serial):
    """Test that Rak811 passes parameters passed to RackSerial."""
    port = '/dev/ttyAMA0'
    timeout = 5
    lora = Rak811(port=port, timeout=timeout)
    mock_serial.assert_called_once_with(port=port, timeout=timeout)
    lora.close()


@patch('rak811.rak811.GPIO')
@patch('rak811.rak811.sleep')
@patch('rak811.rak811.Rak811Serial')
def test_hard_reset(mock_serial, mock_sleep, mock_gpio):
    """Test hard_reset().

    Test is a bit pointless, at least ensures it runs...
    """
    lora = Rak811()
    lora.hard_reset()
    mock_gpio.setup.assert_called_once()
    mock_gpio.cleanup.assert_not_called()
    lora.close()


@patch('rak811.rak811.Rak811Serial')
def test_int(mock_serial):
    """Test _int function."""
    lora = Rak811()
    assert lora._int(1) == 1
    assert lora._int('1') == 1
    assert lora._int('Hello') == 'Hello'
    lora.close()


@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_send_string(mock_serial):
    """Test _send_string (passthrough to RackSerial)."""
    lora = Rak811()
    lora._send_string('Hello')
    lora._serial.send_string.assert_called_with('Hello')
    lora.close()


@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_send_command(mock_serial):
    """Test _send_command."""
    lora = Rak811()

    # Successful command
    lora._serial.get_response.return_value = 'OK0'
    assert lora._send_command('dr') == '0'
    lora._serial.send_command.assert_called_with('dr')

    # Error
    lora._serial.get_response.return_value = 'ERROR-1'
    with raises(Rak811ResponseError,
                match='-1'):
        lora._send_command('mode=2')

    # Unknown error
    lora._serial.get_response.return_value = 'Unexpected'
    with raises(Rak811ResponseError,
                match='Unexpected'):
        lora._send_command('mode=2')

    lora.close()


@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_events(mock_serial):
    """Test _get_events."""
    lora = Rak811()

    # Successful command
    lora._serial.get_events.return_value = [
        'at+recv=2,0,0',
        'at+recv=0,1,0,0,1,55',
    ]
    events = lora._get_events()
    assert events.pop() == '0,1,0,0,1,55'
    assert events.pop() == '2,0,0'

    lora.close()


"""AT command API.

For the sake of simplicity we mock Rak811.__send_command and
Tack811._get_events, as these have already been tested.
"""


@patch.object(Rak811, '_send_command', return_value='2.0.3.0')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_version(mock_serial, mock_send):
    """Test version command."""
    lora = Rak811()
    assert lora.version == '2.0.3.0'
    mock_send.assert_called_once_with('version')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_sleep(mock_serial, mock_send):
    """Test sleep command."""
    lora = Rak811()
    lora.sleep()
    mock_send.assert_called_once_with('sleep')
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['8,0,0'])
@patch.object(Rak811, '_send_string')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_wake_up(mock_serial, mock_send, mock_events):
    """Test wake_up command."""
    lora = Rak811()
    lora.wake_up()
    mock_send.assert_called_once()
    mock_events.assert_called_once()
    lora.close()


@patch.object(Rak811, 'hard_reset')
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_reset_module(mock_serial, mock_send, mock_hard_reset):
    """Test reset module command."""
    lora = Rak811()
    lora.reset(Reset.Module)
    mock_send.assert_called_once_with('reset=0')
    mock_hard_reset.assert_called_once()
    lora.close()


@patch.object(Rak811, 'hard_reset')
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_reset_lora(mock_serial, mock_send, mock_hard_reset):
    """Test reset lora command."""
    lora = Rak811()
    lora.reset(Reset.LoRa)
    mock_send.assert_called_once_with('reset=1')
    mock_hard_reset.assert_not_called()
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_reload(mock_serial, mock_send):
    """Test reload command."""
    lora = Rak811()
    lora.reload()
    mock_send.assert_called_once_with('reload')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_mode(mock_serial, mock_send):
    """Test mode setter."""
    lora = Rak811()
    lora.mode = Mode.LoRaWan
    mock_send.assert_called_once_with('mode=0')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='0')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_mode(mock_serial, mock_send):
    """Test mode getter."""
    lora = Rak811()
    assert lora.mode == 0
    mock_send.assert_called_once_with('mode')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_recv_ex(mock_serial, mock_send):
    """Test recv_ex setter."""
    lora = Rak811()
    lora.recv_ex = RecvEx.Disabled
    mock_send.assert_called_once_with('recv_ex=1')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='1')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_recv_ex(mock_serial, mock_send):
    """Test recv_ex getter."""
    lora = Rak811()
    assert lora.recv_ex == 1
    mock_send.assert_called_once_with('recv_ex')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_config(mock_serial, mock_send):
    """Test config setter."""
    lora = Rak811()
    lora.set_config(adr='on', dr=5)
    mock_send.assert_called_once_with('set_config=adr:on&dr:5')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='1')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_config(mock_serial, mock_send):
    """Test config getter."""
    lora = Rak811()
    assert lora.get_config('dr') == '1'
    mock_send.assert_called_once_with('get_config=dr')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_band(mock_serial, mock_send):
    """Test band setter."""
    lora = Rak811()
    lora.band = 'EU868'
    mock_send.assert_called_once_with('band=EU868')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='EU868')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_band(mock_serial, mock_send):
    """Test band getter."""
    lora = Rak811()
    assert lora.band == 'EU868'
    mock_send.assert_called_once_with('band')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_join_abp(mock_serial, mock_send):
    """Test join_abp command."""
    lora = Rak811()
    lora.join_abp()
    mock_send.assert_called_once_with('join=abp')
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['3,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_join_otaa_success(mock_serial, mock_send, mock_events):
    """Test join_abp command, successful."""
    lora = Rak811()
    lora.join_otaa()
    mock_send.assert_called_once_with('join=otaa')
    mock_events.assert_called_once()
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['4,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_join_otaa_failure(mock_serial, mock_send, mock_events):
    """Test join_abp command, failure."""
    lora = Rak811()
    with raises(Rak811EventError,
                match='4'):
        lora.join_otaa()
    mock_send.assert_called_once_with('join=otaa')
    mock_events.assert_called_once()
    lora.close()


@patch.object(Rak811, '_send_command', return_value='-30,26')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_signal(mock_serial, mock_send):
    """Test signal command."""
    lora = Rak811()
    assert lora.signal == [-30, 26]
    mock_send.assert_called_once_with('signal')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_dr(mock_serial, mock_send):
    """Test dr setter."""
    lora = Rak811()
    lora.dr = 5
    mock_send.assert_called_once_with('dr=5')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='5')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_dr(mock_serial, mock_send):
    """Test dr getter."""
    lora = Rak811()
    assert lora.dr == 5
    mock_send.assert_called_once_with('dr')
    lora.close()


@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_set_link_cnt(mock_serial, mock_send):
    """Test link_cnt setter."""
    lora = Rak811()
    lora.link_cnt = (15, 2)
    mock_send.assert_called_once_with('link_cnt=15,2')
    lora.close()


@patch.object(Rak811, '_send_command', return_value='15,2')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_link_cnt(mock_serial, mock_send):
    """Test link_cnt getter."""
    lora = Rak811()
    assert lora.link_cnt == [15, 2]
    mock_send.assert_called_once_with('link_cnt')
    lora.close()


@patch.object(Rak811, '_send_command', return_value=(
    '13,'
    '26dddddd,'
    '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn,'
    '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
))
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_abp_info(mock_serial, mock_send):
    """Test abp_info command."""
    lora = Rak811()
    assert lora.abp_info == [
        '13',
        '26dddddd',
        '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn',
        '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ]
    mock_send.assert_called_once_with('abp_info')
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['2,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_unconfirmed(mock_serial, mock_send, mock_events):
    """Test send, unconfirmed."""
    lora = Rak811()
    lora.send('Hello')
    mock_send.assert_called_once_with('send=0,1,48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 0
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['1,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_confirmed(mock_serial, mock_send, mock_events):
    """Test send, confirmed."""
    lora = Rak811()
    lora.send('Hello', port=2, confirm=True)
    mock_send.assert_called_once_with('send=1,2,48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 0
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['2,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_binary(mock_serial, mock_send, mock_events):
    """Test send, binary."""
    lora = Rak811()
    lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()
    lora.close()


@patch.object(Rak811, '_get_events', return_value=['5,0,0'])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_fail(mock_serial, mock_send, mock_events):
    """Test send, fail."""
    lora = Rak811()
    with raises(Rak811EventError,
                match='5'):
        lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()
    lora.close()


@patch.object(Rak811, '_get_events', return_value=[
    '2,0,0',
    '0,11,-34,27,4,65666768',
])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_receive(mock_serial, mock_send, mock_events):
    """Test send and receive."""
    lora = Rak811()
    lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 1
    assert lora.get_downlink() == {
        'port': 11,
        'rssi': -34,
        'snr': 27,
        'len': 4,
        'data': '65666768',
    }
    lora.close()


@patch.object(Rak811, '_get_events', return_value=[
    '2,0,0',
    '0,11,4,65666768',
])
@patch.object(Rak811, '_send_command')
@patch('rak811.rak811.Rak811Serial', autospec=True)
def test_get_send_receive_no_recv_ex(mock_serial, mock_send, mock_events):
    """Test send and receive, recv_ex disabled."""
    lora = Rak811()
    lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 1
    assert lora.get_downlink() == {
        'port': 11,
        'rssi': 0,
        'snr': 0,
        'len': 4,
        'data': '65666768',
    }
    lora.close()
