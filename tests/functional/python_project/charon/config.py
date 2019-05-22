import anyconfig
import logging
import os
import yaml

from charon import cloud
from charon.model import schema
from charon import notification
from charon import scanner
from charon import util

logger = logging.getLogger(__name__)


class Config(object):
    def __init__(self, config_file, request_config):
        self.config_file = config_file
        self.request_config = request_config
        self.config = self._combine()

    @property
    def cloud(self):
        return cloud.Cloud(self)

    @property
    def scanner(self):
        return scanner.Scanner(self)

    @property
    def notification(self):
        return notification.Notification(self)

    def _combine(self):

        base = self._get_defaults()
        with util.open_file(self.config_file) as stream:
            try:
                base = self.merge_dicts(base, yaml.safe_load(stream))
                base = self.merge_dicts(base, self.request_config)
            except Exception as e:
                logger.exception("Cannot parse config file.\n\n" "{}\n".format(e))

        schema.validate(base)
        return base

    def merge_dicts(self, a, b):
        return util.merge_dicts(a, b)

    @classmethod
    def _get_defaults(self):
        return {
            "scanner": {
                "name": "nessus",
                "compliance_threshold": "49",
                "authentication": {"url": "", "access_key": "", "secret_key": ""},
                "policy_id": "1261",
                "verify": "False",
            },
            "cloud": {"name": "openstack", "network_id": "", "username": "centos"},
            "request": {
                "image_uuids": [""],
                "source_project_id": "",
                "dest_project_id": "",
            },
        }
