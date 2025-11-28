from .common import *

def monitor(client, pid):
    res = None
    state = None
    lastState = None
    delay=0
    logging.info(f"Start monitoring process {pid}...")
    while True:
        # No delay for first loop, then 1 min
        time.sleep(delay)
        delay=60
        # get the process info
        res = client.query().app.process(str(pid)).get()
        state = res["state"]
        # if no change, new loop
        if state == lastState: continue
        # if change, log it and store it
        logging.info(f"-> Current state: {state}")
        lastState = state
        # if a final state has been reached, exit the monitoring loop
        if state=="dead": break
        elif state.startswith("failed"): break
    logging.info(f"Stop monitoring process {pid}...")
    if res['errors']:
        msg  = "Errors encountered during process:\n--> " 
        msg += res['errors'].replace('\n', '\n--> ')
        logging.error(msg)
        return False
    elif state.startswith("failed"):
        logging.error(f"Failed final state ({state})")
        return False
    return True

def collect(client, pid, dst=None):
    logging.info(f"Collect result for process {pid}")
    collected = []
    try:
        dst = Path(pid) if dst is None else Path(dst)
        res = client.query().app.process(str(pid)).get()
        src = res['outputs']
        logging.info(f"found {len(res['outputs'])} files")
        for name, src in res['outputs'].items():
            dst_file = dst/name
            logging.info(f"downloading {src} to {dst_file}...")
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            urlretrieve(src, dst_file)
            collected.append(dst_file)
    except tcp.exceptions.HttpClientError as err:
        logging.error(err.content)
    return collected
