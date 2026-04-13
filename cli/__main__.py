from .common import cli
from .app import buildAppCommands
from . import data
from . import remote

buildAppCommands()

if __name__ == "__main__": cli()
