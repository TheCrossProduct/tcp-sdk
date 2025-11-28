import os, sys
import time, logging, getpass, requests
import re
import click
import yaml
from pathlib import Path
from urllib.request import urlretrieve

import tcp

__doc__ = """
    T A C\n
    TCP | The Cross Product\n
    API | Application Programming Interface\n
    CLI | Command Line Interface\n
"""
SPEC_FILEPATH = Path.home() / ".tcp" / "api.yaml"

HOST_STABLE  = "stable"
HOST_STAGING = "staging"
HOST_LOCAL   = "local"
HOST_DEFAULT = HOST_STABLE

HOSTS = {}
HOSTS[HOST_STAGING] = "https://staging.api.thecrossproduct.xyz/v1"
HOSTS[HOST_LOCAL]   = "http://127.0.0.1:8000/v1"
HOSTS[HOST_STABLE]  = "https://api.thecrossproduct.xyz/v1"

pass_client = click.make_pass_decorator(tcp.client, ensure=True)

@click.group(help=__doc__)
@click.option('-h', '--host', default=HOST_STABLE)
@click.option('-q', '--quiet', is_flag=True)
@click.option('-v', '--verbose', is_flag=True)
@pass_client
def cli(client,  host, quiet, verbose):

    if quiet:     log_level = logging.ERROR
    elif verbose: log_level = logging.DEBUG
    else:         log_level = logging.INFO
    logging.basicConfig(level=log_level)

    client.host = HOSTS[host]
    logging.info(f"Host : {client.host}")

