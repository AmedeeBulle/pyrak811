"""Units tests for the CLI.

Rak811 is tested separately and therefore mocked in this suite.
"""
from click.testing import CliRunner
from mock import Mock, patch, PropertyMock
from pytest import fixture
# Ignore RPi.GPIO
p = patch.dict('sys.modules', {'RPi': Mock()})
p.start()
from rak811 import Rak811EventError, Rak811ResponseError, Rak811TimeoutError # noqa
from rak811.cli import cli # noqa
from rak811.rak811 import Mode, RecvEx, Reset # noqa


@fixture
def mock_rak811():
    with patch('rak811.cli.Rak811', autospec=True) as p:
        yield p


@fixture
def runner():
    return CliRunner()


def test_hard_reset(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'hard-reset'])
    mock_rak811.return_value.hard_reset.assert_called_once()
    assert result.output == 'Hard reset complete\n'


def test_version(runner, mock_rak811):
    p = PropertyMock(return_value='2.0.3.0')
    type(mock_rak811.return_value).version = p
    result = runner.invoke(cli, ['version'])
    p.assert_called_once_with()
    assert result.output == '2.0.3.0\n'


def test_sleep(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'sleep'])
    mock_rak811.return_value.sleep.assert_called_once()
    assert result.output == 'Sleeping\n'


def test_wake(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'wake-up'])
    mock_rak811.return_value.wake_up.assert_called_once()
    assert result.output == 'Alive!\n'


def test_reset_module(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'reset', 'module'])
    mock_rak811.return_value.reset.assert_called_once_with(Reset.Module)
    assert result.output.startswith('Module reset')


def test_reset_lora(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'reset', 'lora'])
    mock_rak811.return_value.reset.assert_called_once_with(Reset.LoRa)
    assert result.output.startswith('LoRa reset')


def test_reload(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'reload'])
    mock_rak811.return_value.reload.assert_called_once()
    assert result.output == 'Configuration reloaded.\n'


def test_mode(runner, mock_rak811):
    p = PropertyMock(return_value=Mode.LoRaWan)
    type(mock_rak811.return_value).mode = p
    result = runner.invoke(cli, ['mode'])
    p.assert_called_once_with()
    assert result.output == 'LoRaWan\n'


def test_mode_lora(runner, mock_rak811):
    p = PropertyMock()
    type(mock_rak811.return_value).mode = p
    result = runner.invoke(cli, ['-v', 'mode', 'LoRawan'])
    p.assert_called_once_with(Mode.LoRaWan)
    assert result.output == 'Mode set to LoRaWan.\n'


def test_recv_ex(runner, mock_rak811):
    p = PropertyMock(return_value=RecvEx.Enabled)
    type(mock_rak811.return_value).recv_ex = p
    result = runner.invoke(cli, ['recv-ex'])
    p.assert_called_once_with()
    assert result.output == 'Enabled\n'


def test_recv_ex_disabled(runner, mock_rak811):
    p = PropertyMock()
    type(mock_rak811.return_value).recv_ex = p
    result = runner.invoke(cli, ['-v', 'recv-ex', 'disable'])
    p.assert_called_once_with(RecvEx.Disabled)
    assert result.output == 'RSSI & SNR report on receive Disabled.\n'


def test_band(runner, mock_rak811):
    p = PropertyMock(return_value='US915')
    type(mock_rak811.return_value).band = p
    result = runner.invoke(cli, ['band'])
    p.assert_called_once_with()
    assert result.output == 'US915\n'


def test_band_eu868(runner, mock_rak811):
    p = PropertyMock()
    type(mock_rak811.return_value).band = p
    result = runner.invoke(cli, ['-v', 'band', 'EU868'])
    p.assert_called_once_with('EU868')
    assert result.output == 'LoRaWan region set to EU868.\n'


def test_set_config(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'set-config', 'dr=0', 'adr=on'])
    mock_rak811.return_value.set_config.assert_called_once_with(dr='0',
                                                                adr='on')
    assert result.output == 'LoRaWan parameters set\n'


def test_set_config_nokv(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'set-config', 'dr:0'])
    assert 'dr:0 is not a valid Key=Value parameter' in result.output


def test_set_config_badkey(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'set-config', 'dx=0'])
    assert 'dx is not a valid config key' in result.output


def test_get_config(runner, mock_rak811):
    mock_rak811.return_value.get_config.return_value = 5
    result = runner.invoke(cli, ['-v', 'get-config', 'dr'])
    mock_rak811.return_value.get_config.assert_called_once()
    assert result.output == '5\n'


def test_join_otaa(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'join-otaa'])
    mock_rak811.return_value.join_otaa.assert_called_once()
    assert result.output == 'Joined in OTAA mode\n'


def test_join_otaa_event(runner, mock_rak811):
    mock_rak811.return_value.join_otaa.side_effect = Rak811EventError(4)
    result = runner.invoke(cli, ['-v', 'join-otaa'])
    mock_rak811.return_value.join_otaa.assert_called_once()
    assert result.output == 'RAK811 event error 4: Join failed\n'


def test_join_otaa_timeout(runner, mock_rak811):
    mock_rak811.return_value.join_otaa.side_effect = Rak811TimeoutError(
        'Timeout while waiting for event'
    )
    result = runner.invoke(cli, ['-v', 'join-otaa'])
    mock_rak811.return_value.join_otaa.assert_called_once()
    assert result.output == 'RAK811 timeout: Timeout while waiting for event\n'


def test_join_abp(runner, mock_rak811):
    result = runner.invoke(cli, ['-v', 'join-abp'])
    mock_rak811.return_value.join_abp.assert_called_once()
    assert result.output == 'Joined in ABP mode\n'


def test_join_abp_response(runner, mock_rak811):
    mock_rak811.return_value.join_abp.side_effect = Rak811ResponseError(-3)
    result = runner.invoke(cli, ['-v', 'join-abp'])
    mock_rak811.return_value.join_abp.assert_called_once()
    assert result.output == 'RAK811 response error -3: ABP join error\n'


def test_signal(runner, mock_rak811):
    p = PropertyMock(return_value=(-30, 26))
    type(mock_rak811.return_value).signal = p
    result = runner.invoke(cli, ['signal'])
    p.assert_called_once_with()
    assert result.output == '-30 26\n'


def test_dr(runner, mock_rak811):
    p = PropertyMock(return_value=5)
    type(mock_rak811.return_value).dr = p
    result = runner.invoke(cli, ['dr'])
    p.assert_called_once_with()
    assert result.output == '5\n'


def test_set_dr(runner, mock_rak811):
    p = PropertyMock()
    type(mock_rak811.return_value).dr = p
    result = runner.invoke(cli, ['-v', 'dr', '5'])
    p.assert_called_once_with(5)
    assert result.output == 'Data rate set to 5.\n'


def test_link_cnt(runner, mock_rak811):
    p = PropertyMock(return_value=(15, 2))
    type(mock_rak811.return_value).link_cnt = p
    result = runner.invoke(cli, ['-v', 'link-cnt'])
    p.assert_called_once_with()
    assert result.output == 'Uplink: 15 - Downlink: 2\n'


def test_abp_info(runner, mock_rak811):
    p = PropertyMock(return_value=(
        '13',
        '26dddddd',
        '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn',
        '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    ))
    type(mock_rak811.return_value).abp_info = p
    result = runner.invoke(cli, ['abp-info'])
    p.assert_called_once_with()
    assert result.output == (
        '13 '
        '26dddddd '
        '9annnnnnnnnnnnnnnnnnnnnnnnnnnnnn '
        '0baaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        '\n'
    )


def test_send_unconfirmed(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = []
    result = runner.invoke(cli, ['-v', 'send', 'Hello'])
    mock_rak811.return_value.send.assert_called_once_with(
        data='Hello',
        confirm=False,
        port=1
    )
    assert 'Message sent.' in result.output


def test_send_confirmed(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = []
    result = runner.invoke(cli, ['-v', 'send', '--confirm',
                                 '--port', '2', 'Hello'])
    mock_rak811.return_value.send.assert_called_once_with(
        data='Hello',
        confirm=True,
        port=2
    )
    assert 'Message sent.' in result.output
    assert 'No downlink available.' in result.output


def test_send_binary(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = []
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        confirm=False,
        port=1
    )
    assert 'Message sent.' in result.output
    assert 'No downlink available.' in result.output


def test_send_error(runner, mock_rak811):
    mock_rak811.return_value.send.side_effect = Rak811EventError(5)
    mock_rak811.return_value.get_downlink.return_value = []
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        confirm=False,
        port=1
    )
    assert result.output == 'RAK811 event error 5: Tx timeout\n'


def test_send_receive_recv_tx(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = [{
        'port': 11,
        'rssi': -34,
        'snr': 27,
        'len': 4,
        'data': '65666768',
    }]
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        confirm=False,
        port=1
    )
    assert 'Downlink received' in result.output
    assert 'Port: 11' in result.output
    assert 'RSSI: -34' in result.output
    assert 'SNR: 27' in result.output
    assert 'Data: 65666768' in result.output


def test_send_receive(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = [{
        'port': 11,
        'rssi': 0,
        'snr': 0,
        'len': 4,
        'data': '65666768',
    }]
    result = runner.invoke(cli, ['-v', 'send', '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        confirm=False,
        port=1
    )
    assert 'Downlink received' in result.output
    assert 'Port: 11' in result.output
    assert 'RSSI' not in result.output
    assert 'SNR' not in result.output
    assert 'Data: 65666768' in result.output


def test_send_receive_json(runner, mock_rak811):
    mock_rak811.return_value.get_downlink.return_value = [{
        'port': 11,
        'rssi': -34,
        'snr': 27,
        'len': 4,
        'data': '65666768',
    }]
    result = runner.invoke(cli, ['-v', 'send', '--json',
                                 '--binary', '01020211'])
    mock_rak811.return_value.send.assert_called_once_with(
        data=bytes.fromhex('01020211'),
        confirm=False,
        port=1
    )
    assert ('"port": 11') in result.output
    assert ('"rssi": -34') in result.output
    assert ('"snr": 27') in result.output
    assert ('"len": 4') in result.output
    assert ('"data": "65666768"') in result.output
