if False:
    import logging
    import contextlib
    
    from http.client import HTTPConnection
    HTTPConnection.debuglevel=1
    logging.basicConfig ()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger ("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

from .client import client
from .admin import admin
