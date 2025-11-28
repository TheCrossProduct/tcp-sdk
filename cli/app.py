from .common import *
from .utils import monitor as monitor_process
from .utils import collect as collect_process

def URI(uri):

    if ":" not in uri:
        logging.info(f"passing external uri {uri}")
        return uri
    src, dst = uri.split(":")
    if not dst:
        t = time.time()
        timestamp  = time.strftime("%Y-%m-%d_%Hh%Mm%Ss", time.gmtime(t))
        timestamp += f"{t%1}"[2:5] + "ms"
        dst = f"{timestamp}{src}"
    logging.info(f"uploading {src} to {dst}")
    tcp.client().upload(src, dst, overwrite=True)
    return dst

OPT_TYPES = {}
OPT_TYPES["string"] = str
OPT_TYPES["integer"] = int
OPT_TYPES["number"] = float
OPT_TYPES["boolean"] = bool
OPT_TYPES["URI"] = URI

@cli.command(help="Refresh the offline API specification")
@pass_client
@click.option("-o", "--output", default=SPEC_FILEPATH,
              type=click.Path(dir_okay=False, writable=True),
              help="filepath to save the API specifications")
def refresh(client, output):
    query = client.query()
    domains = query.app.get()
    spec = {}
    for domain_name, apps in domains.items():
        domain = query.app.__getattr__(domain_name)
        spec[domain_name] = {}
        for app_name in apps:
            app = domain.__getattr__(app_name)
            ins = app.inputs.get()
            ins = ins["content"][0]["content"]["top"]
            ins = ins["properties"]["inputs"]["properties"]
            spec[domain_name][app_name] = ins
    txt = yaml.safe_dump(spec)
    for line in txt.split("\n"):
        logging.debug(line)
    Path(output).parent.mkdir(parents=True, exist_ok=True) 
    with open(output, 'w') as f: f.write(txt)

def addOption(command, name, spec):
    if spec["type"] == "array":
        multiple = True
        opt_type = spec["items"]["type"]
        if "format" in spec["items"] and spec["items"]["format"] == "uri":
            opt_type="URI"
    else:
        multiple = False 
        opt_type = spec["type"]
        if "format" in spec and spec["format"] == "URI": opt_type="URI"
    #print(f"option {name}'s type is {opt_type}")
    return click.option(f"--{name}",
                        help = spec["description"],
                        type = OPT_TYPES[opt_type],
                        is_flag = spec["type"] == "boolean",
                        multiple = multiple)(command)

def buildAppCommand(domain_group, domain_name, app_name, app_spec):
    # Create the basic command
    @domain_group.command(name=app_name.replace("_", "-"))
    @pass_client
    @click.option("-t", "--tags", type=str, multiple=True,
                  help="keyword to document the process")
    @click.option("-p", "--pool", type=str, multiple=True,
                  help="selection of machine")
    @click.option("-m", "--monitor", is_flag=True,
                  help="monitor the launched process")
    @click.option("-c", "--collect", is_flag=True,
                  help="collect the results in ./<pid>/")
    def com(client, tags, pool, monitor, collect, **inputs):
        if collect: monitor=True
        inputs = {k:v for k,v in inputs.items() if v is not None}
        inputs = {k:v for k,v in inputs.items() if v != ()}
        inputs = {k.replace("_", "-"):v for k,v in inputs.items()}
        logging.debug(f"Launching {domain_name}.{app_name} with inputs:")
        for k,v in inputs.items(): logging.debug(f"  - {k}: {v}")
        body = {"inputs":inputs}
        if pool: body["pool"] = pool
        if tags: body["tags"] = tags
        api = client.query().app
        api = api.__getattr__(domain_name)
        api = api.__getattr__(app_name)
        try:
            pid = api.run.post(body)["id"]
            logging.info(f"pid: {pid}")
            if monitor: monitor_process(client, pid)
            if collect: collect_process(client, pid)
        except tcp.exceptions.HttpClientError as err:
            logging.error(err.content)
        except BaseException as err:
            logging.error(err)
    # Add the options described in the spec
    for opt_name, opt_spec in app_spec.items(): 
        com = addOption(com, opt_name, opt_spec)

def buildAppCommands(spec_filepath=SPEC_FILEPATH):
    fp = Path(SPEC_FILEPATH)
    spec = {}
    if fp.exists():
        with open(fp) as f: spec=yaml.safe_load(f.read())
    for domain_name, domain_spec in spec.items():
        @cli.group(name=domain_name)
        def domain_group(): pass
        for app_name, app_spec in domain_spec.items():
            buildAppCommand(domain_group, domain_name, app_name, app_spec)
