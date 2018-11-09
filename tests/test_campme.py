# encoding: utf-8
import random
import sys
import os
import urllib2
sys.path.append("ccbot")

from ccbot.commands.campme import CampMe
from ccbot.services.api_client import ApiClient
from ccbot.services.slack_response import SlackResponse
from mock import MagicMock, patch
import pytest
import unittest
from urllib2 import *

COMMAND = 'campme'
COMMAND_WITH_VERB = 'campme now'

SAMPLE_API_RESPONSE = [{
    'Room': 'SLH 102',
    'SessionEnd': '2018-11-11T11:15:00',
    'SessionId': 'a83dca4a-06f8-48b6-a398-e857c74d6a30',
    'SessionName': 'Awesome Code!',
    'SessionStart': '2018-11-11T11:15:00',
    'SpeakerFirstName': 'Bob',
    'SpeakerLastName': 'Bobberson'}]


def get_target():
    return CampMe()


class CampMeTest(unittest.TestCase):

    def test_commandtext_is_campme(self):
        assert get_target().get_command() == "campme"

    def test_available_in_all_channels(self):
        assert get_target().get_channel_id() == "all"

    def test_invoke_without_verb_returns_suggestion(self):
        result = get_target().invoke(COMMAND, "fake_user")
        assert result[0][0:] == CampMe.USAGE_TEXT

    @patch.object(CampMe, 'get_data')
    def test_invoke_calls_get_data(self, get_data):
        get_data.return_value = SAMPLE_API_RESPONSE
        target = get_target()
        target.invoke(COMMAND_WITH_VERB, "fake_user")

        get_data.assert_called_with(target.URL)

    @patch.object(CampMe, 'get_data')
    def test_invoke_io_error(self, get_data):
        get_data.side_effect = HTTPError(
            url='http://a.b/', code=403, msg='nope!', hdrs=None, fp=None)
        actual = get_target().invoke(COMMAND_WITH_VERB, "fake_user")
        assert actual == SlackResponse.text('HTTP Error 403: nope!')

    @patch.object(CampMe, 'get_data')
    def test_invoke_value_error(self, get_data):
        get_data.side_effect = URLError('Nope!')
        actual = get_target().invoke(COMMAND_WITH_VERB, "fake_user")
        assert actual == SlackResponse.text("('Nope!',)")

    def test_create_slack_response_populates_attachment(self):
        actual = CampMe.create_slack_response(SAMPLE_API_RESPONSE, 'something')
        for entry in ('title', 'text', 'author_link', 'author_name'):
            assert actual[1][0][entry]

    def test_create_slack_response_zero_results(self):
        actual = CampMe.create_slack_response([], 'something')
        assert actual[0] == 'Server returned no data ¯\\_(ツ)_/¯'

    def test_get_verb_extracts_verb(self):
        cases = {
            'campme': None,
            'campme now': 'now',
            'campme   now': 'now',
            'campme   now   ': 'now',
        }

        for command, expected in cases.iteritems():
            actual = get_target().get_verb(command)
            if (expected is None):
                assert actual is None
            else:
                assert actual == expected

    def test_get_data_calls_api(self):
        api_client = ApiClient()
        api_client.fetch = MagicMock(return_value='yup')

        target = get_target()
        target.api_client = api_client

        actual = target.get_data('dummy_url')

        assert actual == 'yup'
        target.api_client.fetch.assert_called_once()
