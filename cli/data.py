from .common import *

def getlist(client, prefix=None, suffix=None, **kwargs):

    logging.info(f"listing data")
    body={}
    if prefix: body["prefix"] = prefix
    if suffix: body["suffix"] = suffix
    body.update(kwargs)
    for k, v in body.items():
        if type(v) is tuple: body[k] = list(v)
    for k, v in body.items():
        logging.info(f"  - {k}: {v}")
    try:
        res = client.query().data.post(body)
        print(yaml.dump(res))
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

def delete(client, uri):
    try:
        client.query().data.remove.post({'uri':uri})
        logging.info(f"removed {uri}")
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

def deleteSelection(client, prefix=None, suffix=None):
    logging.info(f"deleting data")
    body={}
    if prefix: body["prefix"] = prefix
    if suffix: body["suffix"] = suffix
    for k, v in body.items():
        logging.info(f"  - {k}: {v}")
    try:
        res = client.query().data.post(body)
        for uri in res["files"] + res["dirs"]:
            if uri == "/": continue
            logging.info(f"removing {uri}")
            client.query().data.remove.post({'uri':uri})
            logging.info(f"removed {uri}")
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

def upload(client, src, dst):
    body = {}
    body['uri'] = str(dst)
    try:
        resp = client.query().data.upload.singlepart.post(body)
        with open(str(src), 'rb') as fp:
            requests.put(resp['url'], data=fp)
        client.query().data.upload.singlepart.complete.post({"uri": body['uri']})
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    logging.info(f"Successfully uploaded {src} to {dst}")
    return True

def download(client, src, dst=None):
    '''
    Use 'client' to download file 'src' to 'dst'.
    Arguments:
    - client: a TCP client (can be obtained by getClient)
    - src: the local path where to download the file
    - dst: the URI of the file to be downloaded
    Return:
    True if everything went as expected, False otherwise.
    '''
    logging.info(f"Trying to downloaded {src} to {dst}")
    try:
        dst = Path(src) if dst is None else Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        client.download(src, dst)
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

def downloadSelection(client, dst="./", prefix=None, suffix=None):
    logging.info(f"downloading selection")
    body={}
    if prefix: body["prefix"] = prefix
    if suffix: body["suffix"] = suffix
    for k, v in body.items():
        logging.info(f"  - {k}: {v}")
    try:
        res = client.query().data.post(body)
        for uri in res["dirs"]:
            loc = Path(dst)/uri
            logging.info(f"create {loc}")
            loc.mkdir(parents=True, exist_ok=True)
        for src in res["files"]:
            logging.info(f"downloading {src}...")
            client.download(src, Path(dst)/src)
        logging.info(f"done")
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

@cli.group(name="data")
def data(): pass

@data.command(name="upload", help="upload a file to remote storage")
@click.argument("src", type=click.Path(exists=True, dir_okay=False))
@click.argument("dst", type=click.Path())
@pass_client
def _upload(client, **kwargs):
    upload(client, **kwargs)

@data.command(name="download", help="get a file from remote storage")
@click.argument("src", type=click.Path())
@click.argument("dst", type=click.Path(), default=None)
@pass_client
def _download(client, **kwargs):
    download(client, **kwargs)

@data.command(name="list", help="list files from storage")
@click.option("-p", "--prefix", type=str, default="")
@click.option("-s", "--suffix", type=str, default="")
@click.option("--personal/--global", default=True)
@click.option("-g", "--group", "groups", type=str, multiple=True)
@pass_client
def _list(client, **kwargs):
    getlist(client, **kwargs)

@data.command(name="delete", help="delete a file from storage")
@click.argument("uri", type=str, default=click.Path())
@pass_client
def _delete(client, **kwargs):
    delete(client, **kwargs)

@data.command(name="delete-selection", help="delete several files by pre/suffix")
@click.option("-s", "--prefix", type=str, default="")
@click.option("-p", "--suffix", type=str, default="")
@pass_client
def _delete_selection(client, **kwargs):
    deleteSelection(client, **kwargs)

@data.command(name="download-selection", help="download files by pre/suffix")
@click.option("-s", "--prefix", type=str, default="")
@click.option("-p", "--suffix", type=str, default="")
@click.option("-d", "--dst", type=click.Path(), default="./")
def _download_selection(**kwargs):
    downloadSelection(client, **kwargs)
