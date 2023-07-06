import platform
import requests
import sys

__version__ = '0.0.1'

from .common import SlumberAPI

class tcpAPI (object):

    base_url = None
    user_agent = 'scw-sdk/%s Python/%s %s' % (__version__, ' '.join(sys.version.split()), platform.platform())

    def __init__ (self, host="https://api.thecrossproduct.xyz/v1", token=None, user_agent=None, usermail=None, passwd=None):

        self.host = host

        if user_agent:
            self.user_agent = user_agent

        self.token = None

        if token:
            self.token = token

        elif usermail and passwd:
            from requests.auth import HTTPBasicAuth
            import json

            resp = requests.get (self.host+'/auth/login', auth=HTTPBasicAuth(usermail,passwd))
            if resp.status_code == 200:
                self.token = json.loads (resp.text)['token']

        if not token:
            import os
            if 'TCP_API_TOKEN' not in os.environ.keys():
                exit (1)
            self.token = os.environ['TCP_API_TOKEN']

    def make_requests_session (self):

        session = requests.Session ()

        session.headers.update({'User-Agent': self.user_agent})

        if self.token:

            session.headers.update ({'Authorization': f'Bearer {self.token}'})

        return session

    def get_api_url (self):

        return self.host

    def query (self, **kwargs):

        api = SlumberAPI (self.get_api_url (),
                          session=self.make_requests_session(),
                          **kwargs)

        return api
