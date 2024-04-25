import sys


def eprint(*args, **kwargs):
    if "debug" in kwargs:
        debug = kwargs["debug"]
        del kwargs["debug"]
        if debug:
            print(*args, file=sys.stderr, **kwargs)
        else:
            print(*args, **kwargs)
    else:
        print(*args, **kwargs)


def create_msg(msg: str, topics=[]):
    from datetime import datetime

    ts = datetime.utcnow().strftime("%a|%H:%M:%S")
    topics_to_string = ""
    space = " "
    if " " == msg[0]:
        space = ""

    for t in topics:
        func = getattr(t, "footprint", None)
        if func and callable(func):
            topics_to_string += f"[{t.footprint()}]"
        else:
            topics_to_string += "[" + str(t)[:8] + "]"

    return f"[{ts}]{topics_to_string}{space}{msg}"


def debug(msg: str, topics=[]):
    eprint(create_msg(msg, topics), debug=True)


def error(msg: str, topics=[]):
    eprint("[Error]" + create_msg(msg, topics), debug=True)


def warning(msg: str, topics=[]):
    eprint("[Warning]" + create_msg(msg, topics), debug=True)
