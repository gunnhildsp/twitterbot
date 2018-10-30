from tweepy.api import API
from tweepy import User

from twitterbot.twitter_api import connect_to_api, get_followings, get_most_recent_status


def test_connect_to_api():
    api = connect_to_api()
    assert isinstance(api, API)
    api.verify_credentials()


def test_get_followings():
    api = connect_to_api()
    ids, friends = get_followings(api)
    assert isinstance(ids, list)
    assert isinstance(friends[0], User)
    assert len(ids) == len(friends)


def test_get_status():
    api = connect_to_api()
    user_id = 3098427092
    tweet = get_most_recent_status(api, user_id)
    assert tweet is not None