from .common import cli
from .app import buildAppCommands
from . import data

buildAppCommands()

if __name__ == "__main__": cli()
