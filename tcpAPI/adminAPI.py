import platform
import requests
import sys

from datetime import datetime

from slumber.serialize import Serializer
from slumber.exceptions import HttpServerError


__version__ = datetime.today().strftime ("%Y-%m-%d")

class adminAPI (object):

    base_url = None
    user_agent = 'scw-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host="https://api.thecrossproduct.xyz/v1", privkey="", user_agent=None):

        from .log import error

        self.host = host

        if user_agent:
            self.user_agent = user_agent

        self.private_key = privkey
        if not privkey:
            import os
            if 'PRIVATE_KEY' not in os.environ.keys():
                error ("No private key was provided") 
                exit (1)

            self.private_key = os.environ["PRIVATE_KEY"]


    def make_requests_session (self):

        session = requests.Session ()

        return session

    def get_api_url (self):

        return self.host

    def query (self, **kwargs):

        from .adminSlumberAPI import AdminSlumberAPI

        api = AdminSlumberAPI (self.host, 
                          self.private_key, 
                          self.get_api_url (),
                          session=self.make_requests_session(),
                          serializer=Serializer(default="json"),
                          **kwargs)

        return api
