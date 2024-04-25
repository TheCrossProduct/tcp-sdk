from slumber.serialize import BaseSerializer


class PlainTextSerializer(BaseSerializer):
    content_types = ["text/plain", "text/html"]

    key = "plain"

    def loads(self, data):
        decoded = str(data.decode("utf-8"))
        return decoded

    def dumps(self, data):
        return data
