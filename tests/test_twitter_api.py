import pytest

from tweepy.api import API
from tweepy import User

from twitterbot.twitter_api import connect_to_api, get_followings, logger

def test_connect_to_api():
    api = connect_to_api()
    assert isinstance(api, API)

def test_get_followings():
    friends = get_followings('gunnhildhp')
    assert isinstance(friends, list)
    assert isinstance(friends[0], User)
