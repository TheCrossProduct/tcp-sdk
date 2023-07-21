import time
import slumber

class clientResource (slumber.Resource):

    MAX_RETRIES = 8
    MAX_DELAY = 32

    def help (self):

        new_uri = self._store["host"] + '/help' + self._store["base_url"].replace(self._store["host"], "")
        self._store.update({"base_url": new_uri} )

        resp = self.get ()

        try:
            print (resp.decode('utf-8'))
        except Exception as err:
            print (err)
            print ("No documentation available")

    def _retry_in (self, retry):

        return min(2 ** retry, self.MAX_DELAY)

    def _request (self, *args, **kwargs):

        from .utils import error

        retry = 0

        while True:
            try:
                return super(clientResource, self)._request(*args, **kwargs)
            except slumber.exceptions.HttpServerError as exc:
                if exc.response.status_code not in (502, 503, 504):
                    raise

            retry += 1
            retry_in = self._retry_in(retry)

            if retry >= self.MAX_RETRIES:
                error (f'API endpoint still in maintenance after {retry} attempts.'
                        'Stop trying.')
                raise

            warning (f'API endpoint is currently in maintenance. Try again in'
                      '{retry_in} seconds... (retry {retry} on {self.MAX_RETRIES})'
                     )
            time.sleep (retry_in)

    def _process_response (self, resp):
        if not self._store.get('serialize', True):
            return resp
        return super (clientResource, self)._process_response(resp)

class clientAPI (slumber.API):
    resource_class = clientResource

    def __init__ (self, host=None, base_url=None, auth=None, format=None, append_slash=True, session=None, serializer=None):

        super ().__init__ (base_url, auth, format, append_slash, session, serializer)
        self._store.update ({"host": host})
