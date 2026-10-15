from .common import *

def getList(client):

    logging.info(f"List processes")
    try:
        ans = client.query().app.processes.get()
        res = ans["processes"]
        while "next" in ans["paging"]:
            logging.info("getting next page...")
            lnk = ans["paging"]["next"].split("/next/")[1]
            ans = client.query().app.processes.next(lnk).get()
            res += ans["processes"]
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    for proc in res:
        print("{id} {launched} {state:20s} {domain}@{app}".format(**proc))
    return res

def show(client, pid):

    logging.info(f"Show processes {pid}")
    try:
        res = client.query().app.process(pid).get()
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    print(yaml.dump(res))
    return res

def delete(client, pid, keep=True):

    if pid == "*":
        if not click.confirm('Erase all processes?'): return False
        for proc in getList(client):
            delete(client, proc["id"], keep=keep)
        return True

    logging.info(f"Delete processes {pid}")
    try:
        res = client.query().app.process(pid).delete(keep=f"{keep}".lower())
        print(res)
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
        return False
    return True

@cli.group
def processes(): pass

@processes.command(name="list", help="list files from storage")
@pass_client
def _list(client, **kwargs):
    getList(client, **kwargs)

@processes.command(name="show", help="list files from storage")
@click.argument("pid", type=str)
@pass_client
def _show(client, **kwargs):
    show(client, **kwargs)

@processes.command(name="delete", help="list files from storage")
@click.argument("pid", type=str)
@click.option("--keep/--no-keep", default=True)
@pass_client
def _delete(client, **kwargs):
    delete(client, **kwargs)

