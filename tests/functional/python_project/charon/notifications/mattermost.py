import logging
import requests
import json

from charon.notifications import base

logger = logging.getLogger("charon.notifications.mattermost")


class Mattermost(base.Base):
    def __init__(self, config):
        super(Mattermost, self).__init__(config)
        self.access_token = self._config.notification.authentication["access_token"]
        self.url = self._config.notification.url
        self.verify = self._config.notification.verify

    def _headers(self):

        return {"Authorization": "Bearer {}".format(self.access_token)}

    def _get(self, path):
        """
        Send formatted GET request
        """

        result = requests.get(
            self.url + str(path), headers=self._headers(), verify=self.verify
        )

        try:
            result.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(e.response.text, response=e.response)

        return result.json()

    def _post(self, path, data):
        """
        Send formatted POST request
        """

        result = requests.post(
            self.url + str(path), headers=self._headers(), data=data, verify=self.verify
        )

        try:
            result.raise_for_status()
        except requests.HTTPError as e:
            raise requests.HTTPError(e.response.text, response=e.response)

        return result.json()

    def _get_team_id(self, team_name):
        """
        Get a mattermost TeamID from the team name
        """

        result = self._get("/teams/name/{}".format(team_name))

        return result["id"]

    def _get_channel_id(self, team_id, channel_name):
        """
        Get a mattermost channel ID from a channel name
        """

        result = self._get("/teams/{0}/channels/name/{1}".format(team_id, channel_name))

        return result["id"]

    def send_notification(self, message, channel_name, team_name):
        """
        Sends a message to a specified channel
        """

        team_id = self._get_team_id(team_name)
        channel_id = self._get_channel_id(team_id, channel_name)

        payload = {"channel_id": channel_id, "message": message}

        result = self._post("/posts", data=json.dumps(payload))

        return result["id"]
