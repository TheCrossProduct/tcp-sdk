class MetaSingleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in MetaSingleton.__instances:
            MetaSingleton.__instances[cls] = super(MetaSingleton, cls).__call__(
                *args, **kwargs
            )
        return MetaSingleton.__instances[cls]


class TrackUsage(object, metaclass=MetaSingleton):
    def init(self, client):
        if hasattr(self, "uses") and self.uses:
            return

        self.uses = {}

        import re

        for ee in client._get_endpoints():
            for mm in ee["methods"]:
                key = ee["endpoint"].replace("/", "\\/") + "\\+" + mm

                key = re.sub("<string:[a-z_]+>", "[^\\/]", key)
                key = re.sub("<int:[a-z_]+>", "[0-9]*", key)
                key = re.sub("<float:[a-z_]+>", "[0-9]*(|\\.[0-9]*)", key)
                key = re.sub("<path:[a-z_]+>", ".*", key)
                key = re.sub(
                    "<uuid:[a-z_]+>",
                    "[0-9a-f]{8}\\-[0-9a-f]{4}\\-4[0-9a-f]{3}\\-[89ab][0-9a-f]{3}\\-[0-9a-f]{12}",
                    key,
                )

                self.uses[f"^{key}$"] = 0
