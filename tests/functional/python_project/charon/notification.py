class Notification(object):
    def __init__(self, config):
        self._config = config

    @property
    def name(self):
        return self._config.config["notification"]["name"]

    @property
    def authentication(self):
        return self._config.config["notification"]["authentication"]

    @property
    def url(self):
        return self._config.config["notification"]["url"]

    @property
    def verify(self):
        return self._config.config["notification"]["verify"]
