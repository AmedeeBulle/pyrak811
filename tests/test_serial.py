"""Units tests for the Rak811Serial class."""
from time import sleep

from mock import Mock, patch
from pytest import raises
from serial import EIGHTBITS
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811.serial import BAUDRATE, PORT, TIMEOUT # noqa
from rak811.serial import Rak811Serial, Rak811TimeoutError # noqa


@patch('rak811.serial.Serial')
def test_instantiate_default(mock_serial):
    """Test that Rak811Serial can be instantiated.

    Check for basic initialisation and teardown of the serial interface.
    """
    rs = Rak811Serial()
    # Test default parameters are used
    mock_serial.assert_called_once_with(port=PORT,
                                        baudrate=BAUDRATE,
                                        timeout=TIMEOUT)
    # Class initialization
    mock_serial.return_value.reset_input_buffer.assert_called_once()
    assert rs._alive

    # Test tear down
    rs.close()
    mock_serial.return_value.close.assert_called_once()
    assert not rs._alive


@patch('rak811.serial.Serial')
def test_instantiate_custom(mock_serial):
    """Test that Rak811Serial can be instantiated - custom parameters."""
    port = '/dev/ttyAMA0'
    timeout = 5
    bytesize = EIGHTBITS
    rs = Rak811Serial(port=port, timeout=timeout, bytesize=bytesize)

    mock_serial.assert_called_once_with(
        port=port,
        baudrate=BAUDRATE,
        timeout=timeout,
        bytesize=bytesize
    )
    rs.close()


@patch('rak811.serial.Serial')
def test_send_string(mock_serial):
    """Test Rak811Serial.send_string."""
    rs = Rak811Serial()

    rs.send_string('Hello world')
    mock_serial.return_value.write.assert_called_once_with(b'Hello world')

    rs.close()


@patch('rak811.serial.Serial')
def test_send_command(mock_serial):
    """Test Rak811Serial.send_command."""
    rs = Rak811Serial()

    rs.send_command('RESET')
    mock_serial.return_value.write.assert_called_once_with(b'at+RESET\r\n')

    rs.close()


def emulate_rak_input(mock, timeout, data_in):
    """Emulate Rak811 output.

    Parameters:
        mock: mocked Serial class
        timeout is the Serial.readline() timeout
        data_in is a list of tuples (delay, bytes):
            delay: delay before data is available
            bytes: output from the Rak811 module

    When used, this function needs to be called before instantiating the
    Rak811Serial object, as it starts the read thread immediately.

    """
    def side_effect():
        if len(data):
            (d1, b1) = data.pop(0)
            sleep(d1)
            # If we have data readily available after this one, set in_waiting
            # to the data size.
            # If we are at the end, or if there is a delay before next set
            # in_waiting to zero.
            if len(data):
                (d2, b2) = data[0]
                if d2:
                    type(mock.return_value).in_waiting = 0
                else:
                    type(mock.return_value).in_waiting = len(b2)
            else:
                type(mock.return_value).in_waiting = 0
            return b1
        else:
            # No more data
            sleep(timeout)
            return b''

    # Take a local copy of the list and update mock
    data = list(data_in)
    mock.return_value.readline.side_effect = side_effect
    # Set in_waiting to the size of the first data line
    if len(data):
        type(mock.return_value).in_waiting = len(data[0][1])
    else:
        type(mock.return_value).in_waiting = 0


@patch('rak811.serial.Serial')
def test_get_response(mock_serial):
    """Test Rak811Serial.get_response."""
    # For response, first line is passed, others, if any are buffered.
    emulate_rak_input(mock_serial, 1, [
        (0, b'OK\r\n'),
        (0, b'OKok\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'OK'
    assert rs.get_response() == 'OKok'
    rs.close()

    # Check for Errors
    emulate_rak_input(mock_serial, 1, [
        (0, b'ERROR-1\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'ERROR-1'
    rs.close()

    # Noise is skipped
    emulate_rak_input(mock_serial, 1, [
        (0, b'Welcome to RAK811\r\n'),
        (0.5, b'\r\n'),
        (0, b'\r\n'),
        (0, b'OK\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'OK'
    rs.close()

    # Handle non-ASCII characters
    emulate_rak_input(mock_serial, 1, [
        (0, b'Non ASCII: \xde\xad\xbe\xef\r\n'),
        (0.5, b'\r\n'),
        (0, b'\r\n'),
        (0, b'OK\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'OK'
    rs.close()

    # Response timeout
    emulate_rak_input(mock_serial, 1, [
    ])
    rs = Rak811Serial(response_timeout=1)
    with raises(Rak811TimeoutError,
                match='Timeout while waiting for response'):
        rs.get_response()
    rs.close()


@patch('rak811.serial.Serial')
def test_get_events(mock_serial):
    """Test Rak811Serial.get_events."""
    # Single command
    emulate_rak_input(mock_serial, 1, [
        (0, b'at+recv=8,0,0\r\n'),
    ])
    rs = Rak811Serial()
    event = rs.get_events()
    assert len(event) == 1
    assert event.pop() == 'at+recv=8,0,0'
    rs.close()

    # Multiple commands
    emulate_rak_input(mock_serial, 1, [
        (0, b'at+recv=2,0,0\r\n'),
        (0, b'Welcome to RAK811\r\n'),
        (0, b'at+recv=0,0,0\r\n'),
    ])
    rs = Rak811Serial()
    event = rs.get_events()
    assert len(event) == 2
    assert event.pop() == 'at+recv=0,0,0'
    assert event.pop() == 'at+recv=2,0,0'
    rs.close()

    # Event timeout
    emulate_rak_input(mock_serial, 1, [
    ])
    rs = Rak811Serial(event_timeout=1)
    with raises(Rak811TimeoutError,
                match='Timeout while waiting for event'):
        rs.get_events()
    rs.close()


@patch('rak811.serial.Serial')
def test_get_response_event(mock_serial):
    """Test response / event sequence."""
    # All at once
    emulate_rak_input(mock_serial, 1, [
        (0, b'Welcome 1\r\n'),
        (0, b'OK\r\n'),
        (0, b'Welcome 2\r\n'),
        (0, b'at+recv=2,0,0\r\n'),
        (0, b'Welcome 3\r\n'),
        (0, b'at+recv=0,0,0\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'OK'
    event = rs.get_events()
    assert len(event) == 2
    assert event.pop() == 'at+recv=0,0,0'
    assert event.pop() == 'at+recv=2,0,0'
    rs.close()

    # Same scenario with delay between response and event
    emulate_rak_input(mock_serial, 1, [
        (0, b'Welcome 1\r\n'),
        (0, b'OK\r\n'),
        (0, b'Welcome 2\r\n'),
        (1, b'at+recv=2,0,0\r\n'),
        (0, b'Welcome 3\r\n'),
        (0, b'at+recv=0,0,0\r\n'),
    ])
    rs = Rak811Serial()
    assert rs.get_response() == 'OK'
    event = rs.get_events()
    assert len(event) == 2
    assert event.pop() == 'at+recv=0,0,0'
    assert event.pop() == 'at+recv=2,0,0'
    rs.close()
