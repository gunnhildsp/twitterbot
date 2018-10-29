import os

from tweepy.api import API
from tweepy import User

from twitterbot.twitter_api import connect_to_api, get_followings


def test_connect_to_api():
    api = connect_to_api()
    assert isinstance(api, API)


def test_get_followings():
    ids, friends = get_followings(os.environ.get('MY_USER_NAME'))
    assert isinstance(ids, list)
    assert isinstance(friends[0], User)
    assert len(ids) == len(friends)
