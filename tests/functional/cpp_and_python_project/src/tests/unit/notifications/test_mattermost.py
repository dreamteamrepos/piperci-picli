import unittest
from mock import patch, Mock
import json
import pytest
import requests

from charon.notifications import mattermost


class MattermostTest(unittest.TestCase):
    def setUp(self):
        with patch.object(mattermost.Mattermost, "__init__", lambda x, y: None):
            self.notification = mattermost.Mattermost(None)
            self.notification.url = "http://localhost"
            self.notification.access_token = "test"
            self.notification.verify = False

    @patch("requests.post")
    @patch("requests.get")
    @patch("charon.notifications.mattermost.Mattermost._get_channel_id")
    def test_send_notification(self, mock_get_channel_id, mock_get, mock_post):
        mock_get.status_code = 200
        mock_post.status_code = 200
        mock_get_channel_id.return_value = "123"

        data = {"channel_id": "123", "message": "test"}

        result = self.notification.send_notification("test", "test", "test")
        mock_post.assert_called_with(
            "http://localhost/posts",
            headers={"Authorization": "Bearer test"},
            data=json.dumps(data),
            verify=False,
        )

    @patch("requests.post", autospec=True)
    @patch("requests.get", autospec=True)
    @patch("charon.notifications.mattermost.Mattermost._get_channel_id")
    def test_send_notification_failure(self, mock_get_channel_id, mock_get, mock_post):
        mock_get.status_code = 400
        mock_post.status_code = 400
        mock_get_channel_id.return_value = "123"

        result = self.notification.send_notification("test", "test", "test")
        self.assertRaises(requests.HTTPError)

    @patch("requests.get", autospec=True)
    def test_get(self, mock_get):
        mock_get.status_code = 200

        result = self.notification._get(1)
        assert result is not None

    @patch("requests.get", autospec=True)
    def test_get_failure(self, mock_get):
        mock_get.status_code = 200

        result = self.notification._get(1)
        self.assertRaises(requests.HTTPError)

    @patch("requests.post", autospec=True)
    def test_post(self, mock_post):
        mock_post.status_code = 200

        result = self.notification._post(1, 2)
        mock_post.assert_called_once_with(
            "http://localhost1",
            headers={"Authorization": "Bearer test"},
            data=2,
            verify=False,
        )
        assert result is not None

    @patch("requests.post", autospec=True)
    def test_get_failure(self, mock_post):
        mock_post.status_code = 400

        result = self.notification._post(1, 2)
        self.assertRaises(requests.HTTPError)

    @patch("requests.get", autospec=True)
    def test_get_team_id(self, mock_get):
        mock_get.status_code = 200
        mock_get.return_value.content = '{"id": "123"}'

        result = self.notification._get_team_id("test")
        mock_get.assert_called_once_with(
            "http://localhost/teams/name/test",
            headers={"Authorization": "Bearer test"},
            verify=False,
        )

    @patch("requests.get", autospec=True)
    def test_get_team_id_failure(self, mock_get):
        mock_get.status_code = 404

        result = self.notification._get_team_id("test")

        self.assertRaises(requests.HTTPError)

    @patch("requests.get", autospec=True)
    def test_get_channel_id(self, mock_get):
        team_id = "123"
        channel_name = "test"
        mock_get.status_code = 200
        mock_get.return_value.content = '{"id": "123"}'

        result = self.notification._get_channel_id(team_id, channel_name)
        mock_get.assert_called_once_with(
            "http://localhost/teams/{0}/channels/name/{1}".format(
                team_id, channel_name
            ),
            headers={"Authorization": "Bearer test"},
            verify=False,
        )
