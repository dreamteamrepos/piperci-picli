class Scanner(object):
    def __init__(self, config):

        self._config = config

    @property
    def name(self):
        return self._config.config["scanner"]["name"]

    @property
    def authentication(self):
        return self._config.config["scanner"]["authentication"]

    @property
    def compliance_threshold(self):
        return self._config.config["scanner"]["compliance_threshold"]

    @property
    def policy_id(self):
        return self._config.config["scanner"]["policy_id"]

    @property
    def verify(self):
        return self._config.config["scanner"]["verify"]
