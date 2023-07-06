import platform
import requests
import sys

__version__ = '0.0.1'

from .common import SlumberAPI
from .common import SlumberResource

class adminResource (SlumberResource):

    

class adminAPI (object):

    base_url = None
    user_agent = 'scw-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host="https://api.thecrossproduct.xyz/v1", user_agent=None):

        self.host = host

        if user_agent:
            self.user_agent = user_agent

    def make_requests_session (self):

        session = requests.Session ()

        session.headers.update({'User-Agent': self.user_agent})

        return session

    def get_api_url (self):

        return self.host

    def query (self, serialize=True, **kwargs):

        api = SlumberAPI (self.get_api_url (),
                          session=self.make_requests_session(),
                          **kwargs)

        return api
