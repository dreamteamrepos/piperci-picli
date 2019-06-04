import abc


class Base(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self._config = config

    @abc.abstractmethod
    def start_scan(self):
        """
        Start scan on instance
        """
        pass

    @abc.abstractmethod
    def get_scan_status(self):
        """
        Poll for scan status
        """
        pass

    @abc.abstractmethod
    def download_scan(self):
        """
        Download a completed scan
        """
        pass

    @abc.abstractmethod
    def parse_scan_results(self):
        """
        Parse scan results and output
        """
        pass

    @abc.abstractmethod
    def scan(self):
        """
        Run the previous scan methods
        """
        pass
