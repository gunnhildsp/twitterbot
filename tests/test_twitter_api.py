from datetime import datetime
from unittest import mock

import pandas as pd
from tweepy.api import API
from tweepy import User

from twitterbot.twitter_api import (
    connect_to_api,
    get_followings,
    get_most_recent_status,
    format_tweets,
    analyse_tweets,
)


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
    user_id = 3098427092  # User that has tweets
    tweet = get_most_recent_status(api, user_id)
    assert tweet is not None


def test_get_recent_tweets():
    # TODO implement test
    pass


def test_format_tweets():
    # Create mock tweet
    tweet = mock.Mock()
    tweet.created_at = datetime.now()
    tweet.text = (
        "RT @brianokken: Test &amp; Code 52: pyproject.toml : "
        "the future of Python packaging, with @brettsky https://t.co/hkHFqwKXjr"
    )
    tweet.user.id = 1234
    tweet.user.screen_name = "1234_screen_name"
    tweet.favorite_count = 1
    tweet.retweet_count = 0
    tweets = [tweet]
    exp_cols = [
        "created_at",
        "text",
        "user_id",
        "user_screen_name",
        "favorite_count",
        "retweet_count",
    ]
    tweet_df = format_tweets(tweets)
    assert set(tweet_df.columns) == set(exp_cols)
    assert tweet_df.retweet_count.iloc[0] == 0
    assert tweet_df.favorite_count.iloc[0] == 1


def test_get_most_recent_status():
    # TODO implement test
    pass


def test_analyse_tweets():
    test_dict = {
        "created_at": [""],
        "text": ["Text"],
        "user_id": [1],
        "user_screen_name": ["name"],
        "favorite_count": [1],
        "retweet_count": [15],
    }
    tweet_df = pd.DataFrame.from_dict(test_dict)
    analysed_tweets = analyse_tweets(tweet_df)
    assert (
        analysed_tweets.subjectivity.max() <= 1
        and analysed_tweets.subjectivity.min() >= -1
    )
    assert analysed_tweets.polarity.max() <= 1 and analysed_tweets.polarity.min() >= -1
    assert all([c in analysed_tweets.columns for c in ["subjectivity", "polarity"]])
