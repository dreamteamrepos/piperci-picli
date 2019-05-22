import requests
import json
import time
import os
import urllib
import uuid

import charon.cloudutils
import charon.util


class Functional(object):
    def __init__(self, cloud, config):
        self.instance_ip = cloud.get_instance_ip
        self.key = cloud.get_onetime_key
        self.username = config.cloud.username

    def run_tests(self, commands):
        """
        Run tests through charon.util.run_command.
        This invokes a paramiko client and runs the tests over ssh.
        Parameters: An array of commands to run on the host
        Returns: A dictionary 
        """

        test_results = []

        for command in commands:
            charon.util.run_command(self.instance_ip, self.username, self.key, command)

        return test_results


def verify_syslog(baseurl, username, password, log_string):
    """
    Verify a system is syslogging to Splunk
    :param baseurl: The baseurl of the splunk server (https://loghost:8089)
    :param username: Username to authenticate to Splunk with
    :param password: Password of the user
    :return: json dict containing {'logging_verified': Boolean}
    """

    def get_session_key(baseurl, username, password):
        endpoint = baseurl + "/services/auth/login?output_mode=json"
        header_auth = {}
        body_auth = {"username": username, "password": password}

        response_auth = requests.post(endpoint, data=body_auth, verify=False)

        return response_auth.text

    def set_search(session_key, search_term):
        session_key_format = "Splunk {0}".format(session_key)
        search_query = "search {0}".format(search_term)
        header_auth = {
            "Authorization": session_key_format,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        endpoint = baseurl + "/services/search/jobs?output_mode=json"
        data = {"search": "{}".format(search_query)}

        response_set_search = requests.post(
            endpoint, headers=header_auth, data=data, verify=False
        )
        return response_set_search.text

    def get_search(session_key, sid, num_retries=10):
        session_key_format = "Splunk {0}".format(session_key)
        header_auth = {"Authorization": session_key_format}
        endpoint = (
            baseurl + "/services/search/jobs/" + sid + "/results?output_mode=json"
        )

        for _ in range(num_retries):
            try:
                response_get_search = requests.get(
                    endpoint, headers=header_auth, verify=False
                )

                if response_get_search.status_code == 200:
                    return response_get_search.text
                else:
                    time.sleep(1.0)
            except requests.exceptions.RequestException as e:
                return e

    session_key = json.loads(get_session_key(baseurl, username, password))["sessionKey"]

    search_id = json.loads(set_search(session_key, log_string))["sid"]

    get_search = json.loads(get_search(session_key, search_id))["results"]

    if len(get_search) > 0:
        results = {"logging_verified": "True"}
    else:
        results = {"logging_verified": "False"}

    return results
