class Cloud(object):
    def __init__(self, config):

        self._config = config

    @property
    def name(self):
        return self._config.config["cloud"]["name"]

    @property
    def authentication(self):
        return self._config.config["cloud"]["authentication"]

    @property
    def verify(self):
        return self._config.config["cloud"]["verify"]
