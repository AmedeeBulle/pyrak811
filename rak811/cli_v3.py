"""RAK811 CLI interface.

Provides a command line interface for the RAK811 module (Firmware V3.0).

Copyright 2021 Philippe Vanhaesendonck

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
import logging

import click

from .rak811_v3 import Rak811
from .rak811_v3 import Rak811Error
from .rak811_v3 import Rak811ResponseError, Rak811TimeoutError


def print_exception(e):
    """Print exception raised by the Rak811 library."""
    if isinstance(e, Rak811ResponseError):
        click.echo('RAK811 response error {}: {}'.format(e.errno, e.strerror))
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
@click.option(
    '-d',
    '--debug',
    is_flag=True,
    help='Debug mode'
)
@click.version_option()
@click.pass_context
def cli(ctx, verbose, debug):
    """Command line interface for the RAK811 module."""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)


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


"""Get / set commands."""


@cli.command()
@click.argument(
    'config_item',
    required=True
)
@click.pass_context
def set_config(ctx, config_item):
    """Execute set_config RAK811 command.

    \b
    Config items are in the format <type>:<topic>[:<param>]...
    Supported types and topics:
        - device: restart, sleep, boot, status, uart, uart_mode, gpio
        - lora: region, channel, dev_eui, app_eui, app_key, dev_addr,
            apps_key, nwks_key, join_mode, work_mode, ch_mask, class,
            confirm, dr, tx_power, adr, send_interval
        - lorap2p: transfer_mode, channel configuration
    """
    lora = Rak811()
    try:
        responses = lora.set_config(config_item)
        if ctx.obj['VERBOSE']:
            click.echo('Configuration done')
            for response in responses:
                if response.strip():
                    click.echo(response)
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.argument(
    'config_item',
    required=True
)
@click.pass_context
def get_config(ctx, config_item):
    """Execute get_config RAK811 command.

    \b
    Config items are in the format <type>:<topic>[:<param>]
        Supported types and topics:
            - device: status, gpio, adc
            - lora: channel, status
    """
    lora = Rak811()
    try:
        responses = lora.get_config(config_item)
        for response in responses:
            if response.strip():
                click.echo(response)
    except Rak811Error as e:
        print_exception(e)
    lora.close()


"""General AT commands."""


@cli.command()
@click.pass_context
def version(ctx):
    """Get module version."""
    lora = Rak811()
    click.echo(lora.version)
    lora.close()


@cli.command()
@click.pass_context
def help(ctx):
    """Print module help."""
    lora = Rak811()
    for response in lora.help:
        click.echo(response)
    lora.close()


@cli.command()
@click.pass_context
def run(ctx):
    """Exit boot mode and enter normal mode."""
    lora = Rak811()
    lora.run()
    lora.close()


""" Interface commands."""


@cli.command()
@click.option(
    '-i', '--index',
    default='3',
    type=click.Choice(['1', '3']),
    help='UART Index (1 or 3, default 3)'
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
def send_uart(ctx, index, binary, data):
    """Send data to UART.

    UART1 is the AT Command interface, so you probably want to use
    UART3!
    """
    if binary:
        try:
            data = bytes.fromhex(data)
        except ValueError:
            click.echo('Invalid binary data')
            return
    lora = Rak811()
    try:
        lora.send_uart(data, int(index))
    except Rak811Error as e:
        print_exception(e)
        lora.close()
        return

    if ctx.obj['VERBOSE']:
        click.echo('Data sent.')


"""LoRaWan commands."""


@cli.command()
@click.pass_context
def join(ctx):
    """Join the configured network.

    \b
    ABP requires the following parameters to be set prior join:
        - dev_addr
        - nwks_key
        - apps_key

    OTAA requires the following parameters to be set prior join:
        - dev_eui
        - app_eui
        - app_key
    """
    lora = Rak811()
    try:
        lora.join()
        if ctx.obj['VERBOSE']:
            click.echo('Joined!')
    except Rak811Error as e:
        print_exception(e)
    lora.close()


@cli.command()
@click.option(
    '-p', '--port',
    default=1,
    type=click.IntRange(1, 223),
    help='port number to use (1-223)'
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
def send(ctx, port, binary, data, json):
    """Send LoRaWan message and check for downlink."""
    if binary:
        try:
            data = bytes.fromhex(data)
        except ValueError:
            click.echo('Invalid binary data')
            return
    lora = Rak811()
    try:
        lora.send(data, port=port)
    except Rak811Error as e:
        print_exception(e)
        lora.close()
        return

    if ctx.obj['VERBOSE']:
        click.echo('Message sent.')
    if lora.nb_downlinks:
        downlink = lora.get_downlink()
        if downlink['len']:
            downlink['data'] = downlink['data'].hex()
            if json:
                click.echo(dumps(downlink, indent=4))
            elif ctx.obj['VERBOSE']:
                click.echo('Downlink received:')
                click.echo('Port: {}'.format(downlink['port']))
                click.echo('RSSI: {}'.format(downlink['rssi']))
                click.echo('SNR: {}'.format(downlink['snr']))
                click.echo('Data: {}'.format(downlink['data']))
            else:
                click.echo(downlink['data'])
        elif ctx.obj['VERBOSE']:
            click.echo('Send confirmed.')
            click.echo('RSSI: {}'.format(downlink['rssi']))
            click.echo('SNR: {}'.format(downlink['snr']))
    elif ctx.obj['VERBOSE']:
        click.echo('No downlink available.')
    lora.close()


@cli.command()
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
def send_p2p(ctx, binary, data):
    """Send LoRa P2P message."""
    if binary:
        try:
            data = bytes.fromhex(data)
        except ValueError:
            click.echo('Invalid binary data')
            return
    lora = Rak811()
    try:
        lora.send_p2p(data)
    except Rak811Error as e:
        print_exception(e)
        lora.close()
        return

    if ctx.obj['VERBOSE']:
        click.echo('Message sent.')


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
def receive_p2p(ctx, timeout, json):
    """Get LoraP2P message."""
    lora = Rak811()
    lora.receive_p2p(timeout)
    if lora.nb_downlinks:
        rx = lora.get_downlink()
        rx['data'] = rx['data'].hex()
        if json:
            click.echo(dumps(rx, indent=4))
        elif ctx.obj['VERBOSE']:
            click.echo('Message received:')
            click.echo('RSSI: {}'.format(rx['rssi']))
            click.echo('SNR: {}'.format(rx['snr']))
            click.echo('Data: {}'.format(rx['data']))
        else:
            click.echo(rx['data'])
    elif ctx.obj['VERBOSE']:
        click.echo('No message available.')
    lora.close()


if __name__ == '__main__':
    cli()
