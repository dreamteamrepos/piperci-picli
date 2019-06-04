import requests
import json
import time
import sys
import logging
import lxml.html
from lxml.etree import XPath
import uuid
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from charon.scanners import base


logger = logging.getLogger(__name__)


class Nessus(base.Base):
    def __init__(self, config):
        super(Nessus, self).__init__(config)
        self.url = self._config.scanner.authentication["url"]
        self.access_key = self._config.scanner.authentication["access_key"]
        self.secret_key = self._config.scanner.authentication["secret_key"]
        self.policy_id = self._config.scanner.policy_id
        self.verify = self._config.scanner.verify

    def _connect(self, method, resource, data=None, params=None):
        """
        Send a request
        Send a request to Nessus based on the specified data. If the session token
        is available add it to the request. Specify the content type as JSON and
        convert the data to JSON format.
        """
        headers = {
            "content-type": "application/json",
            "X-APIKeys": "accessKey="
            + self.access_key
            + "; secretKey="
            + self.secret_key,
        }

        data = json.dumps(data)

        if method == "POST":
            result = requests.post(
                self.url + resource, data=data, headers=headers, verify=self.verify
            )
        elif method == "PUT":
            result = requests.put(
                self.url + resource, data=data, headers=headers, verify=self.verify
            )
        elif method == "DELETE":
            result = requests.delete(
                self.url + resource, data=data, headers=headers, verify=self.verify
            )
        else:
            result = requests.get(
                self.url + resource, params=params, headers=headers, verify=self.verify
            )

        try:
            result.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(e.response.text, response=e.response)

        if "download" in resource:
            return result.content

        try:
            return result.json()
        except ValueError:
            return result.content

    def _get_policy_uuid(self, policy_id):
        """
        Get policy uuid of a given policy id
        """

        data = self._connect("GET", "/policies/{0}".format(policy_id))

        return data["uuid"]

    def _get_history_ids(self, sid):
        """
        Get history ids
        Create a dictionary of scan uuids and history ids so we can lookup the
        history id by uuid.
        """
        data = self._connect("GET", "/scans/{0}".format(sid))

        return dict((h["uuid"], h["history_id"]) for h in data["history"])

    def _get_scan_history(self, sid, hid):
        """
        Scan history details
        Get the details of a particular run of a scan.
        """
        params = {"history_id": hid}
        data = self._connect("GET", "/scans/{0}".format(sid), params)

        return data["info"]

    def _add(self, name, desc, targets, policy_id):
        """
        Add a new scan
        Create a new scan using the policy_id, name, description and targets. The
        scan will be created in the default folder for the user. Return the id of
        the newly created scan.
        """

        scan = {
            "uuid": "fb18acbc-39cc-d6a6-3d3b-b145f6f2eade659f25cac6837b27",
            "settings": {
                "policy_id": policy_id,
                "name": name,
                "description": desc,
                "text_targets": targets,
            },
        }

        data = self._connect("POST", "/scans", data=scan)

        return data["scan"]

    def _launch(self, sid):
        """
        Launch a scan
        Launch the scan specified by the sid.
        """

        data = self._connect("POST", "/scans/{0}/launch".format(sid))

        return data["scan_uuid"]

    def _update(self, scan_id, name, desc, targets, policy_id=None):
        """
        Update a scan
        Update the name, description, targets, or policy of the specified scan. If
        the name and description are not set, then the policy name and description
        will be set to None after the update. In addition the targets value must
        be set or you will get an "Invalid 'targets' field" error.
        """

        scan = {}
        scan["settings"] = {}
        scan["settings"]["name"] = name
        scan["settings"]["desc"] = desc
        scan["settings"]["text_targets"] = targets

        if policy_id is not None:
            scan["settings"]["policy_id"] = policy_id

        data = self._connect("PUT", "/scans/{0}".format(scan_id), data=scan)

        return data

    def _status(self, sid, hid):
        """
        Check the status of a scan run
        Get the historical information for the particular scan and hid. Return
        the status if available. If not return unknown.
        """

        d = self._get_scan_history(sid, hid)
        return d["status"]

    def _export_status(self, sid, fid):
        """
        Check export status
        Check to see if the export is ready for download.
        """

        data = self._connect("GET", "/scans/{0}/export/{1}/status".format(sid, fid))

        return data["status"] == "ready"

    def _export(self, sid, hid):
        """
        Make an export request
        Request an export of the scan results for the specified scan and
        historical run. In this case the format is hard coded as nessus but the
        format can be any one of nessus, html, pdf, csv, or db. Once the request
        is made, we have to wait for the export to be ready.
        """

        data = {"history_id": hid, "format": "html", "chapters": "compliance_exec"}

        data = self._connect("POST", "/scans/{0}/export".format(sid), data=data)

        fid = data["file"]

        while self._export_status(sid, fid) is False:
            time.sleep(5)

        return fid

    def _download(self, sid, fid):
        """
        Download the scan results
        Download the scan results stored in the export file specified by fid for
        the scan specified by sid.
        """

        data = self._connect("GET", "/scans/{0}/export/{1}/download".format(sid, fid))

        return data

    def _delete(self, scan_id):
        """
        Delete a scan
        This deletes a scan and all of its associated history. The scan is not
        moved to the trash folder, it is deleted.
        """

        self._connect("DELETE", "/scans/{0}".format(scan_id))

    def _history_delete(self, scan_id, history_id):
        """
        Delete a historical scan.
        This deletes a particular run of the scan and not the scan itself. the
        scan run is defined by the history id.
        """

        self._connect("DELETE", "/scans/{0}/history/{1}".format(scan_id, history_id))

    def start_scan(self):

        # ip = self.instance.ip_address
        ip_address = "172.18.129.158"
        name = uuid.uuid4()

        scan_info = self._add(
            str(name), "Create a new scan with API", ip_address, self.policy_id
        )
        scan_id = scan_info["id"]
        self._update(
            scan_id,
            scan_info["name"],
            scan_info["description"],
            ip_address,
            self.policy_id,
        )
        scan_uuid = self._launch(scan_id)

        return scan_id, scan_uuid

    def get_scan_status(self, scan_id, scan_uuid):

        d = self._get_scan_history(scan_id, scan_uuid)
        return d["status"]

    def download_scan(self, scan_id, scan_uuid):

        history_ids = self._get_history_ids(scan_id)
        history_id = history_ids[scan_uuid]

        file_id = self._export(scan_id, history_id)
        data = self._download(scan_id, file_id)

        return data

    def parse_scan_results(self, data):

        html = lxml.html.fromstring(data)
        compliance_failed_xpath = XPath("//span[contains(text(), 'FAILED')]")
        compliance_failed = len(compliance_failed_xpath(html))

        return compliance_failed

    def delete_scan(self, scan_id, scan_uuid):

        history_ids = self._get_history_ids(scan_id)
        history_id = history_ids[scan_uuid]

        self._history_delete(scan_id, history_id)
        self._delete(scan_id)

    def scan(self, num_retries=50):

        new_scan = self.start_scan()
        scan_id, scan_uuid = map(str, new_scan)

        for _ in range(num_retries):
            try:
                scan_completed = self.get_scan_status(scan_id, scan_uuid)
                if scan_completed == "completed":

                    scan_results = self.download_scan(scan_id, scan_uuid)
                    scan_compliance_failed = self.parse_scan_results(scan_results)

                    results = {
                        "scan_report": scan_results,
                        "scan_compliance_failed": scan_compliance_failed,
                    }

                    self.delete_scan(scan_id, scan_uuid)

                    return results

                else:
                    time.sleep(15)
            except Exception as e:
                logger.exception(
                    "These are an error with the Nessus scan. Cleaning up. {}".format(e)
                )
                self.delete_scan(scan_id, scan_uuid)
