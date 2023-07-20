import time

class adminResource (slumber.Resource):

    MAX_RETRIES = 8
    MAX_DELAY = 32

    def help (self):

        new_uri = self._store["host"] + '/help' + self._store["base_url"].replace(self._store["host"], "")
        self._store.update({"base_url", new_uri} )

        return self.get ()

    def retry_in (self, retry):

        return min(2 ** retry, self.MAX_DELAY)

    def _request (self, *args, **kwargs):

        from tcp_api_utils.signature import edit_tcp_signature 

        integral_path = self._store["base_url"].replace(self._store["host"], "")

        # removing trailing slashes
        if integral_path[0] == '/':
            integral_path = integral_path[1:]
        if integral_path[-1] == '/':
            integral_path = integral_path[:-1]
   
        host = self._store["host"] 
        if host[-1] == '/':
            host = host[:-1]

        headers =  edit_tcp_signature (self.args[0],
                                       integral_path,
                                       host,
                                       kwargs["data"],
                                       self._store["private_key"])

        self.store_["session"].headers.update (headers)
        return super()._request (*args, **kwargs)

    def _process_response (self, resp):
        if not self._store.get('serialize', True):
            return resp
        return super (SlumberResource, self)._process_response(resp)

class adminAPI (slumber.API):
    resource_class = adminResource

    def __init__ (self, host=None, private_key, base_url=None, auth=None, format=None, append_slash=True, session=None, serializer=None):

        super ().__init__ (base_url, auth, format, append_slash, session, serializer)
        self._store.update ({"host": host,
                             "private_key": private_key})
