"""RAK811 CLI interface.

Provides a command line interface for the RAK811 module.

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
from json import dumps

import click
from rak811 import Mode, RecvEx, Reset
from rak811 import Rak811
from rak811 import Rak811Error
from rak811 import Rak811EventError, Rak811ResponseError, Rak811TimeoutError

# Valid configuration keys for LoRaWan
LW_CONFIG_KEYS = ('dev_addr', 'dev_eui', 'app_eui', 'app_key', 'nwks_key',
                  'apps_key', 'tx_power', 'pwr_level', 'adr', 'dr',
                  'public_net', 'rx_delay1', 'ch_list', 'ch_mask', 'max_chs',
                  'rx2', 'join_cnt', 'nbtrans', 'retrans', 'class', 'duty')

# Valid configuration keys for LoRaP2P
P2P_CONFIG_KEYS = {
    'freq': click.FloatRange(min=860.000, max=929.900, clamp=False),
    'sf': click.IntRange(min=6, max=12, clamp=False),
    'bw': click.IntRange(min=0, max=2, clamp=False),
    'cr': click.IntRange(min=1, max=4, clamp=False),
    'prlen': click.IntRange(min=8, max=65535, clamp=False),
    'pwr': click.IntRange(min=5, max=20, clamp=False)
}


class KeyValueParamTypeLW(click.ParamType):
    """Basic KEY=VALUE pair parameter type for LoRaWan."""

    name = 'key-value-lorawan'

    def convert(self, value, param, ctx):
        try:
            (k, v) = value.split('=')
            k = k.lower()
            if k not in LW_CONFIG_KEYS:
                self.fail('{0} is not a valid config key'.format(k),
                          param,
                          ctx)
            return (k, v)
        except ValueError:
            self.fail('{0} is not a valid Key=Value parameter'.format(value),
                      param,
                      ctx)


class KeyValueParamTypeP2P(click.ParamType):
    """Basic KEY=VALUE pair parameter type for LoRaP2P."""

    name = 'key-value-p2p'

    def convert(self, value, param, ctx):
        try:
            (k, v) = value.split('=')
            k = k.lower()
        except ValueError:
            self.fail('{0} is not a valid Key=Value parameter'.format(value),
                      param,
                      ctx)
        if k not in P2P_CONFIG_KEYS:
            self.fail('{0} is not a valid config key'.format(k),
                      param,
                      ctx)
        v = P2P_CONFIG_KEYS[k].convert(v, param, ctx)
        return (k, v)


def print_exception(e):
    """Print exception raised by the Rak811 library."""
    if isinstance(e, Rak811ResponseError):
        click.echo('RAK811 response error {}: {}'.format(e.errno, e.strerror))
    elif isinstance(e, Rak811EventError):
        click.echo('RAK811 event error {}: {}'.format(e.errno, e.strerror))
    elif isinstance(e, Rak811TimeoutError):
        click.echo('RAK811 timeout: {}'.format(e))
    else:
        click.echo('RAK811 unexpected exception {}'.format(e))


@click.group()
@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    help='Verbose mode'
)
@click.version_option()
@click.pass_context
def cli(ctx, verbose):
    """Command line interface for the RAK811 module."""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


@cli.command(name='hard-reset')
@click.pass_context
def hard_reset(ctx):
    """Hardware reset of the module.

    Hard reset should not be required in normal operation. It needs to be
    issued once after host boot, or module restart.
    """
    lora = Rak811()
    lora.hard_reset()
    if ctx.obj['VERBOSE']:
        click.echo('Hard reset complete')
    lora.close()


"""System commands."""


@cli.command()
@click.pass_context
def version(ctx):
    """Get module version."""
    lora = Rak811()
    click.echo(lora.version)
    lora.close()


@cli.command()
@click.pass_context
def sleep(ctx):
    """Enter sleep mode."""
    lora = Rak811()
    lora.sleep()
    if ctx.obj['VERBOSE']:
        click.echo('Sleeping')
    lora.close()


@cli.command(name='wake-up')
@click.pass_context
def wake_up(ctx):
    """Wake up."""
    lora = Rak811()
    lora.wake_up()
    if ctx.obj['VERBOSE']:
        click.echo('Alive!')
    lora.close()


@cli.command()
@click.argument(
    'reset_type',
    required=True,
    type=click.Choice(['module', 'lora'])
)
@click.pass_context
def reset(ctx, reset_type):
    """Reset Module or LoRaWan stack."""
    lora = Rak811()
    if reset_type == 'module':
        lora.reset(Reset.Module)
    else:
        lora.reset(Reset.LoRa)
    if ctx.obj['VERBOSE']:
        click.echo('{0} reset complete.'.format(
            'Module' if reset_type == 'module' else 'LoRa'))
    lora.close()


@cli.command()
@click.pass_context
def reload(ctx):
    """Set LoRaWan or LoRaP2P configurations to default."""
    lora = Rak811()
    lora.reload()
    if ctx.obj['VERBOSE']:
        click.echo('Configuration reloaded.')
    lora.close()


@cli.command()
@click.argument(
    'mode',
    required=False,
    type=click.Choice(['LoRaWan', 'LoRaP2P'], case_sensitive=False)
)
@click.pass_context
def mode(ctx, mode):
    """Get/Set mode to LoRaWan or LoRaP2P."""
    lora = Rak811()
    if mode is None:
        click.echo('LoRaWan' if lora.mode == Mode.LoRaWan else 'LoRaP2P')
    else:
        mode = mode.lower()
        if mode == 'lorawan':
            lora.mode = Mode.LoRaWan
        else:
            lora.mode = Mode.LoRaP2P
        if ctx.obj['VERBOSE']:
            click.echo('Mode set to {0}.'.format(
                'LoRaWan' if mode == 'lorawan' else 'LoRaP2P'))
    lora.close()


@cli.command()
@click.argument(
    'recv_ex',
    required=False,
    type=click.Choice(['enable', 'disable'])
)
@click.pass_context
def recv_ex(ctx, recv_ex):
    """RSSI & SNR report on receive."""
    lora = Rak811()
    if recv_ex is None:
        click.echo('Enabled' if lora.recv_ex == RecvEx.Enabled else 'Disabled')
    else:
        lora.recv_ex = (
            RecvEx.Enabled if recv_ex == 'enable' else RecvEx.Disabled
        )
        if ctx.obj['VERBOSE']:
            click.echo('RSSI & SNR report on receive {0}.'.format(
                'Enabled' if recv_ex == 'enable' else 'Disabled'))
    lora.close()


"""LoRaWan commands."""


@cli.command()
@click.argument(
    'band',
    required=False,
    type=click.Choice(
        ['EU868', 'US915', 'AU915', 'KR920', 'AS923', 'IN865'],
        case_sensitive=False
    )
)
@click.pass_context
def band(ctx, band):
    """Get/Set LoRaWan region."""
    lora = Rak811()
    if band is None:
        click.echo(lora.band)
    else:
        band = band.upper()
        lora.band = band
        if ctx.obj['VERBOSE']:
            click.echo('LoRaWan region set to {0}.'.format(band))
    lora.close()


@cli.command()
@click.argument(
    'key_values',
    metavar='KEY=VALUE...',
    required=True,
    type=KeyValueParamTypeLW(),
    nargs=-1
)
@click.pass_context
def set_config(ctx, key_values):
    """Set LoraWAN configuration.

    \b
    Arguments are specified as KEY=VALUE pairs, e.g.:
        set-config app_eui='APP_EUI' app_key='APP_KEY'
    """
    lora = Rak811()
    kv_args = dict(key_values)
    try:
        lora.set_config(**kv_args)
        if ctx.obj['VERBOSE']:
            click.echo('LoRaWan parameters set')
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.argument(
    'key',
    required=True,
    type=click.Choice(LW_CONFIG_KEYS)
)
@click.pass_context
def get_config(ctx, key):
    """Get LoraWan configuration."""
    lora = Rak811()
    try:
        click.echo(lora.get_config(key))
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.pass_context
def join_otaa(ctx):
    """Join the configured network in OTAA mode."""
    lora = Rak811()
    try:
        lora.join_otaa()
        if ctx.obj['VERBOSE']:
            click.echo('Joined in OTAA mode')
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.pass_context
def join_abp(ctx):
    """Join the configured network in ABP mode."""
    lora = Rak811()
    try:
        lora.join_abp()
        if ctx.obj['VERBOSE']:
            click.echo('Joined in ABP mode')
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.pass_context
def signal(ctx):
    """Get (RSSI,SNR) from latest received packet."""
    lora = Rak811()
    (rssi, snr) = lora.signal
    if ctx.obj['VERBOSE']:
        click.echo('RSSI: {0} - SNR: {1}'.format(rssi, snr))
    else:
        click.echo('{} {}'.format(rssi, snr))
    lora.close()


@cli.command()
@click.argument(
    'dr',
    required=False,
    type=click.INT
)
@click.pass_context
def dr(ctx, dr):
    """Get/Set next send data rate."""
    lora = Rak811()
    if dr is None:
        click.echo(lora.dr)
    else:
        try:
            lora.dr = dr
            if ctx.obj['VERBOSE']:
                click.echo('Data rate set to {0}.'.format(dr))
        except Rak811Error as e:
            print_exception(e)
    lora.close()


@cli.command()
@click.pass_context
def link_cnt(ctx):
    """Get up & downlink counters."""
    lora = Rak811()
    (uplink, downlink) = lora.link_cnt
    if ctx.obj['VERBOSE']:
        click.echo('Uplink: {0} - Downlink: {1}'.format(uplink, downlink))
    else:
        click.echo('{} {}'.format(uplink, downlink))
    lora.close()


@cli.command()
@click.pass_context
def abp_info(ctx):
    """Get ABP info.

    When using OTAA, returns the necessary info to re-join in ABP mode. The
    following tuple is returned: (NetworkID, DevAddr, Nwkskey, Appskey)
    """
    lora = Rak811()
    (nwk_id, dev_addr, nwks_key, apps_key) = lora.abp_info
    if ctx.obj['VERBOSE']:
        click.echo('NwkId: {}'.format(nwk_id))
        click.echo('DevAddr: {}'.format(dev_addr))
        click.echo('Nwkskey: {}'.format(nwks_key))
        click.echo('Appskey: {}'.format(apps_key))
    else:
        click.echo('{} {} {} {}'.format(nwk_id, dev_addr, nwks_key, apps_key))
    lora.close()


@cli.command()
@click.option(
    '-p', '--port',
    default=1,
    type=click.IntRange(1, 223),
    help='port number to use (1-223)'
)
@click.option(
    '--confirm',
    is_flag=True,
    help='regular or confirmed send'
)
@click.option(
    '--binary',
    is_flag=True,
    help='Data is binary (hex encoded)'
)
@click.argument(
    'data',
    required=True
)
@click.option(
    '--json',
    is_flag=True,
    help='Output downlink in JSON format'
)
@click.pass_context
def send(ctx, port, confirm, binary, data, json):
    """Send LoRaWan message and check for downlink."""
    if binary:
        try:
            data = bytes.fromhex(data)
        except ValueError:
            click.echo('Invalid binary data')
            return
    lora = Rak811()
    try:
        lora.send(data, confirm=confirm, port=port)
    except Rak811Error as e:
        print_exception(e)
        lora.close()
        return

    if ctx.obj['VERBOSE']:
        click.echo('Message sent.')
    if lora.nb_downlinks:
        downlink = lora.get_downlink()
        downlink['data'] = downlink['data'].hex()
        if json:
            click.echo(dumps(downlink, indent=4))
        elif ctx.obj['VERBOSE']:
            click.echo('Downlink received:')
            click.echo('Port: {}'.format(downlink['port']))
            if downlink['rssi']:
                click.echo('RSSI: {}'.format(downlink['rssi']))
                click.echo('SNR: {}'.format(downlink['snr']))
            click.echo('Data: {}'.format(downlink['data']))
        else:
            click.echo(downlink['data'])
    elif ctx.obj['VERBOSE']:
        click.echo('No downlink available.')
    lora.close()


@cli.command()
@click.argument(
    'key_values',
    metavar='KEY=VALUE...',
    required=False,
    type=KeyValueParamTypeP2P(),
    nargs=-1
)
@click.pass_context
def rf_config(ctx, key_values):
    """Get/Set LoraP2P configuration.

    \b
    Without argument, returns:
        frequency, sf, bw, cr, prlen, pwr

    \b
    Otherwhise set rf_config, Arguments are specified as KEY=VALUE pairs:
        freq: frequency in MHz (860.000-929.900)
        sf: strength factor (6-12)
        bw: bandwidth (0:125KHz, 1:250KHz, 2:500KHz)
        cr: coding rate (1:4/5, 2:4/6, 3:4/7, 4:4/8)
        prlen: preamble length default (8-65535)
        pwr: Tx power (5-20)
    E.g.: rf-config freq=860.100 sf=7 pwr=16

    """
    lora = Rak811()
    config = dict(key_values)
    if config == {}:
        # No parameters: returns rc_config
        config = lora.rf_config
        if ctx.obj['VERBOSE']:
            click.echo('Frequency: {}'.format(config['freq']))
            click.echo('SF: {}'.format(config['sf']))
            click.echo('BW: {}'.format(config['bw']))
            click.echo('CR: {}'.format(config['cr']))
            click.echo('PrLen: {}'.format(config['prlen']))
            click.echo('Power: {}'.format(config['pwr']))
        else:
            click.echo('{} {} {} {} {} {}'.format(
                config['freq'], config['sf'], config['bw'], config['cr'],
                config['prlen'], config['pwr']
            ))
    else:
        # At least a parameter, set rc_config
        lora.rf_config = config
        if ctx.obj['VERBOSE']:
            click.echo('rf_config set: ' + ', '.join('{}={}'.format(k, v) for
                                                     k, v in config.items()))

    lora.close()


@cli.command()
@click.option(
    '--cnt',
    default=1,
    type=click.IntRange(1, 65535),
    help='tx counts (1-65535)'
)
@click.option(
    '--interval',
    default=60,
    type=click.IntRange(1, 3600),
    help=' tx interval (1-3600)'
)
@click.option(
    '--binary',
    is_flag=True,
    help='Data is binary (hex encoded)'
)
@click.argument(
    'data',
    required=True
)
@click.pass_context
def txc(ctx, cnt, interval, binary, data):
    """Send LoRaP2P message."""
    if binary:
        try:
            data = bytes.fromhex(data)
        except ValueError:
            click.echo('Invalid binary data')
            return
    lora = Rak811()
    try:
        lora.txc(data, cnt=cnt, interval=interval)
    except Rak811Error as e:
        print_exception(e)
        lora.close()
        return

    if ctx.obj['VERBOSE']:
        click.echo('Message sent.')
    lora.close()


@cli.command()
@click.pass_context
def rxc(ctx):
    """Set module in LoraP2P receive mode."""
    lora = Rak811()
    lora.rxc()
    if ctx.obj['VERBOSE']:
        click.echo('Module set in receive mode.')
    lora.close()


@cli.command()
@click.pass_context
def tx_stop(ctx):
    """Stop LoraP2P TX."""
    lora = Rak811()
    lora.tx_stop()
    if ctx.obj['VERBOSE']:
        click.echo('LoraP2P TX stopped.')
    lora.close()


@cli.command()
@click.pass_context
def rx_stop(ctx):
    """Stop LoraP2P RX."""
    lora = Rak811()
    lora.rx_stop()
    if ctx.obj['VERBOSE']:
        click.echo('LoraP2P RX stopped.')
    lora.close()


@cli.command()
@click.argument(
    'timeout',
    required=False,
    default=60,
    type=click.INT
)
@click.option(
    '--json',
    is_flag=True,
    help='Output message in JSON format'
)
@click.pass_context
def rx_get(ctx, timeout, json):
    """Get LoraP2P message."""
    lora = Rak811()
    lora.rx_get(timeout)
    if lora.nb_downlinks:
        rx = lora.get_downlink()
        rx['data'] = rx['data'].hex()
        if json:
            click.echo(dumps(rx, indent=4))
        elif ctx.obj['VERBOSE']:
            click.echo('Message received:')
            if rx['rssi']:
                click.echo('RSSI: {}'.format(rx['rssi']))
                click.echo('SNR: {}'.format(rx['snr']))
            click.echo('Data: {}'.format(rx['data']))
        else:
            click.echo(rx['data'])
    elif ctx.obj['VERBOSE']:
        click.echo('No message available.')
    lora.close()


@cli.command()
@click.pass_context
def radio_status(ctx):
    """Get radio statistics.

    Returns: TxSuccessCnt, TxErrCnt, RxSuccessCnt, RxTimeOutCnt, RxErrCnt,
    Rssi, Snr.
    """
    lora = Rak811()
    (
        tx_success_cnt, tx_err_cnt,
        rx_success_cnt, rx_timeout_cnt, rx_err_cnt,
        rssi, snr
    ) = lora.radio_status
    if ctx.obj['VERBOSE']:
        click.echo('TxSuccessCnt: {}'.format(tx_success_cnt))
        click.echo('TxErrCnt: {}'.format(tx_err_cnt))
        click.echo('RxSuccessCnt: {}'.format(rx_success_cnt))
        click.echo('RxTimeOutCnt: {}'.format(rx_timeout_cnt))
        click.echo('RxErrCnt: {}'.format(rx_err_cnt))
        click.echo('RSSI: {}'.format(rssi))
        click.echo('SNR: {}'.format(snr))
    else:
        click.echo('{} {} {} {} {} {} {}'.format(
            tx_success_cnt, tx_err_cnt,
            rx_success_cnt, rx_timeout_cnt, rx_err_cnt,
            rssi, snr
        ))
    lora.close()


@cli.command()
@click.pass_context
def clear_radio_status(ctx):
    """Clear radio statistics."""
    lora = Rak811()
    lora.clear_radio_status()
    if ctx.obj['VERBOSE']:
        click.echo('Radio statistics cleared.')
    lora.close()


if __name__ == '__main__':
    cli()
