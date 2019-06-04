import abc


class Base(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, config):
        self._config = config

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, *args):
        pass

    @abc.abstractmethod
    def generate_onetime_key(self):
        """
        One-Time SSH deployment key
        """
        pass

    @abc.abstractmethod
    def launch_instance(self):
        """
        Start an instance
        """
        pass

    @abc.abstractmethod
    def get_instance_status(self):
        """
        Get status of an instance 
        """
        pass

    @abc.abstractmethod
    def get_instance_ip(self):
        """
        Get instance  
        """
        pass

    @abc.abstractmethod
    def destroy_instance(self):
        """
        Remove an instance
        """
        pass

    @abc.abstractmethod
    def validate_image(self):
        """
        Validate that an image exists
        """
        pass

    def validate_projects(self):
        """
        Validate that a project exists
        """
        pass

    def validate_image_member(self):
        """
        Validate that an image member exists
        """
        pass

    def create_image_member(self):
        """
        Share an image with a project
        """
        pass
