import datetime
import logging
from operator import attrgetter
import os
import time

from dotenv import load_dotenv, find_dotenv
import numpy as np
import pandas as pd
import tweepy

from twitterbot.sentiment_analysis import text_sentiment

load_dotenv(find_dotenv())
consumer_token = os.environ.get("API_KEY")
consumer_secret = os.environ.get("API_SECRET_KEY")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_SECRET")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def connect_to_api(
    consumer_token=consumer_token,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
):

    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    try:
        api = tweepy.API(auth)
    except Exception as e:
        logger.error(f"Error connecting to API: {e}")
        raise e
    return api


def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15 * 60)


def get_followings(api):
    friends = []
    for friend in limit_handled(tweepy.Cursor(api.friends).items()):
        friends.append(friend)
    return api.friends_ids(), friends


def get_recent_tweets(api, user_id, time_start, return_tweets, num_tweets=50):
    """

    :param api: tweepy.API object to connect
    :param user_id: User to get tweets from
    :param time_start: Oldest time to get tweets for
    :param return_tweets: Number of tweets to return
    :param num_tweets: Maximum number of tweets to fetch from api
    :return: list of tweepy.Status objects
    """

    tweets = api.user_timeline(user_id, count=max(2 * num_tweets, 10))
    tweets.sort(key=attrgetter("created_at"), reverse=True)
    oldest_date = tweets[-1].created_at
    # Only return tweets that are newer than start_time and not comments
    tweets = [
        t
        for t in tweets
        if t.created_at > time_start and t.in_reply_to_status_id is None
    ]
    # If desired number of tweets is found or not enough tweets newer than time_start
    if (
        len(tweets) >= return_tweets or oldest_date <= time_start
    ):  # check age of oldest tweets
        # find out how many tweets to return
        length_to_return = min(len(tweets), return_tweets)
        return tweets[0:length_to_return]
    else:
        # If not enough tweets returned and more tweets are available,
        # Call function again but get more tweets from api
        num_tweets = 2 * num_tweets
        return get_recent_tweets(api, user_id, time_start, return_tweets, num_tweets)


def format_tweets(tweets):
    if not tweets:
        return None
    else:
        cols = [
            "created_at",
            "text",
            "user_id",
            "user_screen_name",
            "favorite_count",
            "retweet_count",
        ]
        tweet_df = pd.DataFrame(columns=cols)
        df_tmp_list = []
        for tweet in tweets:
            df_tmp = pd.DataFrame(
                data=[
                    [
                        tweet.created_at,
                        tweet.text,
                        tweet.user.id,
                        tweet.user.screen_name,
                        tweet.favorite_count,
                        tweet.retweet_count,
                    ]
                ],
                columns=cols,
            )
            df_tmp_list.append(df_tmp)
        tweet_df = tweet_df.append(df_tmp_list, sort=False)
    return tweet_df


def get_most_recent_status(api, user_id):
    # Trying to handle pinned tweets and commenting by fetching five tweets and returning the newest
    count = 5
    user = api.get_user(user_id)
    has_tweets = user.statuses_count > 0

    # Returning None if users does not have any tweets
    if not has_tweets:
        logger.info(f"No tweets for user_id {user_id}")
        return None
    # Removing tweets that are replies to others (=comments)
    else:
        found = False
        tweets = api.user_timeline(user_id, count=count)
        while (not found) and count < 100:
            tweets = [t for t in tweets if t.in_reply_to_status_id is None]
            if tweets:
                found = True
            else:
                count = 2 * count
                tweets = api.user_timeline(user_id, count=count)
    if not found:
        logger.info(
            f"Could not find any tweets among most recent 100 that were not comments for user_id {user_id}"
        )
        return None

    # Find newest of remaining
    newest_tweet = tweets[0]
    for tweet in tweets[1:]:
        if tweet.created_at > newest_tweet.created_at:
            newest_tweet = tweet

    return newest_tweet


def unfollow_users_with_old_posts(maximum_age_days):
    api = connect_to_api()
    user_ids, friends = get_followings(api)
    time = datetime.datetime.now() - datetime.timedelta(days=maximum_age_days)
    for user_id in user_ids:
        tweet = get_recent_tweets(api, user_id, time, 1)
        if not tweet:
            logger.info(
                f"Unfollowing user_id {user_id} as there are no tweets on their timeline"
            )
            api.destroy_friendship(user_id)
        else:
            duration = datetime.datetime.now() - tweet.created_at
            if duration.days > maximum_age_days:
                logger.info(
                    f'Unfollowing user "{tweet.user.name}" as the newest post is {duration.days} days old'
                )
                api.destroy_friendship(user_id)


def analyse_tweets(tweet_df):
    tweet_df["subjectivity"] = np.nan
    tweet_df["polarity"] = np.nan
    for row in tweet_df.itertuples():
        sentiment_tuple = text_sentiment(row.text)
        tweet_df.loc[row.Index, "polarity"] = sentiment_tuple.polarity
        tweet_df.loc[row.Index, "subjectivity"] = sentiment_tuple.subjectivity
    return tweet_df


def get_tweets_with_sentiments(no_of_days, api):
    oldest_date = datetime.datetime.now() - datetime.timedelta(days=no_of_days)
    user_ids, _ = get_followings(api)
    list_of_df = []
    for user_id in user_ids:
        tweets = get_recent_tweets(api, user_id, oldest_date)
        tweet_df = format_tweets(tweets)
        list_of_df.append(tweet_df)
    tweet_df = pd.concat(list_of_df, ignore_index=True)
    tweet_df = analyse_tweets(tweet_df)
    return tweet_df


if __name__ == "__main__":
    # Clean friends list
    # tweet_age_days = 365
    # unfollow_users_with_old_posts(tweet_age_days)

    # Get tweets during recent week
    # TODO add visualisation library that can plot distributions and checks
    # Maybe create notebook with plots
    no_of_days = 7
    api = connect_to_api()
    user_ids, users = get_followings(api)
    oldest_date = datetime.datetime.now() - datetime.timedelta(days=no_of_days)
    count = 0
    while count < 3:
        for user in users:
            logger.info(
                f"Getting tweets for {user.name} (screen name {user.screen_name})"
            )
            tweets = get_recent_tweets(
                api, user.id, oldest_date, return_tweets=1, num_tweets=15
            )
            if tweets:
                count += 1
                print([tweet.text for tweet in tweets])
