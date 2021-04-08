"""Units tests for the CLI (V3 firmware).

Rak811 is tested separately and therefore mocked in this suite.
"""
from click.testing import CliRunner
from mock import Mock, patch, PropertyMock
from pytest import fixture
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811.cli_v3 import cli  # noqa: E402
from rak811.rak811_v3 import Rak811ResponseError, Rak811TimeoutError  # noqa: E402


@fixture
def mock_rak811():
    with patch('rak811.cli_v3.Rak811', autospec=True) as p:
        yield p


@fixture
def runner():
    return CliRunner()


def test_set_config(runner, mock_rak811):
    mock_rak811.return_value.set_config.return_value = [' ']
    result = runner.invoke(cli, ['-v', 'set-config', 'lora:confirm:1'])
    mock_rak811.return_value.set_config.assert_called_once_with('lora:confirm:1')
    assert result.output == 'Configuration done\n'


def test_set_config_multi(runner, mock_rak811):
    mock_rak811.return_value.set_config.return_value = ['LoRa work mode:LoRaWAN']
    result = runner.invoke(cli, ['-v', 'set-config', 'lora:confirm:1'])
    mock_rak811.return_value.set_config.assert_called_once_with('lora:confirm:1')
    assert result.output == 'Configuration done\nLoRa work mode:LoRaWAN\n'


def test_set_config_error(runner, mock_rak811):
    mock_rak811.return_value.set_config.side_effect = Rak811ResponseError(1)
    result = runner.invoke(cli, ['-v', 'set-config', 'xxx'])
    mock_rak811.return_value.set_config.assert_called_once_with('xxx')
    assert result.output == 'RAK811 response error 1: Unsupported AT command\n'


def test_get_config(runner, mock_rak811):
    mock_rak811.return_value.get_config.return_value = ['0']
    result = runner.invoke(cli, ['-v', 'get-config', 'device:gpio:2'])
    mock_rak811.return_value.get_config.assert_called_once()
    assert result.output == '0\n'


def test_get_config_error(runner, mock_rak811):
    mock_rak811.return_value.get_config.side_effect = Rak811ResponseError(2)
    result = runner.invoke(cli, ['-v', 'get-config', 'xxx'])
    mock_rak811.return_value.get_config.assert_called_once()
    assert result.output == 'RAK811 response error 2: Invalid parameter in AT command\n'


def test_hard_reset(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'hard-reset'])
    mock_rak811.return_value.hard_reset.assert_called_once()
    assert result.output == 'Hard reset complete\n'


def test_version(runner, mock_rak811):
    p = PropertyMock(return_value='V3.0.0.14.H')
    type(mock_rak811.return_value).version = p
    result = runner.invoke(cli, ['version'])
    p.assert_called_once_with()
    assert result.output == 'V3.0.0.14.H\n'


def test_help(runner, mock_rak811):
    p = PropertyMock(return_value=['Help text'])
    type(mock_rak811.return_value).help = p
    result = runner.invoke(cli, ['help'])
    p.assert_called_once_with()
    assert result.output == 'Help text\n'


def test_run(runner, mock_rak811):
    p = PropertyMock(return_value=['Initialization OK'])
    type(mock_rak811.return_value).run = p
    runner.invoke(cli, ['run'])
    p.assert_called_once_with()


def test_join(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'join'])
    mock_rak811.return_value.join.assert_called_once()
    assert result.output == 'Joined!\n'


def test_join_error(runner, mock_rak811):
    mock_rak811.return_value.join.side_effect = Rak811ResponseError(99)
    result = runner.invoke(cli, ['-v', 'join'])
    mock_rak811.return_value.join.assert_called_once()
    assert result.output == 'RAK811 response error 99: LoRa join failed\n'


def test_join_timeout(runner, mock_rak811):
    mock_rak811.return_value.join.side_effect = Rak811TimeoutError(
        'Timeout while waiting for data'
    )
    result = runner.invoke(cli, ['-v', 'join'])
    mock_rak811.return_value.join.assert_called_once()
    assert result.output == 'RAK811 timeout: Timeout while waiting for data\n'


def test_send_unconfirmed(runner, mock_rak811):
    p = PropertyMock(return_value=0)
    type(mock_rak811.return_value).nb_downlinks = p
    result = runner.invoke(cli, ['-v', 'send', 'Hello'])
    mock_rak811.return_value.send.assert_called_once_with(
        data='Hello',
        port=1
    )
    assert 'Message sent.' in result.output


def test_send_confirmed(runner, mock_rak811):
    p = PropertyMock(return_value=1)
    type(mock_rak811.return_value).nb_downlinks = p
    mock_rak811.return_value.get_downlink.return_value = {
        'port': 0,
        'rssi': -34,
        'snr': 27,
        'len': 0,
        'data': '',
    }
    result = runner.invoke(cli, ['-v', 'send', '--port', '2', 'Hello'])
    mock_rak811.return_value.send.assert_called_once_with(
        data='Hello',
        port=2
    )
    assert 'Message sent.' in result.output
    assert 'Send confirmed.' in result.output


def test_send_binary(runner, mock_rak811):
    p = PropertyMock(return_value=0)
    type(mock_rak811.return_value).nb_downlinks = p
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        port=1
    )
    assert 'Message sent.' in result.output
    assert 'No downlink available.' in result.output


def test_send_binary_invalid(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'send', '--binary', '010202xx'])
    assert result.output == 'Invalid binary data\n'


def test_send_error(runner, mock_rak811):
    mock_rak811.return_value.send.side_effect = Rak811ResponseError(94)
    p = PropertyMock(return_value=0)
    type(mock_rak811.return_value).nb_downlinks = p
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        port=1
    )
    assert result.output == 'RAK811 response error 94: LoRa transmiting timeout\n'


def test_send_receive(runner, mock_rak811):
    p = PropertyMock(return_value=1)
    type(mock_rak811.return_value).nb_downlinks = p
    mock_rak811.return_value.get_downlink.return_value = {
        'port': 11,
        'rssi': -34,
        'snr': 27,
        'len': 4,
        'data': bytes.fromhex('65666768'),
    }
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        port=1
    )
    assert 'Downlink received' in result.output
    assert 'Port: 11' in result.output
    assert 'RSSI: -34' in result.output
    assert 'SNR: 27' in result.output
    assert 'Data: 65666768' in result.output


def test_send_receive_json(runner, mock_rak811):
    p = PropertyMock(return_value=1)
    type(mock_rak811.return_value).nb_downlinks = p
    mock_rak811.return_value.get_downlink.return_value = {
        'port': 11,
        'rssi': -34,
        'snr': 27,
        'len': 4,
        'data': bytes.fromhex('65666768'),
    }
    result = runner.invoke(cli, ['-v', 'send', '--json',
                                 '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        port=1
    )
    assert ('"port": 11') in result.output
    assert ('"rssi": -34') in result.output
    assert ('"snr": 27') in result.output
    assert ('"len": 4') in result.output
    assert ('"data": "65666768"') in result.output
