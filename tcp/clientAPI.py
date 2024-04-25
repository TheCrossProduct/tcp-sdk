import time
import slumber
from .logs import warning
from . import exceptions


class clientResource(slumber.Resource):
    MAX_RETRIES = 8
    MAX_DELAY = 32

    def _get_help(self):
        new_uri = (
            self._store["host"]
            + "/help"
            + self._store["base_url"].replace(self._store["host"], "")
        )
        self._store.update({"base_url": new_uri})

        try:
            resp = self.get()
        except exceptions.HttpClientError as err:
            if err.response.status_code == "404":
                raise exceptions.NoDocumentation(str(err), **err.__dict__) from err
            raise err

        return resp

    def help(self):
        print(self._get_help())

    def _retry_in(self, retry):
        return min(2**retry, self.MAX_DELAY)

    def _request(self, *args, **kwargs):
        retry = 0

        from .track_usage import TrackUsage

        if self._store["keep_track"] and hasattr(TrackUsage(), "uses"):
            key = (
                self._store["base_url"].replace(self._store["host"], "") + "+" + args[0]
            )
            import re

            for pattern in TrackUsage().uses:
                if re.fullmatch(pattern, key):
                    TrackUsage().uses[pattern] += 1
                    break

        while True:
            try:
                return super(clientResource, self)._request(*args, **kwargs)
            except slumber.exceptions.HttpClientError as err:
                if err.response.status_code == 401:
                    raise exceptions.InvalidCredentials(
                        str(err), **err.__dict__
                    ) from err
                raise exceptions.HttpClientError(str(err), **err.__dict__) from err
            except slumber.exceptions.HttpServerError as err:
                if err.response.status_code not in (502, 503, 504):
                    raise exceptions.HttpServerError(str(err), **err.__dict__) from err

            retry += 1
            retry_in = self._retry_in(retry)

            if retry >= self.MAX_RETRIES:
                raise exceptions.HttpServerError(
                    f"API endpoint still in maintenance after {retry} attempts."
                    "Stop trying."
                )

            warning(
                "API endpoint is currently in maintenance. Try again in "
                f"{retry_in} seconds... (retry {retry} on {self.MAX_RETRIES})"
            )
            time.sleep(retry_in)

    def _try_to_serialize_response(self, resp):
        s = self._store["serializer"]

        if resp.headers.get("content-type", None):
            content_type = resp.headers.get("content-type").split(";")[0].strip()

            try:
                stype = s.get_serializer(content_type=content_type)
            except exceptions.SerializerNotAvailable:
                return resp.content

            return stype.loads(resp.content)

        return resp.content


class clientAPI(slumber.API):
    resource_class = clientResource

    def __init__(
        self,
        host=None,
        base_url=None,
        auth=None,
        format=None,
        append_slash=False,
        session=None,
        serializer=None,
        keep_track=False,
    ):
        super().__init__(base_url, auth, format, append_slash, session, serializer)
        self._store.update({"host": host})
        self._store.update({"keep_track": keep_track})
