import os

from tweepy.api import API
from tweepy import User

from twitterbot.twitter_api import connect_to_api, get_followings_id


def test_connect_to_api():
    api = connect_to_api()
    assert isinstance(api, API)


def test_get_followings_id():
    ids = get_followings_id(os.environ.get('MY_USER_NAME'))
    assert isinstance(ids, list)
