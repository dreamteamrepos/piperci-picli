import abc


class Base(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self._config = config

    @abc.abstractmethod
    def send_notification(self, message):
        """
        Send notification message
        Param: Message
        """
        pass
