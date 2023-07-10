import slumber

class BytesSerializer (slumber.serialize.BaseSerializer):
    key = "bytes"
    content_type = "text/plain"

    def loads (self, data):
        print ("la")
        return data.decode ()

    def dumps (self, data):
        print ("ici")
        return data.encode ('latin1')

class SlumberResource (slumber.Resource): 

    MAX_RETRIES = 8 

    def retry_in (self, retry):

        return min (2 ** retry, 32)

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
                    debug ("Stop trying", ["tcpAPI"])
                    raise

                debug (f"API endpoint is currently in maintenance. Try again in {retry_in} seconds... (retry {retry} on {self.MAX_RETRIES})", ["tcpAPI"])

                time.sleep (retry_in)

class SlumberAPI (slumber.API):

    from slumber import serialize

    resource_class = SlumberResource
    serializer = serialize.Serializer (default="json", serializers=[serialize.JsonSerializer(), serialize.YamlSerializer(), BytesSerializer()])

