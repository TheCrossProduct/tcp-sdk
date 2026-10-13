from .common import *

def listRemote(client):
    logging.info(f"Listing remotes")
    try:
        res = client.query().app.remotes.get()
        print(f"Found {len(res['remotes'])} remotes:")
        for e in res['remotes']:
            print(f"  - {e['name']}")
    except tcp.exceptions.HttpClientError as err:
       logging.error(err.content)

def showRemote(client, name):
    '''
    Show remote properties.
    '''
    logging.info(f"show details for remote {name}")
    try:
        res = client.query().app.remote.__getattr__(name).get()
        for k, v in res.items():
            print(f"  {k} : {v}")
        #print(yaml.dump(res))
    except tcp.exceptions.HttpClientError as err:
       logging.error(err.content)

def deleteRemote(client, name):
    '''
    Delete remote by name.
    '''
    logging.info(f"Deleting remote {name}")
    try:
       client.query().app.remote(name).delete()
    except tcp.exceptions.HttpClientError as err:
       logging.error(err.content)

def createRemote(client, name, directory, ram, cores, mem):
    '''
    Creates a remote
    '''
    directory = Path(directory)
    logging.info(f"Creating remote {name}")
    body = {}
    body['ip'] = '127.0.0.0'
    body['name'] = name
    body['usr'] = getpass.getuser()
    body['ram'] = ram
    body['num_cores'] = cores
    body['mem'] = mem
    body["input_path"]   = str(directory / "input")
    body["working_path"] = str(directory / "working")
    body["output_path"]  = str(directory / "output")
    try:
        res = client.query().app.remote.post(body)
        auth_path = os.path.expanduser("~/.ssh/authorized_keys")
        logging.info(f"... adding {res['pub']} to {auth_path}")
        with open(auth_path, 'a') as f: f.write(res["pub"]+'\n')
    except tcp.exceptions.HttpClientError as err:
       logging.error(err.content)

@cli.group(name="remote")
def data(): pass

@data.command(name="list", help="List registered remotes.")
@pass_client
def _list(client, **kwargs):
    listRemote(client, **kwargs)

@data.command(name="show", help="Show a registered remote properties.")
@click.argument("name", type=str)
@pass_client
def _show(client, **kwargs):
    showRemote(client, **kwargs)

@data.command(name="delete", help="Delete a registered remote.")
@click.argument("name", type=str)
@pass_client
def _delete(client, **kwargs):
    deleteRemote(client, **kwargs)

@data.command(name="create", help="Registered a remote.")
@click.argument("name", type=str)
@click.argument("directory", type=click.Path(writable=True))
@click.option("--ram", type=str, default="16Gb")
@click.option("--mem", type=str, default="16Gb")
@click.option("--cores", type=int, default=8)
@pass_client
def _create(client, **kwargs):
    createRemote(client, **kwargs)


