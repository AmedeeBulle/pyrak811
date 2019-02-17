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
from rak811 import Rak811Error, Rak811EventError, Rak811ResponseError

# Valid configuration keys
CONFIG_KEYS = ('dev_addr', 'dev_eui', 'app_eui', 'app_key', 'nwks_key',
               'apps_key', 'tx_power', 'pwr_level', 'adr', 'dr', 'public_net',
               'rx_delay1', 'ch_list', 'ch_mask', 'max_chs', 'rx2',
               'join_cnt', 'nbtrans', 'retrans', 'class', 'duty')


class KeyValueParamType(click.ParamType):
    """Basic KEY=VALUE pair parameter type."""

    name = 'key-value'

    def convert(self, value, param, ctx):
        try:
            (k, v) = value.split('=')
            k = k.lower()
            if k not in CONFIG_KEYS:
                self.fail('{0} is not a valid config key'.format(k),
                          param,
                          ctx)
            return (k, v)
        except ValueError:
            self.fail('{0} is not a valid Key=Value parameter'.format(value),
                      param,
                      ctx)


def print_exception(e):
    """Print exception raised by the Rak811 library."""
    if isinstance(e, Rak811ResponseError):
        click.echo('RAK811 response error {}: {}'.format(e.errno, e.strerror))
    elif isinstance(e, Rak811EventError):
        click.echo('RAK811 event error {}: {}'.format(e.errno, e.strerror))
    else:
        click.echo('RAK811 unexpected exception {}'.format(e))


@click.group()
@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    help='Verbose mode'
)
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
    """Enter sleep mode."""
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
    type=KeyValueParamType(),
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
    type=click.Choice(CONFIG_KEYS)
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
    """Get/set next send data rate."""
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
        click.echo('{} {} {} {}'.format(nwk_id, dev_addr, nwks_key, apps_key))
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
    downlink = lora.get_downlink()
    if downlink:
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


if __name__ == '__main__':
    cli()
