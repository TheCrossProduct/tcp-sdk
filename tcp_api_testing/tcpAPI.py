import platform
import requests
import sys
import slumber

__version__ = '0.0.1'

class SlumberResource (slumber.Resource): 

    MAX_RETRIES = 8 

    def retry_in (self, retry):
        return min (2 ** retry, 30)

    def _request (self, *args, **kwargs):

        from tcp_api_utils.debug import debug
        import time

        retry = 0

        while True:
            try:
                return super (SlumberResource, self)._request (*args, **kwargs)
            except slumber.exceptions.HttpServerError as exc:

                if exc.response.status_code not in (502, 503, 504):
                    raise

                retry += 1

                retry_in = self.retry_in (retry)

                if retry >= self.MAX_RETRIES:
                    debug (f"API endpoint still in maintenance after {retry} attempts", ["tcpAPI"])
                    debug ("Stop trying", ["python-tcp"])
                    raise

                debug (f"API endpoint is currently in maintenance. Try again in %s seconds... (retry {retry_in} on {self.MAX_RETRIES})", ["tcpAPI"])

                time.sleep (retry_in)

    def _process_response (self, resp):

        if self._store.get('serialize', True) is False:
            return resp

        return super (SlumberResource, self)._process_response(resp)

class SlumberAPI (slumber.API):

    resource_class = SlumberResource

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

    def query (self, serialize=True, **kwargs):

        api = SlumberAPI (self.get_api_url (),
                          session=self.make_requests_session(),
                          **kwargs)

        api._store['serialize'] = serialize

        return api
