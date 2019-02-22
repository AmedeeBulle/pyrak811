"""Units tests for the Rak811 class.

Rak811Serial is tested separately and therefore mocked in this suite.

RPi.GPIO is completely ignored as not available on all platforms, and its use
by the Rak811 class very limited.
"""
from mock import call, Mock, patch
from pytest import fixture, raises
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811 import Rak811, Rak811EventError, Rak811ResponseError # noqa
from rak811.rak811 import Rak811Serial # noqa
from rak811.rak811 import Mode, RecvEx, Reset # noqa


@fixture
def lora():
    """Instantiate Rak811 class though fixture."""
    with patch('rak811.rak811.Rak811Serial', autospec=True):
        rak811 = Rak811()
        yield rak811
        rak811.close()


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


def test_get_events(lora):
    """Test _get_events."""
    # Successful command
    lora._serial.get_events.return_value = [
        'at+recv=2,0,0',
        'at+recv=0,1,0,0,1,55',
    ]
    events = lora._get_events()
    assert events.pop() == '0,1,0,0,1,55'
    assert events.pop() == '2,0,0'


"""AT command API.

For the sake of simplicity we mock Rak811.__send_command and
Tack811._get_events, as these have already been tested.
"""


@patch.object(Rak811, '_send_command', return_value='2.0.3.0')
def test_version(mock_send, lora):
    """Test version command."""
    assert lora.version == '2.0.3.0'
    mock_send.assert_called_once_with('version')


@patch.object(Rak811, '_send_command')
def test_sleep(mock_send, lora):
    """Test sleep command."""
    lora.sleep()
    mock_send.assert_called_once_with('sleep')


@patch.object(Rak811, '_get_events', return_value=['8,0,0'])
@patch.object(Rak811, '_send_string')
def test_wake_up(mock_send, mock_events, lora):
    """Test wake_up command."""
    lora.wake_up()
    mock_send.assert_called_once()
    mock_events.assert_called_once()


@patch.object(Rak811, 'hard_reset')
@patch.object(Rak811, '_send_command')
def test_reset_module(mock_send, mock_hard_reset, lora):
    """Test reset module command."""
    lora.reset(Reset.Module)
    mock_send.assert_called_once_with('reset=0')
    mock_hard_reset.assert_called_once()


@patch.object(Rak811, 'hard_reset')
@patch.object(Rak811, '_send_command')
def test_reset_lora(mock_send, mock_hard_reset, lora):
    """Test reset lora command."""
    lora.reset(Reset.LoRa)
    mock_send.assert_called_once_with('reset=1')
    mock_hard_reset.assert_not_called()


@patch.object(Rak811, '_send_command')
def test_reload(mock_send, lora):
    """Test reload command."""
    lora.reload()
    mock_send.assert_called_once_with('reload')


@patch.object(Rak811, '_send_command')
def test_set_mode(mock_send, lora):
    """Test mode setter."""
    lora.mode = Mode.LoRaWan
    mock_send.assert_called_once_with('mode=0')


@patch.object(Rak811, '_send_command', return_value='0')
def test_get_mode(mock_send, lora):
    """Test mode getter."""
    assert lora.mode == 0
    mock_send.assert_called_once_with('mode')


@patch.object(Rak811, '_send_command')
def test_set_recv_ex(mock_send, lora):
    """Test recv_ex setter."""
    lora.recv_ex = RecvEx.Disabled
    mock_send.assert_called_once_with('recv_ex=1')


@patch.object(Rak811, '_send_command', return_value='1')
def test_get_recv_ex(mock_send, lora):
    """Test recv_ex getter."""
    assert lora.recv_ex == 1
    mock_send.assert_called_once_with('recv_ex')


@patch.object(Rak811, '_send_command')
def test_set_config(mock_send, lora):
    """Test config setter."""
    lora.set_config(adr='on', dr=5)
    assert len(mock_send.mock_calls) == 1
    assert mock_send.mock_calls[0] in (
        call('set_config=adr:on&dr:5'),
        call('set_config=dr:5&adr:on')
    )


@patch.object(Rak811, '_send_command', return_value='1')
def test_get_config(mock_send, lora):
    """Test config getter."""
    assert lora.get_config('dr') == '1'
    mock_send.assert_called_once_with('get_config=dr')


@patch.object(Rak811, '_send_command')
def test_set_band(mock_send, lora):
    """Test band setter."""
    lora.band = 'EU868'
    mock_send.assert_called_once_with('band=EU868')


@patch.object(Rak811, '_send_command', return_value='EU868')
def test_get_band(mock_send, lora):
    """Test band getter."""
    assert lora.band == 'EU868'
    mock_send.assert_called_once_with('band')


@patch.object(Rak811, '_send_command')
def test_join_abp(mock_send, lora):
    """Test join_abp command."""
    lora.join_abp()
    mock_send.assert_called_once_with('join=abp')


@patch.object(Rak811, '_get_events', return_value=['3,0,0'])
@patch.object(Rak811, '_send_command')
def test_join_otaa_success(mock_send, mock_events, lora):
    """Test join_abp command, successful."""
    lora.join_otaa()
    mock_send.assert_called_once_with('join=otaa')
    mock_events.assert_called_once()


@patch.object(Rak811, '_get_events', return_value=['4,0,0'])
@patch.object(Rak811, '_send_command')
def test_join_otaa_failure(mock_send, mock_events, lora):
    """Test join_abp command, failure."""
    with raises(Rak811EventError,
                match='4'):
        lora.join_otaa()
    mock_send.assert_called_once_with('join=otaa')
    mock_events.assert_called_once()


@patch.object(Rak811, '_send_command', return_value='-30,26')
def test_signal(mock_send, lora):
    """Test signal command."""
    assert lora.signal == (-30, 26)
    mock_send.assert_called_once_with('signal')


@patch.object(Rak811, '_send_command')
def test_set_dr(mock_send, lora):
    """Test dr setter."""
    lora.dr = 5
    mock_send.assert_called_once_with('dr=5')


@patch.object(Rak811, '_send_command', return_value='5')
def test_get_dr(mock_send, lora):
    """Test dr getter."""
    assert lora.dr == 5
    mock_send.assert_called_once_with('dr')


@patch.object(Rak811, '_send_command')
def test_set_link_cnt(mock_send, lora):
    """Test link_cnt setter."""
    lora.link_cnt = (15, 2)
    mock_send.assert_called_once_with('link_cnt=15,2')


@patch.object(Rak811, '_send_command', return_value='15,2')
def test_get_link_cnt(mock_send, lora):
    """Test link_cnt getter."""
    assert lora.link_cnt == (15, 2)
    mock_send.assert_called_once_with('link_cnt')


@patch.object(Rak811, '_send_command', return_value=(
    '13,'
    '26dddddd,'
    '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn,'
    '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
))
def test_abp_info(mock_send, lora):
    """Test abp_info command."""
    assert lora.abp_info == (
        '13',
        '26dddddd',
        '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn',
        '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    )
    mock_send.assert_called_once_with('abp_info')


@patch.object(Rak811, '_get_events', return_value=['2,0,0'])
@patch.object(Rak811, '_send_command')
def test_get_send_unconfirmed(mock_send, mock_events, lora):
    """Test send, unconfirmed."""
    lora.send('Hello')
    mock_send.assert_called_once_with('send=0,1,48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 0


@patch.object(Rak811, '_get_events', return_value=['1,0,0'])
@patch.object(Rak811, '_send_command')
def test_get_send_confirmed(mock_send, mock_events, lora):
    """Test send, confirmed."""
    lora.send('Hello', port=2, confirm=True)
    mock_send.assert_called_once_with('send=1,2,48656c6c6f')
    mock_events.assert_called_once()
    assert lora.nb_downlinks == 0


@patch.object(Rak811, '_get_events', return_value=['2,0,0'])
@patch.object(Rak811, '_send_command')
def test_get_send_binary(mock_send, mock_events, lora):
    """Test send, binary."""
    lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()


@patch.object(Rak811, '_get_events', return_value=['5,0,0'])
@patch.object(Rak811, '_send_command')
def test_get_send_fail(mock_send, mock_events, lora):
    """Test send, fail."""
    with raises(Rak811EventError,
                match='5'):
        lora.send(bytes.fromhex('01020211'))
    mock_send.assert_called_once_with('send=0,1,01020211')
    mock_events.assert_called_once()


@patch.object(Rak811, '_get_events', return_value=[
    '2,0,0',
    '0,11,-34,27,4,65666768',
])
@patch.object(Rak811, '_send_command')
def test_get_send_receive(mock_send, mock_events, lora):
    """Test send and receive."""
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


@patch.object(Rak811, '_get_events', return_value=[
    '2,0,0',
    '0,11,4,65666768',
])
@patch.object(Rak811, '_send_command')
def test_get_send_receive_no_recv_ex(mock_send, mock_events, lora):
    """Test send and receive, recv_ex disabled."""
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
